# Build spec: Rural and Frontier Perinatal Care Access Layer (v0.1.0)

*Plain-language note: this is the one-page plan the build follows. Each line says what was decided. You only need it if you want to see the plan in one place; the decisions you rule on are repeated in VERIFY_CHECKLIST.md Part 4.*

```
PROJECT:        Rural and Frontier Perinatal Care Access Layer. Archetypes: open dataset (primary) + method/analysis paper.
QUESTION:       For every U.S. county, what share of women aged 15 to 44 live more than 30 and more than 60 minutes'
                drive from (a) a hospital that delivers babies, (b) a treatment facility serving pregnant or
                postpartum women, (c) a community health center; and how do rural and frontier counties compare?
SOURCES:        OpenStreetMap US regional extracts (openstreetmap.fr, data of 2026-11-13; ODbL)
                Overture Maps transportation 2026-10-21.0 (OSM-derived roads) for Alaska and Hawaii (ODbL)
                Census 2020 population-weighted block group centers (public domain)
                ACS 2020-2024 5-year table B01001, block groups (public domain)
                CMS Maternal Health - Hospital; Hospital General Information; Birthing-Friendly Hospitals Geocoded
                  (CMS Provider Data Catalog, refreshed October 2026; public domain)
                Census Geocoder batch service (hospital addresses)
                Project 1 v0.1.0, DOI 10.5281/zenodo.24025395 (FindTreatment.gov listings, HRSA health center
                  sites, NPPES obstetric clinicians by ZIP, RUCC 2023 rural and frontier flags; CC BY 4.0)
                Census 2024 Gazetteer ZCTAs and places; 2024 cartographic county and state boundaries
UNIT:           County (3,144; Census Vintage 2024 geography, 50 states + DC). Block-group detail file also released.
MEASURES:       Drive time (free-flow minutes) from each block group center to the nearest site of each type,
                by Dijkstra shortest path on the national OSM road graph (OSRM car-profile speeds; one-way
                streets respected; routing crosses state lines). County: share of women 15-44 beyond 30 and 60
                minutes, median and women-weighted mean minutes, women unreachable by road.
                Six site types: ob_hosp (headline), ob_hosp_upper (sensitivity), ob_clin (supplement),
                ppw_bh (headline), mh_any (supplement), hc (headline).
OUTPUTS:        data/processed/access_county.csv (main), access_by_rurality.csv, bg_drive_times.csv, sites.csv,
                validation_osrm_sample.csv, qa_report.txt; report/figures/*.png; report/stats.json;
                docs/METHODS_ROUTING.md (routing method notes); paper/ (preprint draft)
VENUES:         GitHub (memesobum/perinatal-access-layer) -> Zenodo DOI (target May 2027, delivered early) ->
                preprint (medRxiv or preprints.org) -> feeds the July 2027 interactive Readiness Map.
VERIFY POINTS:  site definitions (DECISION 4); speeds and connector rule (DECISIONS 1, 3); thresholds (DECISION 5);
                spot checks against the author's Nevada maps; OSRM agreement; geocode differences list.
LICENSE:        Code MIT; data and documents CC BY 4.0, with OpenStreetMap attribution (ODbL) for road-derived values.
ASSUMPTIONS:    Defaults proposed in chat on 2026-11-13 are in use until the author rules on them.
```
