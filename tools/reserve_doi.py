#!/usr/bin/env python3
"""reserve_doi.py: create an empty Zenodo draft and reserve its DOI, so the DOI can be written into the
README, CITATION.cff, and paper BEFORE the files are archived.

Plain-language summary: Zenodo can hand out a DOI for a record you have not published yet. This script asks
for one and prints it. Nothing becomes public until the draft is published (zenodo_deposit.py --publish, or the
Publish button on zenodo.org). The same thing can be done by hand: zenodo.org > New upload > "Do you already
have a DOI?" No > "Get a DOI now!".

Usage:  ZENODO_TOKEN=... python3 tools/reserve_doi.py [--sandbox]
Prints the deposition id and the reserved DOI. Then run: python3 tools/set_doi.py <DOI>
"""
import argparse
import os
import sys

import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sandbox", action="store_true")
    a = ap.parse_args()
    host = "https://sandbox.zenodo.org" if a.sandbox else "https://zenodo.org"
    tok = os.environ.get("ZENODO_SANDBOX_TOKEN" if a.sandbox else "ZENODO_TOKEN")
    if not tok:
        sys.exit("set ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN with --sandbox)")
    r = requests.post(f"{host}/api/deposit/depositions", params={"access_token": tok}, json={
        "metadata": {"prereserve_doi": True, "upload_type": "dataset",
                     "title": "Rural and Frontier Perinatal Care Access Layer (reserved, not yet published)"}},
        timeout=60)
    r.raise_for_status()
    d = r.json()
    print(f"deposition id: {d['id']}")
    print(f"reserved DOI:  {d['metadata']['prereserve_doi']['doi']}")
    print(f"edit page:     {host}/deposit/{d['id']}")


if __name__ == "__main__":
    main()
