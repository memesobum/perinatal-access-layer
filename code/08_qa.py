#!/usr/bin/env python3
"""08_qa.py: write the quality report.

Plain-language summary: this script checks the build and writes everything it finds to
data/processed/qa_report.txt: how many rows made it through each step, which sites could
not be placed or connected to a road, how far neighborhood centers are from the nearest
road, whether the numbers obey basic logic (for example, adding hospitals can never make
a drive longer), how the sample agrees with the OSRM routing engine, and spot checks on
named counties you can compare against your Nevada maps. Read this file first.
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import PROC, SERVICE_TYPES, WORK  # noqa: E402

SPOT = {  # named spot checks: Nevada (the author's own maps) plus national extremes and easy cases
    "32003": "Clark County, NV (Las Vegas; easy case)",
    "32031": "Washoe County, NV (Reno)",
    "32009": "Esmeralda County, NV (frontier)",
    "32011": "Eureka County, NV (frontier)",
    "32017": "Lincoln County, NV (frontier)",
    "32023": "Nye County, NV (frontier, large)",
    "32033": "White Pine County, NV (frontier, Ely hospital)",
    "48301": "Loving County, TX (smallest population)",
    "30033": "Garfield County, MT (frontier)",
    "02290": "Yukon-Koyukuk Census Area, AK (off-road villages)",
    "15005": "Kalawao County, HI (no road connection)",
    "36061": "New York County, NY (dense metro)",
}


def main():
    L = []
    w = L.append
    o = pd.read_csv(os.path.join(PROC, "bg_drive_times.csv"), dtype={"geoid": str, "fips": str})
    c = pd.read_csv(os.path.join(PROC, "access_county.csv"), dtype={"fips": str})
    s = pd.read_csv(os.path.join(PROC, "sites.csv"), dtype={"zip": str})
    rs = json.load(open(os.path.join(PROC, "route_stats.json")))
    os_ = json.load(open(os.path.join(PROC, "origins_stats.json")))
    v = json.load(open(os.path.join(PROC, "validation_summary.json")))
    snap = pd.read_csv(os.path.join(WORK, "sites_snap.csv")) if os.path.exists(os.path.join(WORK, "sites_snap.csv")) else None

    w("QUALITY REPORT: Rural and Frontier Perinatal Care Access Layer")
    w("=" * 70)
    w("\n1. ROAD NETWORK")
    for f in sorted(os.listdir(WORK)):
        if f.startswith("roads_") and f.endswith("_stats.json"):
            r = json.load(open(os.path.join(WORK, f)))
            w(f"  {f[6:-11]:<14} {r['km_road']:>12,.0f} km  {r['edges']:>11,} links  ({r['source']})")
    w(f"  national graph: {rs['vertices']:,} road points, {rs['arcs']:,} one-way links, "
      f"{rs['components']:,} strongly connected pieces; {rs['share_vertices_in_main']:.2%} of points in "
      f"{rs['main_networks']:,} main networks")

    w("\n2. NEIGHBORHOODS (block groups)")
    w(f"  matched center point + ACS row: {os_['bg_matched']:,}; center only: {os_['bg_center_only']} "
      f"(Suffolk County NY tract recode; ACS women there are all in matched block groups); ACS only: {os_['bg_acs_only']}")
    w(f"  women aged 15-44: {os_['women_total']:,.0f}; block groups with zero women: {os_['bg_zero_women']:,}")
    q = o.snap_km.quantile([.5, .9, .99]).round(2).to_dict()
    w(f"  distance from center to nearest usable road (km): median {q[.5]}, 90th pct {q[.9]}, 99th pct {q[.99]}")
    w(f"  block groups farther than 5 km from a road: {(o.snap_km > 5).sum():,} "
      f"({o.loc[o.snap_km > 5, 'women_15_44'].sum():,.0f} women)")
    w(f"  not connected (more than 25 km): {rs['bg_not_connected']:,} block groups, "
      f"{rs['women_not_connected']:,.0f} women")

    w("\n3. CARE SITES")
    g = pd.read_csv(os.path.join(PROC, "sites_geo_methods.csv")).set_index("service_type")
    w(g.T.to_string())
    w(f"  sites farther than 25 km from a usable road (not routed): {rs['sites_not_routed']}")
    for t in SERVICE_TYPES:
        w(f"  {t:<14} routed sites: {rs.get('sites_routed_' + t, 0):,}")
    hd = s[(s.service_type == "ob_hosp_upper") & (s.census_vs_cms_km > 2)].sort_values("census_vs_cms_km", ascending=False)
    w(f"  hospitals where the Census geocode and CMS's geocode differ by more than 2 km: {len(hd)} "
      "(listed in qa_hospital_geocode_differences.csv; the CMS point was used only for non-exact Census matches)")
    hd[["site_id", "name", "city", "state", "geo_method", "census_vs_cms_km"]].to_csv(
        os.path.join(PROC, "qa_hospital_geocode_differences.csv"), index=False)

    w("\n4. LOGIC CHECKS (each should say 0)")
    a, b = o.min_ob_hosp, o.min_ob_hosp_upper
    w(f"  block groups where adding hospitals made the drive longer (upper > confirmed): "
      f"{int(((b - a) > 0.01).sum())}")
    w(f"  negative drive times: {int(sum((o[f'min_{t}'] < 0).sum() for t in SERVICE_TYPES))}")
    for t in SERVICE_TYPES:
        bad = ((c[f"{t}_share_gt60"] - c[f"{t}_share_gt30"]) > 1e-9).sum()
        w(f"  {t}: counties with more women beyond 60 min than beyond 30 min: {int(bad)}")
    w(f"  women in county table vs block groups: {c.women_15_44.sum():,.0f} vs {o.women_15_44.sum():,.0f}")
    w(f"  counties in table: {len(c):,}; counties with no block group: {int(c.block_groups.isna().sum())}")

    w("\n5. UNREACHABLE BY ROAD (women in block groups with no road route to any delivering hospital)")
    u = o[o.min_ob_hosp.isna()]
    w(f"  {len(u):,} block groups, {u.women_15_44.sum():,.0f} women; by state: "
      f"{u.groupby(u.fips.str[:2]).women_15_44.sum().sort_values(ascending=False).head(8).round(0).to_dict()}")

    w("\n6. CHECK AGAINST OSRM (public open routing engine, same OpenStreetMap roads)")
    al = v["all"]
    w(f"  pairs compared: {al['n']} of {v['pairs_sampled']} sampled; median ratio project/OSRM {al['median_ratio']}; "
      f"median difference {al['median_diff_min']} min; mean absolute difference {al['mean_abs_diff_min']} min; "
      f"within 20% or 5 min: {al['share_within_20pct_or_5min']:.1%}; correlation {al['pearson_r']}")
    w(f"  agree on the 30-minute cutoff: {al['agree_gt30']:.1%}; on the 60-minute cutoff: {al['agree_gt60']:.1%}")
    for k in sorted(v):
        if k.startswith(("type_", "rurality_")):
            x = v[k]
            w(f"    {k:<20} n={x['n']:>3} median ratio {x['median_ratio']}, within 20%/5 min "
              f"{x['share_within_20pct_or_5min']:.1%}, agree 30 {x['agree_gt30']:.1%}, agree 60 {x['agree_gt60']:.1%}")

    w("\n7. NAMED SPOT CHECKS (women 15-44; share beyond 30 / 60 min; median minutes; site nearest to most women)")
    for f, label in SPOT.items():
        r = c[c.fips == f]
        if r.empty:
            w(f"  {f} {label}: not in table")
            continue
        r = r.iloc[0]
        w(f"  {f} {label}: women {r.women_15_44:,.0f}")
        for t in ["ob_hosp", "ppw_bh", "hc"]:
            w(f"      {t:<8} >30: {r[f'{t}_share_gt30']:.0%}  >60: {r[f'{t}_share_gt60']:.0%}  "
              f"median {r[f'{t}_median_min']} min  nearest: {r.get(f'{t}_main_site_name', '')}")

    w("\n8. THRESHOLD COUNTS USED IN DOCUMENTS")
    rt = pd.read_csv(os.path.join(PROC, "access_by_rurality.csv"))
    for _, r in rt.iterrows():
        w(f"  {r.group:<32} counties {r.counties:>5}  women {r.women_15_44:>12,.0f}  " + "  ".join(
            f"{t} >30 {r[f'{t}_share_gt30']:.1%} >60 {r[f'{t}_share_gt60']:.1%}" for t in ["ob_hosp", "ppw_bh", "hc"]))
    txt = "\n".join(L)
    open(os.path.join(PROC, "qa_report.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
