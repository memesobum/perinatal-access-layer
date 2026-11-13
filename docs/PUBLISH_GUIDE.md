# Publishing guide

*Plain-language summary: step-by-step instructions to get Project 2 a DOI, put it on GitHub and Zenodo, and post the paper. You verified v0.1.0 on 2026-11-13 and the files are built without draft stamps. Two things must still happen before the publish gate passes: the DOI is reserved, and that DOI is written into the files. This guide does both, in the right order.*

## Why the order matters

The README, citation file, and paper should carry the DOI of the archive they sit in. Zenodo can **reserve** a DOI before anything is published, so the order is:

1. Reserve the DOI.
2. Write it into the files.
3. Pass the gate.
4. Push to GitHub.
5. Upload the archive to the reserved Zenodo record and publish it.

**Important: leave the GitHub-to-Zenodo switch OFF for this repository.** You turned that link on for Project 1. If it is also on for this repository, a GitHub release makes a second, different DOI. For this project, Zenodo is filled by hand (or by Claude) using the reserved DOI.

## Copy-ready text

**Repository name:** `perinatal-access-layer`

**Repository description:** Open drive-time measures from every U.S. neighborhood to delivering hospitals, perinatal substance use treatment, and health centers, summarized by county, with rural and frontier results.

**Title (Zenodo and citation):** Rural and Frontier Perinatal Care Access Layer: County Drive-Time Measures to Perinatal Care Service Types

**Author:** Emesobum, Munachimso A. | ORCID 0009-0002-7506-2153 | Independent Researcher, Nevada, USA

**Keywords:** perinatal behavioral health; travel time; drive time; geographic access; obstetric care; substance use treatment; rural health; frontier; OpenStreetMap; open data

**License:** Creative Commons Attribution 4.0 International. Code inside is MIT. Road-derived values: © OpenStreetMap contributors (ODbL).

**Version:** 0.1.0. **Resource type:** Dataset.

**Description:** use the "In plain terms" paragraph from README.md, followed by the headline table.

**Related works:**
- `https://github.com/memesobum/perinatal-access-layer`, relation "Is supplemented by"
- Project 1, `10.5281/zenodo.24025395`, relation "References"

## Option A: Claude does it (about 10 minutes of your time)

1. **Zenodo token.** Go to https://zenodo.org/account/settings/applications/tokens/new/ and fill in:
   - Name: "access layer"
   - Tick **deposit:write** and **deposit:actions**.

   Click **Create** and copy the token.
2. **GitHub token.** Go to https://github.com/settings/tokens/new and fill in:
   - Note: "access layer"
   - Expiration: 7 days
   - Tick **repo**.

   Click **Generate token** and copy the token.
3. In a Claude session with this project, say: "Publish Project 2. Here are my tokens." Claude then:
   - runs `tools/reserve_doi.py` and `tools/set_doi.py`, and rebuilds the paper
   - runs `tools/gate.sh` until it prints `gate: clear`
   - pushes to GitHub
   - tests the Zenodo upload on the Zenodo sandbox and shows you the practice record
   - publishes the real record only after you say yes
4. Afterward, delete both tokens: GitHub at https://github.com/settings/tokens and Zenodo at https://zenodo.org/account/settings/applications/.

## Option B: you do it (about 40 minutes)

1. **Reserve the DOI.** Log in at https://zenodo.org (Log in with ORCID) and click **New upload**. Under "Do you already have a DOI?" choose **No**, then click **Get a DOI now!**. Copy the DOI shown (it looks like `10.5281/zenodo.1234567`). Click **Save draft** and leave the page open.
2. **Write the DOI into the files.** In a terminal in the project folder, run:
   ```
   python3 tools/set_doi.py 10.5281/zenodo.1234567
   python3 paper/make_tex_inputs.py && (cd paper && latexmk -pdf -quiet main.tex)
   bash tools/gate.sh
   ```
   The last line must print `gate: clear`.
3. **Commit, then push to GitHub.** Go to https://github.com/new and fill in:
   - Name: `perinatal-access-layer`
   - Visibility: Public
   - Do **not** add a README.

   Click **Create repository**. Then in the project folder run:
   ```
   git add -A && git commit -m "Add DOI"
   git tag v0.1.0
   git remote add origin https://github.com/memesobum/perinatal-access-layer.git
   git push -u origin main --tags
   ```
   When asked for a password, paste the GitHub token (Option A, step 2), not your account password.
4. **Make the archive.** On the GitHub repository page, click **Code** and then **Download ZIP**.
5. **Fill the Zenodo draft.** Go back to the draft from step 1 and fill in:
   - Upload the ZIP.
   - Fill the fields from "Copy-ready text" above.
   - Add yourself as creator, with your ORCID.

   Click **Preview**, read it once, then click **Publish**.

## The same day you publish (10 min)

1. Save the Zenodo record page as a PDF (browser Print, then Save as PDF).
2. Ask Claude to add a row to `docs/EVIDENCE_LOG.csv`, or add it yourself:
   `2026-MM-DD,Perinatal Care Access Layer v0.1.0,dataset,Zenodo + GitHub,10.5281/zenodo.NUMBER,live,https://doi.org/10.5281/zenodo.NUMBER,0 downloads at release,zenodo_record.pdf,Verified by author 2026-11-13`

   Publications not logged the day they happen are the ones that go missing later.

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
