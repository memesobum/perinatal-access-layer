#!/usr/bin/env python3
"""03_sites.py: build the list of care sites, with a map location for each.

Plain-language summary: this script decides which places count as each type of
care (see config.py DECISION 4) and gives each one a latitude and longitude.
Hospitals are placed with the Census Bureau's free address geocoder; Project 1
facilities and health centers already have coordinates; obstetric clinicians are
placed at the center of their ZIP code. Output: data/processed/sites.csv, one row
per site per service type.
"""

import io
import os
import re
import sys
import time
import zipfile

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(__file__))
from config import PROC, RAW, ROOT, STATE_ABBR  # noqa: E402

IN_SCOPE = set(STATE_ABBR.values())
GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
GEOCODE_CACHE = os.path.join(RAW, "census_geocoder_hospitals.csv")


def zcta_points():
    with zipfile.ZipFile(os.path.join(RAW, "2024_Gaz_zcta_national.zip")) as z:
        name = [fn for fn in z.namelist() if fn.endswith(".txt")][0]
        g = pd.read_csv(z.open(name), sep="\t", dtype=str)
    g.columns = [c.strip() for c in g.columns]
    return pd.DataFrame({"zip": g.GEOID.str.strip(), "zlat": pd.to_numeric(g.INTPTLAT),
                         "zlon": pd.to_numeric(g.INTPTLONG.str.strip())}).set_index("zip")


def place_points():
    """Town (Census place) interior points keyed by (STATE, NORMALIZED NAME)."""
    with zipfile.ZipFile(os.path.join(RAW, "2024_Gaz_place_national.zip")) as z:
        name = [fn for fn in z.namelist() if fn.endswith(".txt")][0]
        g = pd.read_csv(z.open(name), sep="\t", dtype=str, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    nm = g.NAME.str.replace(r" (city|town|village|CDP|borough|municipality|city and borough)$", "", regex=True)
    g["key"] = g.USPS + "|" + norm(nm)
    g = g.drop_duplicates("key")
    return pd.DataFrame({"plat": pd.to_numeric(g.INTPTLAT), "plon": pd.to_numeric(g.INTPTLONG.str.strip())}).set_index(g.key)


def obstetric_hospitals():
    m = pd.read_csv(os.path.join(RAW, "Maternal_Health-Hospital.csv"), dtype=str)
    m["n"] = pd.to_numeric(m.Sample, errors="coerce")
    m["sc"] = pd.to_numeric(m.Score, errors="coerce")
    pc = m[m["Measure ID"].str.startswith("PC")]
    pc_ok = pc.groupby("Facility ID").apply(lambda g: bool((g.n.fillna(0) > 0).any() or g.sc.notna().any()),
                                            include_groups=False)
    sm = m[m["Measure ID"] == "SM_7"].set_index("Facility ID").Score
    d = pd.DataFrame({"sm7": sm}).join(pc_ok.rename("pc_reported"), how="outer")
    d["pc_reported"] = d.pc_reported.fillna(False).astype(bool)
    d["sm7"] = d.sm7.fillna("Not in file")
    d["ld_status"] = np.select(
        [d.sm7.isin(["Yes", "No"]), d.pc_reported, d.sm7.str.startswith("Not Applicable")],
        ["confirmed_sm7", "confirmed_pc_measures", "no_labor_delivery"], "not_reported")
    h = pd.read_csv(os.path.join(RAW, "Hospital_General_Information.csv"), dtype=str).set_index("Facility ID")
    d = d.join(h[["Facility Name", "Address", "City/Town", "State", "ZIP Code", "Hospital Type",
                  "Meets criteria for birthing friendly designation"]], how="left")
    d = d[d.State.isin(IN_SCOPE)]
    d.index.name = "ccn"
    return d.reset_index()


def geocode(df):
    """Census batch geocoder, cached in data/raw so a re-run uses the same coordinates."""
    if os.path.exists(GEOCODE_CACHE):
        return pd.read_csv(GEOCODE_CACHE, dtype={"ccn": str})
    rows = df[["ccn", "Address", "City/Town", "State", "ZIP Code"]].copy()
    out = []
    for i in range(0, len(rows), 1000):
        buf = io.StringIO()
        rows.iloc[i:i + 1000].to_csv(buf, header=False, index=False)
        for attempt in range(4):
            try:
                r = requests.post(GEOCODER, files={"addressFile": ("a.csv", buf.getvalue())},
                                  data={"benchmark": "Public_AR_Current"}, timeout=600)
                r.raise_for_status()
                break
            except Exception:
                time.sleep(10 * (attempt + 1))
        res = pd.read_csv(io.StringIO(r.text), header=None, dtype=str,
                          names=["ccn", "input", "match", "mtype", "matched", "lonlat", "tiger", "side"])
        out.append(res)
    g = pd.concat(out)
    ll = g.lonlat.str.split(",", expand=True)
    g["glon"] = pd.to_numeric(ll[0], errors="coerce")
    g["glat"] = pd.to_numeric(ll[1], errors="coerce")
    g = g[["ccn", "match", "mtype", "matched", "glat", "glon"]]
    g.to_csv(GEOCODE_CACHE, index=False)
    subprocess_log(GEOCODE_CACHE)
    return g


def subprocess_log(path):
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "provenance.py"), path, GEOCODER,
                    "--log", os.path.join(RAW, "PROVENANCE.txt"),
                    "--note", "Census Geocoder batch results (benchmark Public_AR_Current) for CMS hospital addresses"],
                   check=True, stdout=subprocess.DEVNULL)


def norm(s):
    return s.fillna("").str.upper().str.replace(r"[^A-Z0-9]", "", regex=True)


def place_hospitals(d, zp):
    g = geocode(d)
    d = d.merge(g, on="ccn", how="left")
    # Fallback 1: CMS's own geocoded birthing-friendly list, matched on street address + ZIP
    bf = pd.read_csv(os.path.join(RAW, "Birthing_Friendly_Hospitals_Geocoded.csv"), dtype=str)
    bf["key"] = norm(bf.addr) + "|" + bf.zip.str[:5]
    bf = bf.drop_duplicates("key").set_index("key")
    d["key"] = norm(d.Address) + "|" + d["ZIP Code"].str[:5]
    d["bflat"] = pd.to_numeric(d.key.map(bf.lat), errors="coerce")
    d["bflon"] = pd.to_numeric(d.key.map(bf.lon), errors="coerce")
    d["zip"] = d["ZIP Code"].str[:5]
    z = zp.reindex(d.zip)
    # Order of preference: Census exact address match; CMS's own geocode; Census non-exact match; ZIP point.
    exact = d.glat.notna() & (d.mtype == "Exact")
    d["lat"] = np.where(exact, d.glat, np.nan)
    d["lon"] = np.where(exact, d.glon, np.nan)
    d["geo_method"] = np.where(exact, "census_geocoder_exact", None)
    fb = d.lat.isna() & d.bflat.notna()
    d.loc[fb, ["lat", "lon"]] = d.loc[fb, ["bflat", "bflon"]].values
    d.loc[fb, "geo_method"] = "cms_birthing_friendly_geocode"
    fn = d.lat.isna() & d.glat.notna()
    d.loc[fn, ["lat", "lon"]] = d.loc[fn, ["glat", "glon"]].values
    d.loc[fn, "geo_method"] = "census_geocoder_nonexact"
    # Next: the town's interior point (Census place), which is much closer than a large rural ZIP's center
    # (e.g. Nome, Kotzebue, and Dillingham, Alaska, list PO-box-style addresses the geocoder cannot match).
    pp = place_points().reindex(d.State + "|" + norm(d["City/Town"]))
    fp = d.lat.isna() & pp.plat.notna().values
    d.loc[fp, "lat"] = pp.plat.values[fp.values]
    d.loc[fp, "lon"] = pp.plon.values[fp.values]
    d.loc[fp, "geo_method"] = "town_interior_point"
    fz = d.lat.isna()
    d.loc[fz, "lat"] = z.zlat.values[fz.values]
    d.loc[fz, "lon"] = z.zlon.values[fz.values]
    d.loc[fz & d.lat.notna(), "geo_method"] = "zip_interior_point"
    d.loc[d.lat.isna(), "geo_method"] = "unplaced"
    # Cross-check: distance between Census geocode and CMS geocode where both exist
    both = d.glat.notna() & d.bflat.notna()
    dist = haversine_km(d.glat, d.glon, d.bflat, d.bflon)
    d["census_vs_cms_km"] = np.where(both, dist, np.nan)
    return d


def haversine_km(la1, lo1, la2, lo2):
    p1, p2 = np.radians(la1), np.radians(la2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def state_check(s, zp):
    """Catch coordinates that land in a different state from the listed address (for example, a site in
    Arlington, OR geocoded to Arlington, TX). Such points are moved to the ZIP code's interior point when
    that point is in the listed state; otherwise the site is left unplaced. Returns the corrected table."""
    import geopandas as gpd
    st = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_state_500k.zip')}")[["STUSPS", "geometry"]].to_crs(4326)
    s = s.copy()
    has = s.lat.notna() & s.state.notna()
    pts = gpd.GeoDataFrame(s[has][["lat", "lon"]], geometry=gpd.points_from_xy(s[has].lon, s[has].lat), crs=4326)
    j = gpd.sjoin(pts, st, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    miss = j.STUSPS.isna()
    if miss.any():   # points just offshore or on a border line: nearest state within 5 km
        nn = gpd.sjoin_nearest(pts[miss].to_crs(5070), st.to_crs(5070), how="left", max_distance=5000)
        j.loc[miss, "STUSPS"] = nn.STUSPS[~nn.index.duplicated()]
    s["point_state"] = j.STUSPS.reindex(s.index)
    bad = has & (s.point_state != s.state)
    zpt = zp.reindex(s.zip.fillna("").str[:5])
    zlat, zlon = zpt.zlat.values, zpt.zlon.values
    zst = pd.Series(index=s.index, dtype=object)
    if bad.any():
        zz = s[bad].copy()
        zz["zlat"], zz["zlon"] = zlat[bad.values], zlon[bad.values]
        okz = zz.zlat.notna()
        if okz.any():
            zp_ = gpd.GeoDataFrame(zz[okz], geometry=gpd.points_from_xy(zz[okz].zlon, zz[okz].zlat), crs=4326)
            jz = gpd.sjoin(zp_, st, how="left", predicate="within")
            zst.loc[jz.index] = jz.STUSPS[~jz.index.duplicated()]
    fix = bad & (zst == s.state)
    s["state_check"] = np.where(bad, np.where(fix, "moved_to_zip_point_after_state_mismatch",
                                              "unplaced_state_mismatch"), "ok")
    s.loc[fix, "lat"] = zlat[fix.values]
    s.loc[fix, "lon"] = zlon[fix.values]
    s.loc[fix, "geo_method"] = "zip_interior_point_after_state_mismatch"
    drop = bad & ~fix
    s.loc[drop, ["lat", "lon"]] = np.nan
    s.loc[drop, "geo_method"] = "unplaced_state_mismatch"
    return s.drop(columns="point_state")


def main():
    zp = zcta_points()
    rows = []

    # Obstetric hospitals
    d = obstetric_hospitals()
    # Upper bound adds "not reported" hospitals only where inpatient births are possible and open to the
    # public: general acute care and critical access hospitals. Rural Emergency Hospitals have no inpatient
    # beds; children's and Department of Defense hospitals are left out of the added set.
    upper_types = ["Acute Care Hospitals", "Critical Access Hospitals"]
    keep = d[d.ld_status.isin(["confirmed_sm7", "confirmed_pc_measures"])
             | ((d.ld_status == "not_reported") & d["Hospital Type"].isin(upper_types))]
    keep = place_hospitals(keep, zp)
    for _, r in keep.iterrows():
        types = ["ob_hosp_upper"] + (["ob_hosp"] if r.ld_status != "not_reported" else [])
        for t in types:
            rows.append({"service_type": t, "site_id": "CCN" + r.ccn, "name": r["Facility Name"],
                         "address": r.Address, "city": r["City/Town"], "state": r.State, "zip": r.zip,
                         "lat": r.lat, "lon": r.lon, "geo_method": r.geo_method,
                         "detail": f"{r['Hospital Type']}; L&D status: {r.ld_status}; SM_7: {r.sm7}",
                         "census_vs_cms_km": r.census_vs_cms_km})
    d[["ccn", "Facility Name", "State", "Hospital Type", "sm7", "pc_reported", "ld_status"]].to_csv(
        os.path.join(PROC, "cms_hospital_ld_status.csv"), index=False)

    # Obstetric clinician ZIPs (Project 1)
    c = pd.read_csv(os.path.join(RAW, "p1_capacity_clinicians_by_zip.csv"), dtype={"zip5": str, "fips": str})
    c = c[(c.group == "obstetric") & (c.clinicians > 0)].groupby("zip5", as_index=False).clinicians.sum()
    z = zp.reindex(c.zip5)
    c["lat"], c["lon"] = z.zlat.values, z.zlon.values
    for _, r in c.iterrows():
        rows.append({"service_type": "ob_clin", "site_id": "ZIP" + r.zip5, "name": f"ZIP {r.zip5}",
                     "zip": r.zip5, "lat": r.lat, "lon": r.lon,
                     "geo_method": "zip_interior_point" if pd.notna(r.lat) else "unplaced_zip_not_a_zcta",
                     "detail": f"{int(r.clinicians)} obstetric clinicians (NPPES primary practice ZIP)"})

    # FindTreatment.gov listings (Project 1)
    f = pd.read_csv(os.path.join(RAW, "p1_capacity_facilities.csv"), dtype=str)
    f = f[f.state.isin(IN_SCOPE)]
    f["lat"] = pd.to_numeric(f.latitude, errors="coerce")
    f["lon"] = pd.to_numeric(f.longitude, errors="coerce")
    f["gm"] = np.where(f.lat.notna(), "findtreatment_coordinates", None)
    nz = f.lat.isna()
    z = zp.reindex(f.zip.str[:5])
    f.loc[nz, "lat"] = z.zlat.values[nz.values]
    f.loc[nz, "lon"] = z.zlon.values[nz.values]
    f.loc[nz & f.lat.notna(), "gm"] = "zip_interior_point"
    f.loc[f.lat.isna(), "gm"] = "unplaced"
    for t, sel in [("ppw_bh", f.serves_ppw == "1"), ("mh_any", f.facility_type == "MH")]:
        for _, r in f[sel].iterrows():
            rows.append({"service_type": t, "site_id": "FT" + r.facility_id, "name": r["name"], "address": r.street,
                         "city": r.city, "state": r.state, "zip": (r.zip or "")[:5], "lat": r.lat, "lon": r.lon,
                         "geo_method": r.gm, "detail": f"type {r.facility_type}; setting: {r.service_setting}"})

    # HRSA health center sites (Project 1)
    h = pd.read_csv(os.path.join(RAW, "p1_capacity_hc_sites.csv"), dtype=str)
    h = h[h.state.isin(IN_SCOPE)]
    h["lat"] = pd.to_numeric(h.latitude, errors="coerce")
    h["lon"] = pd.to_numeric(h.longitude, errors="coerce")
    h["gm"] = np.where(h.lat.notna(), "hrsa_coordinates", None)
    nz = h.lat.isna()
    z = zp.reindex(h.zip.str[:5])
    h.loc[nz, "lat"] = z.zlat.values[nz.values]
    h.loc[nz, "lon"] = z.zlon.values[nz.values]
    h.loc[nz & h.lat.notna(), "gm"] = "zip_interior_point"
    h.loc[h.lat.isna(), "gm"] = "unplaced"
    for _, r in h.iterrows():
        rows.append({"service_type": "hc", "site_id": r.bphc_site_id, "name": r.site_name, "address": r.address,
                     "city": r.city, "state": r.state, "zip": r.zip, "lat": r.lat, "lon": r.lon, "geo_method": r.gm,
                     "detail": f"{r.health_center_name}; {r.setting}"})

    s = pd.DataFrame(rows)
    s = state_check(s, zp)
    sc = s[s.state_check != "ok"]
    print(f"state check: {len(sc)} site rows moved or unplaced")
    sc[["service_type", "site_id", "name", "city", "state", "zip", "geo_method"]].to_csv(
        os.path.join(PROC, "qa_site_state_mismatches.csv"), index=False)
    s.to_csv(os.path.join(PROC, "sites.csv"), index=False)
    summ = s.groupby(["service_type", "geo_method"]).size().unstack(fill_value=0)
    print(summ)
    summ.to_csv(os.path.join(PROC, "sites_geo_methods.csv"))


if __name__ == "__main__":
    os.makedirs(PROC, exist_ok=True)
    main()
