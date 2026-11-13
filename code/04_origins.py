#!/usr/bin/env python3
"""04_origins.py: where women aged 15 to 44 live.

Plain-language summary: for each Census block group (a neighborhood of about 600 to
3,000 people), this script takes the Census Bureau's population-weighted center
point and the number of women aged 15 to 44 from the American Community Survey.
These points are the starting places for every drive. Output:
data/processed/origins_blockgroups.csv (one row per block group).

Connecticut note: the ACS now uses Connecticut's nine planning regions as counties,
while the 2020 center-point file uses the old eight counties. Connecticut block
groups are matched by placing each center point in its planning region.
"""

import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from config import ACS_YEAR, EXCLUDE_STATE_FIPS, PROC, RAW  # noqa: E402


def main():
    c = pd.read_csv(os.path.join(RAW, "CenPop2020_Mean_BG.txt"), dtype=str, encoding="utf-8-sig")
    c["geoid"] = c.STATEFP + c.COUNTYFP + c.TRACTCE + c.BLKGRPCE
    c["lat"] = pd.to_numeric(c.LATITUDE)
    c["lon"] = pd.to_numeric(c.LONGITUDE)
    c["pop2020"] = pd.to_numeric(c.POPULATION)
    c = c[~c.STATEFP.isin(EXCLUDE_STATE_FIPS)]

    # Connecticut: re-key old-county GEOIDs to planning-region GEOIDs by point-in-polygon
    cg = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")
    ctp = cg[cg.STATEFP == "09"][["GEOID", "geometry"]].to_crs(4326)
    ct = c[c.STATEFP == "09"]
    pts = gpd.GeoDataFrame(ct, geometry=gpd.points_from_xy(ct.lon, ct.lat), crs=4326)
    j = gpd.sjoin(pts, ctp, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    miss = j.GEOID.isna()
    if miss.any():
        nn = gpd.sjoin_nearest(pts[miss].to_crs(5070), ctp.to_crs(5070), how="left")
        j.loc[miss, "GEOID"] = nn.GEOID[~nn.index.duplicated()]
    c.loc[ct.index, "geoid"] = j.GEOID + ct.TRACTCE + ct.BLKGRPCE

    cols = ["GEO_ID"] + [f"B01001_E{i:03d}" for i in range(30, 39)] + [f"B01001_M{i:03d}" for i in range(30, 39)]
    a = pd.read_csv(os.path.join(RAW, f"acsdt5y{ACS_YEAR}-b01001.dat"), sep="|", dtype=str, usecols=cols)
    a = a[a.GEO_ID.str.startswith("1500000US")]
    a["geoid"] = a.GEO_ID.str[9:]
    est = a[[f"B01001_E{i:03d}" for i in range(30, 39)]].apply(pd.to_numeric, errors="coerce")
    moe = a[[f"B01001_M{i:03d}" for i in range(30, 39)]].apply(pd.to_numeric, errors="coerce").clip(lower=0)
    a["women_15_44"] = est.sum(axis=1)
    a["women_15_44_moe"] = np.sqrt((moe ** 2).sum(axis=1)).round(0)   # Census approximation for summed MOEs
    a = a[~a.geoid.str[:2].isin(EXCLUDE_STATE_FIPS)]

    o = c[["geoid", "lat", "lon", "pop2020"]].merge(a[["geoid", "women_15_44", "women_15_44_moe"]],
                                                    on="geoid", how="outer", indicator=True)
    o["fips"] = o.geoid.str[:5]
    report = o._merge.value_counts().to_dict()
    lost_acs = o[(o._merge == "right_only")].women_15_44.sum()
    lost_cen = o[(o._merge == "left_only")].pop2020.sum()
    print(f"match: {report}; women in ACS block groups without a center point: {lost_acs:.0f}; "
          f"2020 population in center points without ACS row: {lost_cen:.0f}")
    o = o[o._merge == "both"].drop(columns="_merge")
    o.to_csv(os.path.join(PROC, "origins_blockgroups.csv"), index=False)
    pd.Series({"bg_matched": int(len(o)), "bg_center_only": int(report.get("left_only", 0)),
               "bg_acs_only": int(report.get("right_only", 0)), "women_acs_only": float(lost_acs),
               "women_total": float(o.women_15_44.sum()), "bg_zero_women": int((o.women_15_44 == 0).sum())}
              ).to_json(os.path.join(PROC, "origins_stats.json"))
    print(f"{len(o)} block groups, {o.women_15_44.sum():,.0f} women aged 15 to 44")


if __name__ == "__main__":
    main()
