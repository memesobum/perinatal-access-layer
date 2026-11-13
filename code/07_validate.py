#!/usr/bin/env python3
"""07_validate.py: check a sample of drive times against an independent routing engine.

Plain-language summary: this script picks a random sample of neighborhoods in metro,
rural, and frontier counties, takes the route this project computed to the nearest
delivering hospital, perinatal treatment facility, and health center, and asks the
public OSRM routing service (an open-source routing engine running on the same
OpenStreetMap roads) how long the same trip takes. It then reports how closely the
two agree, including whether they agree on the 30- and 60-minute cutoffs.
The national results are compared with published studies in report/stats.json.

Output: data/processed/validation_osrm_sample.csv and data/processed/validation_summary.json.
Usage policy of the public OSRM demo server: at most one request per second; this
script waits 1.1 seconds between requests and sends about 450 in total.
"""

import json
import os
import sys
import time

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(__file__))
from config import PROC  # noqa: E402

OSRM = "https://router.project-osrm.org/route/v1/driving/{o_lon},{o_lat};{d_lon},{d_lat}?overview=false"
PER_CELL = 50
SEED = 20261113
TYPES = ["ob_hosp", "ppw_bh", "hc"]
CACHE = os.path.join(PROC, "validation_osrm_sample.csv")


def draw_sample():
    o = pd.read_csv(os.path.join(PROC, "bg_drive_times.csv"), dtype={"geoid": str, "fips": str})
    c = pd.read_csv(os.path.join(PROC, "access_county.csv"), dtype={"fips": str})[["fips", "rurality_class"]]
    o = o.merge(c, on="fips", how="left")
    o = o[o.women_15_44 > 0]
    s = pd.read_csv(os.path.join(PROC, "sites.csv"), dtype=str).drop_duplicates(["service_type", "site_id"])
    rng = np.random.default_rng(SEED)
    rows = []
    for t in TYPES:
        st = s[s.service_type == t].set_index("site_id")
        for rc in ["metro", "rural", "frontier"]:
            d = o[(o.rurality_class == rc) & o[f"min_{t}"].notna()]
            pick = d.iloc[rng.choice(len(d), size=min(PER_CELL, len(d)), replace=False)]
            for _, r in pick.iterrows():
                site = st.loc[r[f"site_{t}"]]
                rows.append({"service_type": t, "rurality_class": rc, "geoid": r.geoid, "fips": r.fips,
                             "o_lat": r.lat, "o_lon": r.lon, "site_id": r[f"site_{t}"], "site_name": site["name"],
                             "d_lat": float(site.lat), "d_lon": float(site.lon), "min_project": r[f"min_{t}"],
                             "snap_km": r.snap_km})
    return pd.DataFrame(rows)


def query(df):
    out = []
    sess = requests.Session()
    for i, r in df.iterrows():
        url = OSRM.format(o_lon=r.o_lon, o_lat=r.o_lat, d_lon=r.d_lon, d_lat=r.d_lat)
        dur = dist = np.nan
        code = ""
        for attempt in range(3):
            try:
                j = sess.get(url, timeout=60).json()
                code = j.get("code", "")
                if code == "Ok":
                    dur = j["routes"][0]["duration"] / 60
                    dist = j["routes"][0]["distance"] / 1000
                break
            except Exception as e:  # noqa: BLE001
                code = f"error: {e.__class__.__name__}"
                time.sleep(5)
        out.append((dur, dist, code))
        time.sleep(1.1)
    df = df.copy()
    df["min_osrm"] = [x[0] for x in out]
    df["km_osrm"] = [x[1] for x in out]
    df["osrm_code"] = [x[2] for x in out]
    return df


def summarize(df):
    d = df[df.min_osrm.notna()].copy()
    d["diff"] = d.min_project - d.min_osrm
    d["ratio"] = d.min_project / d.min_osrm.clip(lower=0.5)
    res = {"pairs_sampled": int(len(df)), "pairs_compared": int(len(d)),
           "osrm_server": "router.project-osrm.org (OSRM car profile, OpenStreetMap)",
           "queried_on": time.strftime("%Y-%m-%d")}

    def block(x):
        r = {"n": int(len(x)), "median_project_min": round(x.min_project.median(), 1),
             "median_osrm_min": round(x.min_osrm.median(), 1), "median_diff_min": round(x["diff"].median(), 1),
             "mean_abs_diff_min": round(x["diff"].abs().mean(), 1),
             "median_ratio": round(x.ratio.median(), 3),
             "share_within_20pct_or_5min": round(((x["diff"].abs() <= 5) | ((x.ratio - 1).abs() <= 0.2)).mean(), 3),
             "pearson_r": round(np.corrcoef(x.min_project, x.min_osrm)[0, 1], 3) if len(x) > 2 else None}
        for th in (30, 60):
            r[f"agree_gt{th}"] = round(((x.min_project > th) == (x.min_osrm > th)).mean(), 3)
        return r
    res["all"] = block(d)
    for k, g in d.groupby("service_type"):
        res[f"type_{k}"] = block(g)
    for k, g in d.groupby("rurality_class"):
        res[f"rurality_{k}"] = block(g)
    return res


def main():
    if os.path.exists(CACHE) and "--refresh" not in sys.argv:
        df = pd.read_csv(CACHE, dtype={"geoid": str, "fips": str})
    else:
        df = query(draw_sample())
        df.to_csv(CACHE, index=False)
    res = summarize(df)
    with open(os.path.join(PROC, "validation_summary.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res["all"], indent=1))
    for k in res:
        if k.startswith(("type_", "rurality_")):
            print(k, res[k]["median_ratio"], res[k]["share_within_20pct_or_5min"], res[k]["agree_gt30"],
                  res[k]["agree_gt60"])


if __name__ == "__main__":
    main()
