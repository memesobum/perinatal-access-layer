# Publishing guide

*Plain-language summary: step-by-step instructions for putting Project 2 on GitHub, getting its DOI from Zenodo, and posting the paper as a preprint. Nothing has been uploaded yet. Do these steps only after you finish `VERIFY_CHECKLIST.md` and Claude has rebuilt the files without draft stamps. For Project 1 you already turned on the GitHub-to-Zenodo link, so for this project the DOI is made automatically when you publish a GitHub release.*

## Copy-ready text

**Repository name:** `perinatal-access-layer`

**Repository description:** Open drive-time measures from every U.S. neighborhood to delivering hospitals, perinatal substance use treatment, and health centers, summarized by county, with rural and frontier results.

**Title (Zenodo and citation):** Rural and Frontier Perinatal Care Access Layer: County Drive-Time Measures to Perinatal Care Service Types

**Author:** Emesobum, Munachimso A. | ORCID 0009-0002-7506-2153 | Independent Researcher, Nevada, USA

**Keywords:** perinatal behavioral health; travel time; drive time; geographic access; obstetric care; substance use treatment; rural health; frontier; OpenStreetMap; open data

**License:** code MIT; data and documents CC BY 4.0; road-derived values contain information from OpenStreetMap (© OpenStreetMap contributors, ODbL)

**Related work:** Project 1, DOI 10.5281/zenodo.24025395 (relation: "Is derived from" or "References")

## Before any upload (5 min)

1. Tell Claude "verified", and Claude rebuilds the files with `PANEL_FINAL=1`.
2. Run `python3 tools/publish_gate.py . --allow-draft-in code tools paper`. It must print `gate: clear`.

## Option A: Claude uploads for you (10 min of your time)

1. **GitHub token.** Go to https://github.com/settings/tokens/new and fill in:
   - Note: "access layer upload"
   - Expiration: 7 days
   - Tick the **repo** box.

   Click **Generate token** and copy the token (it starts with `ghp_`).
2. In a Claude session with this project, say: "Publish Project 2. Here is my GitHub token." Claude then:
   - creates the repository
   - pushes the files
   - shows you the page
   - publishes release `v0.1.0` only after you say yes
3. Zenodo makes the DOI by itself within a few minutes. To find it, go to https://zenodo.org/account/settings/github/ and click the repository. Then delete the token at https://github.com/settings/tokens. (A token is a temporary password. Deleting it ends Claude's access.)

## Option B: you upload (about 30 min)

1. Go to https://github.com/new and fill in:
   - Name: `perinatal-access-layer`
   - Visibility: Public
   - Do **not** add a README.

   Click **Create repository**.
2. Go to https://zenodo.org/account/settings/github/, click **Sync now**, and flip the switch next to `memesobum/perinatal-access-layer` to **On**.
3. Push the project. The project folder is already a Git repository with one commit under your name. In a terminal inside the folder, paste:
   ```
   git remote add origin https://github.com/memesobum/perinatal-access-layer.git
   git push -u origin main
   ```
   When asked for a password, paste a GitHub token (Option A, step 1), not your account password.
4. On GitHub, click **Releases**, then **Draft a new release**, and fill in:
   - Tag: `v0.1.0` (choose "create new tag")
   - Title: `v0.1.0`
   - Description: paste your own one-paragraph summary.

   Click **Publish release**.
5. Wait about 5 minutes, then open https://zenodo.org/account/settings/github/ and click the repository. The DOI badge appears, with a number like `10.5281/zenodo.NUMBER`.
6. On the Zenodo record, click **Edit** and make three changes:
   - Under Related works, add Project 1's DOI (10.5281/zenodo.24025395) as "References".
   - Check that the license says CC BY 4.0.
   - Paste the keywords above.

   Then click **Publish**.

## The same day you publish (10 min)

1. Tell Claude the DOI. Claude then:
   - puts it in the README, `CITATION.cff`, and the paper
   - replaces "[DOI pending]"
   - rebuilds the paper
   - commits these changes
2. Save the Zenodo page as a PDF (browser Print, then Save as PDF).
3. Add a row to `docs/EVIDENCE_LOG.csv` (Claude can do this). Publications not logged the day they happen are the ones that go missing later.

## Preprint (20 min, after the DOI exists)

You used preprints.org for Project 1. The same server suits this paper. medRxiv is the other option for a health-services paper.
1. Log in at https://www.preprints.org and click **Submit**. Choose subject area **Public Health and Healthcare**, and article type **Article**.
2. Upload `paper/main.pdf`. Paste the title, the abstract (your own words), and the keywords above.
3. Author: as above, with ORCID. Under data availability, give the GitHub link and the DOI.
4. Declarations:
   - Funding: none.
   - Competing interests: none.
   - AI use: "Claude (Anthropic) assisted with code and data handling; the author made every measurement decision and verified the results."
5. Submit, and save the confirmation email. Log the preprint DOI when it arrives.
