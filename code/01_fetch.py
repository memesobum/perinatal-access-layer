#!/usr/bin/env python3
"""01_fetch.py: download every raw input, and log where each came from.

Plain-language summary: this script downloads the public files the drive-time
measures are built from and writes one line per file to data/raw/PROVENANCE.txt
(file name, size, fingerprint, web address, date). You do not need to open it.
Re-running skips files already downloaded unless you pass --refresh.

Sources (all free and public; see README for vintages and terms):
  OpenStreetMap US regional extracts (openstreetmap.fr)   the road network (about 13 GB)
  Census 2020 population-weighted block group centers      where people live
  ACS 2020-2024 5-year table B01001 (summary file)          women aged 15 to 44 per block group
  CMS Maternal Health - Hospital                            which hospitals deliver babies
  CMS Hospital General Information                          hospital type and address
  CMS Birthing-Friendly Hospitals with Geocoded Addresses   hospital coordinates
  Project 1 release v0.1.0 (Zenodo)                         treatment listings, health center sites,
                                                            obstetric clinicians by ZIP, county rural codes
  Census 2024 Gazetteer ZCTAs                               ZIP interior points
  Census 2024 cartographic county boundaries                maps
"""

import argparse
import os
import subprocess
import sys
import zipfile

import requests

sys.path.insert(0, os.path.dirname(__file__))
from config import ACS_YEAR, OSM_DIR, OSM_REGIONS, OSM_URL, P1_ZENODO_RECORD, RAW, ROOT  # noqa: E402

PROV = os.path.join(RAW, "PROVENANCE.txt")
TOOLS = os.path.join(ROOT, "tools", "provenance.py")
UA = {}  # CMS refuses some custom User-Agent strings; use the library default

STATIC = {
    "CenPop2020_Mean_BG.txt": (
        "https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/CenPop2020_Mean_BG.txt",
        "Census 2020 centers of population by block group (population-weighted mean centers)"),
    f"acsdt5y{ACS_YEAR}-b01001.dat": (
        f"https://www2.census.gov/programs-surveys/acs/summary_file/{ACS_YEAR}/table-based-SF/data/5YRData/acsdt5y{ACS_YEAR}-b01001.dat",
        f"ACS {ACS_YEAR - 4}-{ACS_YEAR} 5-year table-based summary file, table B01001 (sex by age), all geographies"),
    "2024_Gaz_zcta_national.zip": (
        "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip",
        "Census 2024 Gazetteer, ZCTAs; interior points used to place obstetric clinician ZIPs"),
    "cb_2024_us_county_500k.zip": (
        "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip",
        "Census 2024 cartographic boundary file, counties, 1:500,000; maps only"),
    "cb_2024_us_state_500k.zip": (
        "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip",
        "Census 2024 cartographic boundary file, states, 1:500,000; maps only"),
}

# CMS Provider Data Catalog dataset ids. CMS rotates file URLs on every refresh, so the current
# download URL is looked up from the catalog's metastore API at fetch time.
CMS = {
    "Maternal_Health-Hospital.csv": "nrdb-3fcy",
    "Hospital_General_Information.csv": "xubh-q36u",
    "Birthing_Friendly_Hospitals_Geocoded.csv": "hbf-map",
}
CMS_META = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{id}?show-reference-ids=false"

P1_FILES = ["need_county.csv", "capacity_facilities.csv", "capacity_hc_sites.csv",
            "capacity_clinicians_by_zip.csv"]


def get_json(url, tries=4):
    import time
    for i in range(tries):
        try:
            return requests.get(url, headers=UA, timeout=60).json()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(5 * (i + 1))


def log(path, url, note=""):
    subprocess.run([sys.executable, TOOLS, path, url, "--log", PROV, "--note", note], check=True,
                   stdout=subprocess.DEVNULL)


def get(url, path, note="", refresh=False):
    if os.path.exists(path) and not refresh:
        print(f"  have {os.path.basename(path)}")
        return
    print(f"  fetching {os.path.basename(path)}")
    tmp = path + ".part"
    with requests.get(url, headers=UA, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 22):
                f.write(chunk)
    os.replace(tmp, path)
    log(path, url, note)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--skip-osm", action="store_true", help="skip the 13 GB road download")
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(OSM_DIR, exist_ok=True)

    print("Census and ACS files")
    for fn, (url, note) in STATIC.items():
        get(url, os.path.join(RAW, fn), note, a.refresh)

    print("CMS hospital files")
    for fn, ds in CMS.items():
        meta = get_json(CMS_META.format(id=ds))
        dist = meta["distribution"][0]
        url = (dist.get("data") or dist)["downloadURL"]
        get(url, os.path.join(RAW, fn),
            f"CMS Provider Data Catalog dataset {ds} ({meta.get('title')}, modified {meta.get('modified')}); "
            f"URL discovered via {CMS_META.format(id=ds)}", a.refresh)

    print("Project 1 release (Zenodo)")
    rec = get_json(f"https://zenodo.org/api/records/{P1_ZENODO_RECORD}")
    f0 = rec["files"][0]
    zpath = os.path.join(RAW, "project1_" + os.path.basename(f0["key"]))
    get(f0["links"]["self"], zpath, f"Project 1 v0.1.0, DOI {rec.get('doi')}", a.refresh)
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            base = os.path.basename(name)
            if base in P1_FILES and "/data/processed/" in name:
                out = os.path.join(RAW, "p1_" + base)
                if not os.path.exists(out) or a.refresh:
                    with z.open(name) as src, open(out, "wb") as dst:
                        dst.write(src.read())
                    log(out, f0["links"]["self"], f"extracted {name} from Project 1 release")

    if not a.skip_osm:
        print("OpenStreetMap regional extracts (about 13 GB; 20 to 40 minutes)")
        for reg in OSM_REGIONS:
            url = OSM_URL.format(region=reg)
            get(url, os.path.join(OSM_DIR, f"{reg}.osm.pbf"),
                "OpenStreetMap data (c) OpenStreetMap contributors, ODbL 1.0; regional extract by openstreetmap.fr",
                a.refresh)
    print("done; see data/raw/PROVENANCE.txt")


if __name__ == "__main__":
    main()
