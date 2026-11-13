# Preprint

*Plain-language summary: the detailed preprint describing this release. Every number in it comes from the data, never typed by hand.*

Build order (also at the end of `run_all.sh`):

1. `python3 paper/analysis.py`: extra statistics and LaTeX tables (`paper_stats.json`, `tables/`)
2. `python3 paper/figures.py`: figures in Matplotlib/Seaborn style (`figures/*.pdf`, `*.png`)
3. `python3 paper/make_numbers.py`: number macros (`numbers.tex`) from `report/stats.json` and `paper_stats.json`
4. `cd paper && latexmk -pdf main.tex`: `main.pdf`

The layout follows a two-column physics-preprint style (Roman-numeral sections, "FIG." and "TABLE" captions).
