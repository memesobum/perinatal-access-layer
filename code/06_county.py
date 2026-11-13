#!/usr/bin/env python3
"""06_county.py: summarize drive times for each county.

Plain-language summary: for every county, this script adds up how many women aged
15 to 44 live more than 30 minutes and more than 60 minutes from each type of care,
and turns those counts into shares. It also gives the typical (median) and average
drive, and flags counties where some women cannot reach a site by road at all.
Rural and frontier labels come unchanged from Project 1. Output:
  data/processed/access_county.csv      one row per county (the main deliverable)
  data/processed/access_by_rurality.csv national, metro, rural, frontier totals
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import PROC, RAW, SERVICE_TYPES, SMALL_WOMEN, THRESHOLDS_MIN  # noqa: E402


def wquantile(x, w, q):
    """Weighted quantile; unreachable (NaN) counts as longest."""
    x = np.where(np.isnan(x), np.inf, x)
    if w.sum() <= 0:
        return np.nan
    o = np.argsort(x)
    cw = np.cumsum(w[o]) / w.sum()
    k = np.searchsorted(cw, q)
    v = x[o][k]
    return v if np.isfinite(v) else np.inf


def county_rows(o):
    out = []
    for fips, d in o.groupby("fips", sort=True):
        w = d.women_15_44.values.astype(float)
        W = w.sum()
        r = {"fips": fips, "women_15_44": W, "block_groups": len(d),
             "block_groups_no_women": int((w == 0).sum())}
        for t in SERVICE_TYPES:
            m = d[f"min_{t}"].values.astype(float)
            unreach = np.isnan(m)
            r[f"{t}_women_unreachable"] = float(w[unreach].sum())
            for th in THRESHOLDS_MIN:
                beyond = w[unreach | (m > th)].sum()
                r[f"{t}_women_gt{th}"] = float(beyond)
                r[f"{t}_share_gt{th}"] = round(beyond / W, 4) if W > 0 else np.nan
            med = wquantile(m, w, 0.5)
            r[f"{t}_median_min"] = round(med, 1) if np.isfinite(med) else np.nan
            ok = ~unreach
            r[f"{t}_mean_min"] = round(np.average(m[ok], weights=w[ok]), 1) if w[ok].sum() > 0 else np.nan
            r[f"{t}_max_min"] = round(np.nanmax(m), 1) if ok.any() else np.nan
            r[f"{t}_median_unreachable"] = int(np.isinf(med)) if W > 0 else 0
        out.append(r)
    return pd.DataFrame(out)


def nearest_site_names(o, sites):
    """The site nearest to most of the county's women, per type (useful for planners checking the result)."""
    nm = sites.drop_duplicates("site_id").set_index("site_id").name
    rows = {}
    for t in ["ob_hosp", "ppw_bh", "hc"]:
        g = o[o[f"site_{t}"].fillna("") != ""].groupby(["fips", f"site_{t}"]).women_15_44.sum().reset_index()
        g = g.sort_values("women_15_44", ascending=False).drop_duplicates("fips")
        rows[f"{t}_main_site_id"] = g.set_index("fips")[f"site_{t}"]
        rows[f"{t}_main_site_name"] = g.set_index("fips")[f"site_{t}"].map(nm)
    return pd.DataFrame(rows)


def rurality_table(c):
    rows = []
    groups = [("All counties", c.index == c.index), ("Metro", c.rurality_class == "metro"),
              ("Rural (nonmetro, not frontier)", (c.rural == 1) & (c.frontier == 0)),
              ("Frontier", c.frontier == 1), ("Rural or frontier", (c.rural == 1) | (c.frontier == 1))]
    for name, sel in groups:
        d = c[sel]
        r = {"group": name, "counties": int(len(d)), "women_15_44": float(d.women_15_44.sum())}
        for t in SERVICE_TYPES:
            for th in THRESHOLDS_MIN:
                r[f"{t}_share_gt{th}"] = round(d[f"{t}_women_gt{th}"].sum() / d.women_15_44.sum(), 4)
                r[f"{t}_counties_majority_gt{th}"] = int((d[f"{t}_share_gt{th}"] > 0.5).sum())
            r[f"{t}_women_unreachable"] = float(d[f"{t}_women_unreachable"].sum())
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    o = pd.read_csv(os.path.join(PROC, "bg_drive_times.csv"), dtype={"geoid": str, "fips": str})
    sites = pd.read_csv(os.path.join(PROC, "sites.csv"), dtype=str)
    need = pd.read_csv(os.path.join(RAW, "p1_need_county.csv"), dtype={"fips": str, "state_fips": str})
    keep = ["fips", "state", "county_name", "rucc_2023", "pop_density_2024", "rural", "frontier", "rurality_class",
            "births"]
    c = county_rows(o)
    c = need[keep].merge(c, on="fips", how="left", indicator=True)
    miss = c._merge == "left_only"
    print(f"Project 1 counties: {len(need)}; with block groups: {(~miss).sum()}; without: {miss.sum()} "
          f"{c.loc[miss, 'fips'].tolist()}")
    c = c.drop(columns="_merge")
    c = c.join(nearest_site_names(o, sites), on="fips")
    c["flag_small_women"] = (c.women_15_44 < SMALL_WOMEN).astype(int)
    c["flag_some_unreachable"] = (c.ob_hosp_women_unreachable > 0).astype(int)
    extra = set(o.fips) - set(need.fips)
    if extra:
        print(f"block-group counties not in Project 1: {sorted(extra)}")
    c.to_csv(os.path.join(PROC, "access_county.csv"), index=False)
    rt = rurality_table(c.set_index("fips"))
    rt.to_csv(os.path.join(PROC, "access_by_rurality.csv"), index=False)
    with open(os.path.join(PROC, "county_build_stats.json"), "w") as f:
        json.dump({"counties": int(len(c)), "counties_without_block_groups": int(miss.sum()),
                   "counties_not_in_p1": sorted(extra)}, f, indent=1)
    pd.set_option("display.width", 220)
    print(rt[["group", "counties", "women_15_44"] + [f"{t}_share_gt{th}" for t in ["ob_hosp", "ppw_bh", "hc"]
                                                       for th in THRESHOLDS_MIN]].to_string())


if __name__ == "__main__":
    main()
