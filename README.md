# Rural and Frontier Perinatal Care Access Layer

**Status:** v0.1.0, verified by the author 2026-11-13 (review fixes applied the same day; see docs/CHANGELOG.md) | **DOI:** minted by Zenodo for each GitHub release (see the DOI badge and the Zenodo record linked from https://github.com/memesobum/perinatal-access-layer) | **Maintainer:** Munachimso A. Emesobum, ORCID [0009-0002-7506-2153](https://orcid.org/0009-0002-7506-2153) | **License:** data and documents CC BY 4.0, code MIT; road-derived values © OpenStreetMap contributors (ODbL)

**In plain terms:** For every U.S. county, this table shows how many women aged 15 to 44 live more than a 30-minute or 60-minute drive from a hospital that delivers babies, from a substance use treatment program that serves pregnant or postpartum women, and from a community health center. Rural and frontier counties are reported separately. Planners can use it to see which counties are cut off from perinatal care even when a facility exists somewhere in the region.

New here? Read [docs/START_HERE.md](docs/START_HERE.md) first. Unfamiliar terms are in [docs/GLOSSARY.md](docs/GLOSSARY.md). How every drive time was computed: [docs/METHODS_ROUTING.md](docs/METHODS_ROUTING.md).

## Why

Counting facilities inside county lines does not show how far a family must travel. The author's mapping of Nevada's 17 counties found seven counties with no OB/GYN provider and more than half without dedicated perinatal behavioral health services. This release measures the travel nationally. It is the companion to the [U.S. County Perinatal Behavioral Health Need and Capacity Panel](https://doi.org/10.5281/zenodo.24025395) (Project 1), and it shares that panel's county key `fips`.

## What is here

| File | Contents |
|---|---|
| `data/processed/access_county.csv` | **Main table.** One row per county (3,144). For each care type: women beyond 30 and 60 minutes (count and share), median and mean minutes, women unreachable by road, the nearest main site, and rural and frontier flags |
| `data/processed/access_by_rurality.csv` | National, metro, rural, and frontier totals |
| `data/processed/bg_drive_times.csv` | One row per Census block group (239,741): drive minutes and nearest site for each care type |
| `data/processed/sites.csv` | Every care site used, with its location and how the location was found |
| `data/processed/validation_osrm_sample.csv`, `validation_summary.json` | The 450-trip check against the OSRM routing engine |
| `data/processed/qa_report.txt` | Quality report. Read it first |
| `report/figures/`, `report/stats.json` | Maps and charts; every number quoted anywhere |
| `paper/main.pdf` | Draft preprint |

The six care types are:
- `ob_hosp`, a delivering hospital, confirmed by CMS (headline)
- `ob_hosp_upper`, the same plus hospitals whose delivery status CMS does not report (sensitivity)
- `ob_clin`, a ZIP code with an obstetric clinician
- `ppw_bh`, a substance use treatment facility serving pregnant or postpartum women (headline)
- `mh_any`, any mental health facility
- `hc`, a HRSA health center site (headline)

Every column is defined in [docs/CODEBOOK.md](docs/CODEBOOK.md).

```
code/            numbered scripts in run order (config.py holds every measurement decision)
data/raw/        PROVENANCE.txt and the hospital geocodes (raw downloads are re-fetched by code/01_fetch.py)
data/processed/  outputs and the QA report
docs/            START_HERE, GLOSSARY, METHODS_ROUTING, CODEBOOK, LIMITATIONS, VERIFY_CHECKLIST,
                 NEXT_STEPS, PUBLISH_GUIDE, TALK_TRACK, BUILD_SPEC
report/          stats.json, figures/
paper/           preprint source (LaTeX) and PDF
tools/           provenance logger, publish gate, upload scripts
```

## Run it

You need Python 3.11 or newer, the `osmium` command-line tool, 8 GB of memory, and 30 GB of free disk.

```
sudo apt install osmium-tool          # Mac: brew install osmium-tool
pip install -r requirements.txt
bash run_all.sh
```

The road data download takes about 30 to 60 minutes. The build and routing take about 30 minutes on 2 cores. OpenStreetMap and the federal listings change, so a later run will differ slightly. `data/raw/PROVENANCE.txt` records the fingerprint of every file used for this release.

## Sources

| Source | Vintage | Terms | Accessed |
|---|---|---|---|
| [OpenStreetMap](https://www.openstreetmap.org), US regional extracts via [openstreetmap.fr](https://download.openstreetmap.fr/extracts/north-america/) | 2026-11-13 | ODbL 1.0, © OpenStreetMap contributors | 2026-11-13 |
| [Overture Maps transportation](https://docs.overturemaps.org/) (Alaska, Hawaii; OSM-derived) | release 2026-10-21.0 | ODbL 1.0 | 2026-11-13 |
| [Census 2020 centers of population, block groups](https://www2.census.gov/geo/docs/reference/cenpop2020/blkgrp/) | 2020 | U.S. public domain | 2026-11-13 |
| [ACS 5-year summary file, table B01001](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/) | 2020-2024 | U.S. public domain | 2026-11-13 |
| [CMS Maternal Health - Hospital](https://data.cms.gov/provider-data/dataset/nrdb-3fcy), [Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u), [Birthing-Friendly Hospitals Geocoded](https://data.cms.gov/provider-data/dataset/hbf-map) | October 2026 refresh | U.S. public domain | 2026-11-13 |
| [Census Geocoder](https://geocoding.geo.census.gov/) (hospital addresses) | Public_AR_Current | U.S. public domain | 2026-11-13 |
| [Project 1 v0.1.0](https://doi.org/10.5281/zenodo.24025395): FindTreatment.gov listings, HRSA health center sites, NPPES obstetric clinicians by ZIP, USDA RUCC 2023 | November 2026 | CC BY 4.0 | 2026-11-13 |
| [Census 2024 Gazetteer ZCTAs and places; cartographic boundaries](https://www.census.gov/geographies/reference-files.html) | 2024 | U.S. public domain | 2026-11-13 |

## Headline numbers (from `report/stats.json`)

Nationally, 91.0% of women aged 15 to 44 live within 30 minutes of a delivering hospital, and 99.0% live within 60 minutes. More than 60 minutes from care:

| | Delivering hospital | Perinatal treatment facility | Health center |
|---|---|---|---|
| Metro women | 0.2% | 0.4% | 0.1% |
| Rural women | 5.0% | 13.3% | 4.1% |
| Frontier women | 34.1% | 53.4% | 33.9% |

In 556 rural or frontier counties, most women live more than an hour from a perinatal treatment facility. In 108 counties, most women live more than an hour from all three care types. These 108 are all rural or frontier, and most are very small: 101 are frontier, and 67 have fewer than 500 women aged 15 to 44.

In a check against OSRM, an open-source routing engine running on the same OpenStreetMap roads, the median time ratio was 0.99, and 99.1% of trips fell on the same side of the 60-minute cutoff. This confirms the routing computation, not the road map itself.

## Limitations

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before using or citing anything here. In short:
- These are free-flow car times.
- The nearest site is not always the one a woman uses.
- CMS under-lists rural delivering hospitals, so a range is given.
- The perinatal treatment flag covers substance use programs only.
- Places with no road route within 600 minutes, including islands without a car connection and Southeast Alaska ferry towns, are reported as unreachable.

## Citation and authorship

See `CITATION.cff`. The DOI is minted by Zenodo when the release is published; it is listed on the repository page.

Munachimso A. Emesobum made every measurement decision and checked results against his Nevada county maps. Claude (Anthropic) assisted with code and data handling.

Road-derived values contain information from OpenStreetMap, © OpenStreetMap contributors, available under the Open Database License (https://opendatacommons.org/licenses/odbl/).
