# Publishing guide

*Plain-language summary: v0.1.0 is published. This page records how, and what is left (the preprint).*

## What was done on 2026-11-13

- GitHub repository created: https://github.com/memesobum/perinatal-access-layer (public).
- Zenodo's GitHub link switched on for this repository; release v0.1.0 published on GitHub; Zenodo archived it automatically.
- DOI for v0.1.0: **10.5281/zenodo.24206837** (https://doi.org/10.5281/zenodo.24206837). DOI for all versions: 10.5281/zenodo.24206836.
- The DOI was then written into README.md, CITATION.cff, and the paper on the main branch (after the release, because a GitHub-linked DOI only exists once the release is made).
- Logged in docs/EVIDENCE_LOG.csv. Save the Zenodo record page as a PDF for your records.

**Future versions:** because the GitHub link is on, every new GitHub release (v0.2.0 and so on) gets its own DOI automatically, under the same all-versions DOI. The reserve-DOI tools (`tools/reserve_doi.py`, `tools/set_doi.py`) remain available if you ever prefer to put the DOI inside the archived files instead.

## Preprint (20 min, after the DOI is live)

You used preprints.org for Project 1, and it suits this paper too. medRxiv is the other option for a health-services paper.

1. Log in at https://www.preprints.org and click **Submit**. Choose subject area **Public Health and Healthcare**, and article type **Article**.
2. Upload `paper/main.pdf`. Paste the title, the abstract, and the keywords above.
3. Author: as above, with ORCID. Under data availability, give the GitHub link and the DOI.
4. Declarations:
   - Funding: none.
   - Competing interests: none.
   - AI use: "Claude (Anthropic) assisted with code and data handling; the author made every measurement decision and verified the results."
5. Submit, and save the confirmation email. Log the preprint DOI when it arrives.
