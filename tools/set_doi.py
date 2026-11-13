#!/usr/bin/env python3
"""set_doi.py: write the reserved Zenodo DOI and the release date into README.md, CITATION.cff, and the paper.

Plain-language summary: after reserve_doi.py (or Zenodo's "Get a DOI now!" button) gives you a DOI, run this
once. It replaces every "[DOI pending]" and "[release date pending]" and records the DOI in report/doi.txt,
which the paper build reads. Then rebuild the paper (see run_all.sh) and run tools/gate.sh.

Usage:  python3 tools/set_doi.py 10.5281/zenodo.NNNNNNN [--date YYYY-MM-DD]
"""
import argparse
import datetime
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = ["README.md", "CITATION.cff", "paper/main.tex", "docs/PUBLISH_GUIDE.md", "docs/TALK_TRACK.md"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doi")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    if not re.fullmatch(r"10\.\d{4,9}/zenodo\.\d+", a.doi):
        raise SystemExit(f"not a Zenodo DOI: {a.doi}")
    for rel in FILES:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        n = t.replace("[DOI pending]", a.doi).replace("[release date pending]", a.date)
        if n != t:
            open(p, "w", encoding="utf-8").write(n)
            print(f"updated {rel}")
    open(os.path.join(ROOT, "report", "doi.txt"), "w").write(a.doi + "\n")


if __name__ == "__main__":
    main()
