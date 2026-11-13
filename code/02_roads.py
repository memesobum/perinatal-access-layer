#!/usr/bin/env python3
"""02_roads.py: turn OpenStreetMap road data into a drivable road network.

Plain-language summary: this script keeps only roads that cars can use, works out
how long it takes to drive each stretch of road (from road type and posted speed
limit), and saves the result as a list of road links with travel times. The lower
48 states and DC come from OpenStreetMap regional files. Alaska and Hawaii are not
in those files, so their roads come from the Overture Maps transportation layer,
which is built from the same OpenStreetMap roads. You do not need to open this file.

Output (data/work/, not committed):
  roads_<region>_edges.parquet     one row per road link: from point, to point, minutes each way
  roads_<region>_vertices.parquet  one row per road point: id, latitude, longitude, snappable
"""

import argparse
import os
import re
import subprocess
import sys
import time
from array import array

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import (ACCESS_DROP, DENSIFY_M, FERRY_KMH, INCLUDE_FERRIES, MAXSPEED_CAP_FACTOR,  # noqa: E402
                    MAXSPEED_FACTOR, OSM_DIR, OSM_REGIONS, SPEED_KMH, WORK)

R_EARTH = 6371008.8
NO_SNAP = {"motorway", "motorway_link", "trunk_link", "ferry"}
CLASSES = list(SPEED_KMH) + ["ferry"]

# Overture release used for Alaska and Hawaii (OSM-derived roads), and the areas queried.
OVERTURE_RELEASE = "2026-10-21.0"
OVERTURE_AREAS = {
    "alaska": [(-179.99, 51.0, -129.9, 71.6)],
    "hawaii": [(-160.6, 18.8, -154.7, 22.4)],
}


def parse_maxspeed(v):
    if not v:
        return None
    v = v.strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(mph|km/h|kmh|kph)?$", v)
    if not m:
        return None
    x = float(m.group(1))
    if m.group(2) == "mph":
        x *= 1.609344
    elif m.group(2) is None and x <= 85:
        # In the U.S. an untagged unit is almost always mph (e.g. "55").
        x *= 1.609344
    return x if 5 <= x <= 200 else None


def parse_duration(v):
    """OSM duration tag (HH:MM, HH:MM:SS, or minutes) -> seconds."""
    if not v:
        return None
    p = v.strip().split(":")
    try:
        if len(p) == 3:
            return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
        if len(p) == 2:
            return int(p[0]) * 3600 + int(p[1]) * 60
        return float(p[0]) * 60
    except ValueError:
        return None


def way_speeds(tags):
    """Return (class, km/h forward, km/h backward, ferry duration seconds or None); None to drop."""
    hw = tags.get("highway")
    ferry = tags.get("route") == "ferry"
    if ferry:
        if not INCLUDE_FERRIES:
            return None
        if tags.get("motor_vehicle") == "no" or tags.get("motorcar") == "no":
            return None
        # as in the OSRM car profile, ferries count unless tagged as closed to cars
        return ("ferry", FERRY_KMH, FERRY_KMH, parse_duration(tags.get("duration")))
    if hw not in SPEED_KMH:
        return None
    for k in ("access", "motor_vehicle", "motorcar", "vehicle"):
        if tags.get(k) in ACCESS_DROP:
            return None
    base = SPEED_KMH[hw]
    ms = parse_maxspeed(tags.get("maxspeed"))
    sp = min(ms * MAXSPEED_FACTOR, base * MAXSPEED_CAP_FACTOR) if ms else base
    ow = tags.get("oneway")
    if tags.get("junction") in ("roundabout", "circular") or hw in ("motorway",):
        ow = ow or "yes"
    if ow in ("yes", "true", "1"):
        return (hw, sp, 0.0, None)
    if ow == "-1":
        return (hw, 0.0, sp, None)
    return (hw, sp, sp, None)


def filter_region(reg):
    src = os.path.join(OSM_DIR, f"{reg}.osm.pbf")
    flt = os.path.join(WORK, f"{reg}-roads.osm.pbf")
    loc = os.path.join(WORK, f"{reg}-roads-loc.osm.pbf")
    if not os.path.exists(loc):
        classes = ",".join(SPEED_KMH)
        subprocess.run(["osmium", "tags-filter", "-O", "-o", flt, src, f"w/highway={classes}", "w/route=ferry"],
                       check=True)
        subprocess.run(["osmium", "add-locations-to-ways", "--ignore-missing-nodes", "-O", "-o", loc, flt], check=True)
        os.remove(flt)
    return loc


def read_osm(loc):
    """Read car-usable ways. Coordinates are kept as OSM's native integers (degrees x 1e7) to save memory."""
    import osmium
    ids, ix, iy = array("q"), array("i"), array("i")
    wlen, cls, sf, sb, fdur = array("i"), [], array("f"), array("f"), array("f")
    bad = 2147483647
    for w in osmium.FileProcessor(loc, osmium.osm.WAY):
        r = way_speeds(dict(w.tags))
        if r is None or len(w.nodes) < 2:
            continue
        nodes = w.nodes
        xs = [nd.x for nd in nodes]
        if bad in xs:
            continue
        ids.extend([nd.ref for nd in nodes])
        ix.extend(xs)
        iy.extend([nd.y for nd in nodes])
        wlen.append(len(nodes))
        cls.append(r[0])
        sf.append(r[1])
        sb.append(r[2])
        fdur.append(r[3] if r[3] else np.nan)
    return (np.frombuffer(ids, dtype=np.int64), np.frombuffer(iy, dtype=np.int32),
            np.frombuffer(ix, dtype=np.int32), np.frombuffer(wlen, dtype=np.int32), np.array(cls),
            np.frombuffer(sf, dtype=np.float32), np.frombuffer(sb, dtype=np.float32),
            np.frombuffer(fdur, dtype=np.float32))


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


def shared_points(ids):
    """Boolean mask: point id used more than once (a junction between roads)."""
    srt = np.sort(ids)
    dup = np.unique(srt[1:][srt[1:] == srt[:-1]])
    del srt
    out = np.zeros(len(ids), bool)
    step = 10_000_000
    for i in range(0, len(ids), step):          # chunked lookup keeps memory low on large regions
        x = ids[i:i + step]
        k = np.clip(np.searchsorted(dup, x), 0, len(dup) - 1)
        out[i:i + step] = dup[k] == x
    return out


def build_edges(ids, iy, ix, wlen, cls, sf, sb, fdur, chunk_ways=400_000):
    """Split ways at shared points, way ends, and every DENSIFY_M meters; return edges and vertices.
    iy/ix are latitude/longitude in degrees x 1e7. Works through the ways in chunks to limit memory."""
    shared = shared_points(ids)
    start_all = np.concatenate([[0], np.cumsum(wlen.astype(np.int64))[:-1]])
    E, V = [], []
    for w0 in range(0, len(wlen), chunk_ways):
        w1 = min(w0 + chunk_ways, len(wlen))
        p0 = start_all[w0]
        p1 = start_all[w1] if w1 < len(wlen) else len(ids)
        wl = wlen[w0:w1].astype(np.int64)
        start = start_all[w0:w1] - p0
        end = start + wl - 1
        wid = np.repeat(np.arange(w0, w1), wl)
        lat = iy[p0:p1] / 1e7
        lon = ix[p0:p1] / 1e7
        cid = ids[p0:p1]
        seg = np.zeros(len(cid))
        seg[1:] = haversine(lat[:-1], lon[:-1], lat[1:], lon[1:])
        seg[start] = 0.0
        cum = np.cumsum(seg)
        cum -= np.repeat(cum[start], wl)
        wtot = np.repeat(cum[end], wl)
        isv = shared[p0:p1].copy()
        isv[start] = True
        isv[end] = True
        blk = np.floor(cum / DENSIFY_M)
        brk = np.zeros(len(cid), bool)
        brk[1:] = blk[1:] > blk[:-1]
        brk[start] = False
        isv |= brk
        P = np.flatnonzero(isv)
        same = wid[P[:-1]] == wid[P[1:]]
        a, b = P[:-1][same], P[1:][same]
        w = wid[a]
        L = cum[b] - cum[a]
        spf, spb = sf[w].astype(float), sb[w].astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            tf = np.where(spf > 0, L / (spf / 3.6) / 60.0, np.inf)
            tb = np.where(spb > 0, L / (spb / 3.6) / 60.0, np.inf)
            fd = fdur[w].astype(float)
            wt = wtot[a]
            has = ~np.isnan(fd) & (wt > 0)
            tdur = fd / 60.0 * L / np.where(wt > 0, wt, 1)
        tf = np.where(has, tdur, tf)
        tb = np.where(has, tdur, tb)
        E.append(pd.DataFrame({"u": cid[a], "v": cid[b], "tf": tf.astype(np.float32), "tb": tb.astype(np.float32),
                               "len_m": L.astype(np.float32),
                               "cls": pd.Categorical(cls[w], categories=CLASSES)}))
        snap = ~np.isin(cls[wid[P]], list(NO_SNAP))
        V.append(pd.DataFrame({"id": cid[P], "lat": lat[P], "lon": lon[P], "snap": snap}))
        del lat, lon, seg, cum, wtot, isv, blk, brk, wid
    del shared
    edges = pd.concat(E, ignore_index=True)
    del E
    vt = pd.concat(V, ignore_index=True)
    del V
    # one row per point; a point is snappable if any road through it is
    vt = vt.sort_values(["id", "snap"], ascending=[True, False]).drop_duplicates("id").reset_index(drop=True)
    return edges, vt


def read_overture(area):
    """Alaska/Hawaii roads from Overture Maps (OSM-derived). Returns the same arrays as read_osm."""
    import duckdb
    c = duckdb.connect()
    c.sql("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
    cls_keep = "','".join(SPEED_KMH)
    boxes = " OR ".join(f"(bbox.xmin>{x0} AND bbox.xmax<{x1} AND bbox.ymin>{y0} AND bbox.ymax<{y1})"
                        for x0, y0, x1, y1 in OVERTURE_AREAS[area])
    q = f"""
      SELECT id, class, subtype, ST_AsWKB(geometry) AS wkb, connectors,
             to_json(speed_limits) AS sl, to_json(access_restrictions) AS ar, to_json(road_flags) AS rf
      FROM read_parquet('s3://overturemaps-us-west-2/release/{OVERTURE_RELEASE}/theme=transportation/type=segment/*',
                        hive_partitioning=1)
      WHERE ({boxes}) AND ((subtype='road' AND class IN ('{cls_keep}')) OR subtype='water')
    """
    df = c.sql(q).df()
    return df


def overture_to_arrays(df, base):
    """Convert Overture segments to point arrays. Each connector is a graph point (synthetic id);
    shape points between connectors get unique synthetic ids so they never join other roads."""
    import json

    import shapely
    geoms = shapely.from_wkb([bytes(x) for x in df.wkb.values])
    conn_ids = {}
    next_id = [base]   # synthetic ids; each area gets its own range so areas never share points

    def cid(s):
        if s not in conn_ids:
            conn_ids[s] = next_id[0]
            next_id[0] += 1
        return conn_ids[s]

    ids, lat, lon = [], [], []
    wlen, cls, sf, sb, fdur = [], [], [], [], []
    for r, g in zip(df.itertuples(index=False), geoms):
        if g is None or g.geom_type != "LineString":
            continue
        tags = {}
        if r.subtype == "water":
            tags = {"route": "ferry", "motor_vehicle": "yes"}
            # Overture marks car ferries only through access rules; keep ferries that do not deny motor vehicles
            if isinstance(r.ar, str) and '"motor_vehicle"' in r.ar and '"denied"' in r.ar:
                continue
        else:
            tags["highway"] = r[1]  # namedtuple field for "class"
            ar = json.loads(r.ar) if isinstance(r.ar, str) else None
            if ar:
                # Closed to cars only if a rule denies access outright and no rule allows any access
                # (private roads appear as "denied" plus "allowed for private use"; those are kept, as in OSM).
                denied = any(r_.get("access_type") == "denied" and not r_.get("when") for r_ in ar)
                allowed = any(r_.get("access_type") in ("allowed", "designated") for r_ in ar)
                if denied and not allowed:
                    tags["access"] = "no"
            sl = json.loads(r.sl) if isinstance(r.sl, str) else None
            if sl:
                for rule in sl:
                    mx = rule.get("max_speed")
                    if mx and not rule.get("between"):
                        tags["maxspeed"] = f"{mx.get('value')} {mx.get('unit', 'mph').lower()}"
                        break
        res = way_speeds(tags)
        if res is None:
            continue
        coords = np.asarray(g.coords)
        n = len(coords)
        if n < 2:
            continue
        # place connectors at nearest shape point by fraction along the line
        cum = np.concatenate([[0], np.cumsum(haversine(coords[:-1, 1], coords[:-1, 0], coords[1:, 1], coords[1:, 0]))])
        tot = cum[-1] if cum[-1] > 0 else 1.0
        pid = np.array([next_id[0] + i for i in range(n)], dtype=np.int64)
        next_id[0] += n
        cons = r.connectors if r.connectors is not None else []
        for cn in cons:
            k = int(np.argmin(np.abs(cum / tot - float(cn["at"]))))
            pid[k] = cid(cn["connector_id"])
        ids.extend(pid.tolist())
        lat.extend(coords[:, 1].tolist())
        lon.extend(coords[:, 0].tolist())
        wlen.append(n)
        cls.append(res[0])
        sf.append(res[1])
        sb.append(res[2])
        fdur.append(np.nan if res[3] is None else res[3])
    return (np.array(ids, np.int64), np.round(np.array(lat) * 1e7).astype(np.int32),
            np.round(np.array(lon) * 1e7).astype(np.int32), np.array(wlen, np.int32), np.array(cls),
            np.array(sf, np.float32), np.array(sb, np.float32), np.array(fdur, np.float32))


def save(name, edges, vt, stats):
    edges.to_parquet(os.path.join(WORK, f"roads_{name}_edges.parquet"), index=False)
    vt.to_parquet(os.path.join(WORK, f"roads_{name}_vertices.parquet"), index=False)
    stats.update({"edges": len(edges), "vertices": len(vt), "km_road": float(edges.len_m.sum() / 1000)})
    pd.Series(stats).to_json(os.path.join(WORK, f"roads_{name}_stats.json"))
    print(f"  {name}: {stats}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="regions to (re)build, e.g. us-west alaska")
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    todo = a.only or (OSM_REGIONS + list(OVERTURE_AREAS))
    for reg in todo:
        t0 = time.time()
        if os.path.exists(os.path.join(WORK, f"roads_{reg}_edges.parquet")) and not a.only:
            print(f"  have {reg}")
            continue
        if reg in OVERTURE_AREAS:
            cache = os.path.join(WORK, f"overture_{reg}_segments.parquet")
            if os.path.exists(cache):
                df = pd.read_parquet(cache)
            else:
                df = read_overture(reg)
                df.to_parquet(cache, index=False)
            arrs = overture_to_arrays(df, (1 << 60) + list(OVERTURE_AREAS).index(reg) * (1 << 40))
            src = f"Overture Maps transportation release {OVERTURE_RELEASE} (OSM-derived, ODbL)"
        else:
            loc = filter_region(reg)
            arrs = read_osm(loc)
            src = f"OpenStreetMap {reg} extract"
        edges, vt = build_edges(*arrs)
        save(reg, edges, vt, {"source": src, "ways": int(len(arrs[3])), "points": int(len(arrs[0])),
                              "seconds": round(time.time() - t0)})


if __name__ == "__main__":
    main()
