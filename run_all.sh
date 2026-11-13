#!/usr/bin/env bash
# Rebuild everything from scratch, in order. Needs about 30 GB of free disk and 8 GB of memory.
# Time: 30 to 60 minutes to download the 13 GB of road data, then about 30 minutes to build and route,
# plus about 10 minutes for the OSRM validation sample (one request per second to a public server).
# Until the author verifies a version, outputs carry DRAFT stamps. After verification: PANEL_FINAL=1 bash run_all.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 code/01_fetch.py          # sources, with provenance
python3 code/02_roads.py          # drivable road network (OpenStreetMap; Overture for AK and HI)
python3 code/03_sites.py          # care sites with locations
python3 code/04_origins.py        # block group centers and women aged 15 to 44
python3 code/05_route.py          # drive times
python3 code/06_county.py         # county summaries
python3 code/07_validate.py       # check against OSRM (uses saved results if present; --refresh to re-query)
python3 code/08_qa.py             # quality report
python3 code/09_figures.py        # figures and stats.json
echo "Done. Read data/processed/qa_report.txt first."
# Detailed preprint (paper/main.pdf): statistics, figures, number macros, then LaTeX
python3 paper/analysis.py
python3 paper/figures.py
python3 paper/make_numbers.py
(cd paper && latexmk -pdf -interaction=nonstopmode -quiet main.tex)
