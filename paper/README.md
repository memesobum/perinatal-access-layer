# Preprint

*Plain-language summary: the detailed preprint describing this release. Every number in it comes from the data, never typed by hand.*

Build order (also at the end of `run_all.sh`):

1. `python3 paper/analysis.py`: extra statistics and LaTeX tables (`paper_stats.json`, `tables/`)
2. `python3 paper/figures.py`: figures in Matplotlib/Seaborn style (`figures/*.pdf`, `*.png`)
3. `python3 paper/make_numbers.py`: number macros (`numbers.tex`) from `report/stats.json` and `paper_stats.json`
4. `cd paper && latexmk -pdf main.tex`: `main.pdf`

The layout follows a two-column physics-preprint style (Roman-numeral sections, "FIG." and "TABLE" captions).

## preprints.org upload set

After the steps above:

5. `python3 paper/word/make_docx_source.py`, then
   `cd paper && pandoc word/manuscript_for_pandoc.tex -f latex -t docx --reference-doc=word/ref_palatino.docx --resource-path=. -o word/raw.docx && python3 word/fix_tables.py word/raw.docx word/Emesobum_manuscript.docx`
6. `python3 paper/graphic_abstract.py`
7. `python3 paper/make_submission.py`

The upload map (form field to file) is at the top of `make_submission.py`. The supplementary PDF combines docs/METHODS_ROUTING.md, docs/CODEBOOK.md, docs/LIMITATIONS.md, data/processed/qa_report.txt, and docs/CHANGELOG.md.
