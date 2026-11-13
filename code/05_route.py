#!/usr/bin/env python3
"""05_route.py: compute the drive time from every neighborhood to the nearest site of each care type.

Plain-language summary: this script joins the regional road files into one national
road network, connects each neighborhood center and each care site to the nearest
road, and then finds, for every neighborhood, the quickest drive to the nearest site
of each type. It uses Dijkstra's shortest-path method (the same method inside open
routing engines such as OSRM), run once per care type from all sites at the same
time. Output: data/processed/bg_drive_times.csv, one row per block group.

Technical notes
  * Graph: directed; one-way streets respected. Arc weights are free-flow minutes.
  * The search runs on the reversed graph from the sites, so each distance is the
    time to drive FROM a neighborhood TO the site.
  * Each site enters through its own entry node whose arc to the road carries the
    site's connector time; scipy's min_only search then reports which site is nearest.
  * Neighborhoods and sites connect only to road points that are not on freeways and
    belong to a main road network: a strongly connected piece (every point can reach every other) of
    MIN_ALWAYS or more points, or a smaller piece that holds a care site (see SITE_TIERS in main()).
"""

import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(__file__))
from config import (CONNECTOR_DETOUR, CONNECTOR_KMH, MAX_SNAP_KM, PROC, ROUTE_LIMIT_MIN,  # noqa: E402
                    SERVICE_TYPES, WORK)

MIN_ALWAYS = 50000      # a strongly connected piece this big always counts as a main network
SITE_TIERS = [(MIN_ALWAYS, 2.0), (1000, 2.0), (50, MAX_SNAP_KM)]   # (minimum piece size, max km); None = MAX_SNAP_KM
MIN_COMPONENT = 50
ISOLATED_KM = 2.0       # see the separate-road-network rule in main()
ISOLATED_RATIO = 3.0
R_KM = 6371.0088
MIN_ARC = 1e-4   # minutes; keeps zero-length links as real links


def unit(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    x, y, z = np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)
    return np.column_stack((x, y, z))


def load_vertices():
    parts = [pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(WORK, "roads_*_vertices.parquet")))]
    v = pd.concat(parts, ignore_index=True)
    v = v.groupby("id", sort=True).agg(lat=("lat", "first"), lon=("lon", "first"), snap=("snap", "max")).reset_index()
    return v


def build_graph(vid):
    """Reversed directed graph as CSR (arc x->y means: from y you can drive to x)."""
    src, dst, w = [], [], []
    for f in sorted(glob.glob(os.path.join(WORK, "roads_*_edges.parquet"))):
        e = pd.read_parquet(f, columns=["u", "v", "tf", "tb"])
        u = np.searchsorted(vid, e.u.values).astype(np.int32)
        v = np.searchsorted(vid, e.v.values).astype(np.int32)
        tf, tb = e.tf.values, e.tb.values
        ok = np.isfinite(tf)
        src.append(v[ok]); dst.append(u[ok]); w.append(tf[ok])      # forward u->v becomes reversed v->u
        ok = np.isfinite(tb)
        src.append(u[ok]); dst.append(v[ok]); w.append(tb[ok])      # backward v->u becomes reversed u->v
        del e, u, v, tf, tb
    src = np.concatenate(src); dst = np.concatenate(dst); w = np.concatenate(w).astype(np.float64)
    w = np.maximum(w, MIN_ARC)
    keep = src != dst
    src, dst, w = src[keep], dst[keep], w[keep]
    # keep the fastest of duplicate parallel links (regional files overlap at borders)
    order = np.lexsort((w, dst, src))
    src, dst, w = src[order], dst[order], w[order]
    first = np.ones(len(src), bool)
    first[1:] = (src[1:] != src[:-1]) | (dst[1:] != dst[:-1])
    src, dst, w = src[first], dst[first], w[first]
    n = len(vid)
    indptr = np.zeros(n + 1, np.int64)
    np.add.at(indptr, src.astype(np.int64) + 1, 1)
    indptr = np.cumsum(indptr)
    return indptr, dst.astype(np.int32), w


def road_km_deduplicated():
    """Length of mapped road lines with links shared by overlapping regional files counted once.
    Divided highways are mapped as two one-way lines, so they count twice; private roads are included."""
    parts = []
    for f in sorted(glob.glob(os.path.join(WORK, "roads_*_edges.parquet"))):
        e = pd.read_parquet(f, columns=["u", "v", "len_m", "cls"])
        parts.append(pd.DataFrame({"a": np.minimum(e.u.values, e.v.values), "b": np.maximum(e.u.values, e.v.values),
                                   "len": e.len_m.values, "ferry": (e.cls == "ferry").values}))
    d = pd.concat(parts).drop_duplicates(["a", "b"])
    return {"km_road": float(d.loc[~d.ferry, "len"].sum() / 1000), "km_ferry": float(d.loc[d.ferry, "len"].sum() / 1000)}


def snap(tree, cand_idx, lat, lon):
    d, k = tree.query(unit(lat, lon), k=1)
    km = 2 * R_KM * np.arcsin(np.clip(d / 2, 0, 1))
    return cand_idx[k], km


def crosses_water(lat0, lon0, lat1, lon1, mask):
    """True where the straight line between the two points leaves land (Census 2024 shoreline-clipped states)."""
    import geopandas as gpd
    from shapely.geometry import LineString
    from config import RAW
    land = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_state_500k.zip')}").to_crs(5070).union_all()
    land = land.buffer(100)   # 100 m tolerance for bridges and generalized shorelines
    out = np.zeros(len(lat0), bool)
    idx = np.flatnonzero(mask)
    lines = gpd.GeoSeries([LineString([(lon0[i], lat0[i]), (lon1[i], lat1[i])]) for i in idx], crs=4326).to_crs(5070)
    out[idx] = ~lines.within(land).values
    return out


def connector_min(km):
    return km * CONNECTOR_DETOUR / CONNECTOR_KMH * 60.0


def main():
    t0 = time.time()
    km = road_km_deduplicated()   # computed first, before the graph is in memory
    import gc
    gc.collect()
    v = load_vertices()
    vid = v.id.values
    n = len(vid)
    print(f"vertices: {n:,} ({time.time() - t0:.0f}s)")
    indptr, indices, data = build_graph(vid)
    print(f"arcs: {len(indices):,} ({time.time() - t0:.0f}s)")
    G = csr_matrix((data, indices, indptr), shape=(n, n))
    ncomp, comp = connected_components(G, directed=True, connection="strong")
    csize = np.bincount(comp)
    big = csize[comp] >= MIN_COMPONENT
    print(f"components: {ncomp:,}; points in pieces >= {MIN_COMPONENT}: {big.mean():.4f}")

    # Main road networks. Each site is attached in tiers: to a very large network (the mainland pieces) if
    # one is within 2 km; otherwise to a piece of 1,000+ points within 2 km (islands such as Oahu); otherwise
    # to any piece of 50+ points within MAX_SNAP_KM (road-isolated towns such as Bethel or Nome, Alaska).
    # Main networks = the very large pieces plus every piece that received a site. Neighborhoods then attach
    # only to main networks. This keeps them off closed-off pieces such as gated subdivisions whose gate
    # road is private (and so left out), while keeping road-isolated towns that have their own care sites.
    s = pd.read_csv(os.path.join(PROC, "sites.csv"), dtype={"zip": str})
    s = s[s.lat.notna()].reset_index(drop=True)
    snappable = v.snap.values
    site_comp = np.full(len(s), -1)
    todo = np.ones(len(s), bool)
    for min_size, max_km in SITE_TIERS:
        cand_t = np.flatnonzero(snappable & (csize[comp] >= min_size))
        tree = cKDTree(unit(v.lat.values[cand_t], v.lon.values[cand_t]))
        sv_t, km_t = snap(tree, cand_t, s.lat.values[todo], s.lon.values[todo])
        ok = km_t <= max_km
        idx = np.flatnonzero(todo)[ok]
        site_comp[idx] = comp[sv_t[ok]]
        todo[idx] = False
        del tree
    main_comp = csize >= MIN_ALWAYS
    main_comp[site_comp[site_comp >= 0]] = True
    main = main_comp[comp]
    print(f"main networks: {main_comp.sum():,}; points in them: {main.mean():.4f}")
    cand = np.flatnonzero(snappable & main)
    tree = cKDTree(unit(v.lat.values[cand], v.lon.values[cand]))

    o = pd.read_csv(os.path.join(PROC, "origins_blockgroups.csv"), dtype={"geoid": str, "fips": str})
    o["snap_vertex"], o["snap_km"] = snap(tree, cand, o.lat.values, o.lon.values)
    # A neighborhood on an island with no car connection must not be attached across the water to a main
    # network. Rule: the nearest main-network road is more than ISOLATED_KM away, AND either the nearest
    # road of any kind is a closed-off piece (ISOLATED_RATIO times closer) or there is no closer road at
    # all, AND (below) the straight line to the main network crosses open water.
    all_snap = np.flatnonzero(snappable)
    tree_all = cKDTree(unit(v.lat.values[all_snap], v.lon.values[all_snap]))
    nv_any, km_any = snap(tree_all, all_snap, o.lat.values, o.lon.values)
    del tree_all
    isolated = (o.snap_km.values > ISOLATED_KM) & (
        (~main[nv_any] & (o.snap_km.values > ISOLATED_RATIO * km_any))   # nearest road is a closed-off piece
        | (km_any >= o.snap_km.values - 1e-9))                          # or no road at all on its side
    # ...and only when the straight line to the main network crosses open water (coast, bay, lake), judged
    # against the shoreline-clipped Census state boundaries. On land, a closed-off piece usually means the
    # map is missing an unpaved or service road, so the neighborhood keeps its longer connector instead.
    if isolated.any():
        isolated = isolated & crosses_water(o.lat.values, o.lon.values, v.lat.values[o.snap_vertex.values],
                                            v.lon.values[o.snap_vertex.values], isolated)
    o["origin_status"] = np.where(o.snap_km > MAX_SNAP_KM, "no_road_within_25km",
                                  np.where(isolated, "separate_road_network", "connected"))
    o["connected"] = o.origin_status == "connected"
    print(f"origins on separate road networks: {isolated.sum()} block groups, "
          f"{o.loc[isolated, 'women_15_44'].sum():,.0f} women")
    o["origin_conn_min"] = connector_min(o.snap_km)

    s["snap_vertex"], s["snap_km"] = snap(tree, cand, s.lat.values, s.lon.values)
    s["routed"] = s.snap_km <= MAX_SNAP_KM
    s["site_conn_min"] = connector_min(s.snap_km)
    del tree
    s[["service_type", "site_id", "snap_km", "routed"]].to_csv(os.path.join(WORK, "sites_snap.csv"), index=False)

    stats = {"vertices": int(n), "arcs": int(len(indices)), "components": int(ncomp),
             "share_vertices_in_big_components": float(big.mean()),
             "main_networks": int(main_comp.sum()), "share_vertices_in_main": float(main.mean()),
             "bg_not_connected": int((~o.connected).sum()),
             "women_not_connected": float(o.loc[~o.connected, "women_15_44"].sum()),
             "bg_separate_network": int((o.origin_status == "separate_road_network").sum()),
             "women_separate_network": float(o.loc[o.origin_status == "separate_road_network", "women_15_44"].sum()),
             "sites_not_routed": s[~s.routed].groupby("service_type").size().to_dict(),
             "km_road_sum_of_regional_files": float(sum(json.load(open(f))["km_road"]
                                                    for f in glob.glob(os.path.join(WORK, "roads_*_stats.json")))),
             **km}

    for t in SERVICE_TYPES:
        st = s[(s.service_type == t) & s.routed].reset_index(drop=True)
        k = len(st)
        # one entry node per site, appended after the road points: entry -> road point (connector minutes)
        ind2 = np.concatenate([indices, st.snap_vertex.values.astype(np.int32)])
        dat2 = np.concatenate([data, np.maximum(st.site_conn_min.values, MIN_ARC)])
        ptr2 = np.concatenate([indptr, indptr[-1] + np.arange(1, k + 1)])
        G2 = csr_matrix((dat2, ind2, ptr2), shape=(n + k, n + k))
        t1 = time.time()
        dist, _, src = dijkstra(G2, directed=True, indices=np.arange(n, n + k), min_only=True,
                                limit=ROUTE_LIMIT_MIN, return_predecessors=True)
        del G2, ind2, dat2, ptr2
        dv = dist[o.snap_vertex.values]
        sv = src[o.snap_vertex.values]
        tot = dv + o.origin_conn_min.values
        tot = np.where(o.connected.values, tot, np.inf)
        o[f"min_{t}"] = np.round(np.where(np.isfinite(tot), tot, np.nan), 2)
        o[f"site_{t}"] = np.where(np.isfinite(tot) & (sv >= 0), st.site_id.values[np.clip(sv - n, 0, k - 1)], "")
        reach = np.isfinite(tot).mean()
        print(f"  {t}: {k:,} sites; {reach:.4f} of block groups reach one within {ROUTE_LIMIT_MIN} min "
              f"({time.time() - t1:.0f}s)")
        stats[f"sites_routed_{t}"] = int(k)
        del dist, src

    o.drop(columns=["snap_vertex"]).to_csv(os.path.join(PROC, "bg_drive_times.csv"), index=False)
    with open(os.path.join(PROC, "route_stats.json"), "w") as f:
        json.dump(stats, f, indent=1, default=str)
    print(f"done ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
