"""config.py: every measurement decision in one place.

Plain-language summary: this file holds the choices that shape the drive-time
measures, such as which sites count as obstetric care, how fast cars are assumed
to travel on each kind of road, and the 30- and 60-minute thresholds. Each choice
is marked DECISION and listed in docs/VERIFY_CHECKLIST.md Part 4, where
Mr. Emesobum rules on it. Changing a value here and re-running `bash run_all.sh`
rebuilds everything.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OSM_DIR = os.path.join(RAW, "osm")          # large OpenStreetMap files; not committed
WORK = os.path.join(ROOT, "data", "work")   # intermediate graph files; not committed
PROC = os.path.join(ROOT, "data", "processed")
REPORT = os.path.join(ROOT, "report")

VERSION = "0.1.0"
# Draft stamping: on until the author verifies this version. Set PANEL_FINAL=1 after verification.
DRAFT = os.environ.get("PANEL_FINAL") != "1"

# County universe: same as Project 1 (Census Vintage 2024 geography, 50 states + DC, 3,144 counties).
EXCLUDE_STATE_FIPS = {"72"}

# Project 1 release used as the source of facility sites and county rural codes.
P1_DOI = "10.5281/zenodo.24025395"
P1_ZENODO_RECORD = "24025395"

# ---------------------------------------------------------------------------
# DECISION 1: road network and speeds.
# OpenStreetMap regional extracts (openstreetmap.fr mirror of the OSM planet).
OSM_REGIONS = ["us-west", "us-south", "us-midwest", "us-northeast"]
OSM_URL = "https://download.openstreetmap.fr/extracts/north-america/{region}-latest.osm.pbf"

# Road classes kept. Service roads (driveways, parking aisles) and tracks are left out;
# sites and neighborhoods connect to the nearest kept road (DECISION 3).
# Free-flow car speeds in km/h, the defaults of the OSRM car profile (car.lua, v5.27).
SPEED_KMH = {
    "motorway": 90, "motorway_link": 45,
    "trunk": 85, "trunk_link": 40,
    "primary": 65, "primary_link": 30,
    "secondary": 55, "secondary_link": 25,
    "tertiary": 40, "tertiary_link": 20,
    "unclassified": 25, "residential": 25, "living_street": 10,
}
# Where a road carries a posted speed limit (maxspeed tag), use limit x this factor instead,
# capped at the class default x MAXSPEED_CAP_FACTOR. 0.8 follows the OSRM car profile.
MAXSPEED_FACTOR = 0.8
MAXSPEED_CAP_FACTOR = 1.5
# Ferries (unless tagged closed to cars, as in OSRM): tagged duration when present, otherwise this speed (OSRM default).
INCLUDE_FERRIES = True
FERRY_KMH = 5
# Ways closed to cars are dropped. Private roads (gated subdivisions, military bases, campuses) are kept,
# because the people who live behind a gate can drive out through it; leaving them out strands those homes.
ACCESS_DROP = {"no"}

# Extra graph points every this many meters along long roads, so a neighborhood next to a
# long rural highway connects to the highway where it is, not at the next intersection.
DENSIFY_M = 1000

# ---------------------------------------------------------------------------
# DECISION 2: where people are.
# Origins: 2020 Census population-weighted block group centers. Weights: women aged 15 to 44,
# ACS 2020-2024 5-year table B01001 (female 15-17 through 40-44).
ACS_YEAR = 2024
WOMEN_15_44_VARS = [f"B01001_{i:03d}E" for i in range(30, 39)]

# ---------------------------------------------------------------------------
# DECISION 3: getting on and off the road network.
# The straight-line distance from a neighborhood center or a care site to the nearest
# kept road point is driven at this speed, after multiplying by the detour factor.
CONNECTOR_KMH = 25
CONNECTOR_DETOUR = 1.3
# A neighborhood or site farther than this from any road is treated as not connected.
MAX_SNAP_KM = 25

# ---------------------------------------------------------------------------
# DECISION 4: what counts as each type of care site.
# Obstetric (headline): hospitals that report providing inpatient labor and delivery care in the
#   CMS Maternal Health - Hospital file (structural measure SM_7 = Yes or No), or that report
#   perinatal care measures PC_02 / PC_07 with a nonzero sample.
# Obstetric (upper bound): the headline set plus hospitals whose labor and delivery status CMS
#   lists as "Not Available" (mostly critical access hospitals that do not report).
# OB clinician (supplement): ZIP codes with at least one obstetric clinician in Project 1
#   (OB/GYN, midwife, women's health/perinatal NP or CNS), placed at the ZIP's interior point.
# Perinatal BH (headline): FindTreatment.gov listings flagged "Pregnant/postpartum women"
#   (Project 1 column serves_ppw = 1). These are substance use listings.
# Mental health (supplement): FindTreatment.gov listings of facility type MH (any population).
# Health center: Project 1 HRSA health center sites (active, permanent, not school or correctional).
SERVICE_TYPES = {
    "ob_hosp": "Hospital providing labor and delivery care (CMS, confirmed)",
    "ob_hosp_upper": "Hospital providing labor and delivery care (CMS, confirmed or status not reported)",
    "ob_clin": "Obstetric clinician practice ZIP (NPPES, via Project 1)",
    "ppw_bh": "Treatment facility serving pregnant or postpartum women (FindTreatment.gov, via Project 1)",
    "mh_any": "Mental health treatment facility, any population (FindTreatment.gov, via Project 1)",
    "hc": "HRSA health center site (via Project 1)",
}
HEADLINE_TYPES = ["ob_hosp", "ppw_bh", "hc"]

# ---------------------------------------------------------------------------
# DECISION 5: thresholds and reporting.
THRESHOLDS_MIN = [30, 60]
# Dijkstra search stops at this many minutes; longer times are reported as ">= this".
ROUTE_LIMIT_MIN = 600
# Rural and frontier: taken unchanged from Project 1 (RUCC 2023 codes 4-9 = rural;
# fewer than 6 people per square mile = frontier).
SMALL_WOMEN = 500   # counties with fewer women 15-44 than this are flagged as small

STATE_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC",
    "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT",
    "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}
