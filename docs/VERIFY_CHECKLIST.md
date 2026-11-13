# Your verification checklist (v0.1.0)

**Verified by the author on 2026-11-13**, with the review fixes listed in `docs/CHANGELOG.md` applied the same day. Every checklist row below gave the same value after the fixes. Defaults were accepted for decisions D1 to D5.

*Plain-language version: before anything goes public under your name, you check it. Total time: about 1.5 to 2 hours, in one sitting. Tick each box and write the date. The publish gate (`python3 tools/publish_gate.py .`) checks the mechanical items, such as leftover DRAFT stamps and placeholders. These items are yours.*

**How to check a drive time by hand.** Every row below gives a Google Maps link that opens directions from the neighborhood center to the care site. Read Google's drive time and compare it with ours.

What to expect:
- Google uses real traffic speeds, so in cities it is often a few minutes slower than ours.
- On long rural highways, Google is often faster than ours, because our standard speed on a 55 mph two-lane road is about 44 mph (see LIMITATIONS item 2).
- A "match" means the same nearest site, and a time that is close (within about 20%) or off in the expected direction.

You can also check the same trip on the open OSRM map: https://map.project-osrm.org (drop the two points).

## Part 1: Make sure the results can be rebuilt (15 to 30 min)

Pick one:
- [ ] **Option A, run it yourself.** You need a Linux or Mac computer with 8 GB of memory and 30 GB of free disk. In a terminal, in the project folder, paste these commands:
  ```
  sudo apt install osmium-tool        # Mac: brew install osmium-tool
  pip install -r requirements.txt
  bash run_all.sh
  ```
  It takes about 1.5 to 2 hours. At the end it prints `Done. Read data/processed/qa_report.txt first.`
- [ ] **Option B, ask Claude.** In a new chat with Opus 5.5 or Fable 5, say: "Clone github.com/memesobum/perinatal-access-layer, re-run run_all.sh from scratch, and give me the headline numbers." Then compare its numbers with the ones below. OpenStreetMap changes daily, so expect small differences in the first decimal place, not large ones.
  - Women 15 to 44 within 30 minutes of a delivering hospital: **91.0%**. Within 60 minutes: **99.0%**.
  - Frontier women more than 60 minutes from a perinatal treatment facility: **53.4%**.
  - Counties where most women are more than 60 minutes from all three care types: **108** (107 before the review fixes; see CHANGELOG).
  - OSRM check: median ratio **0.99**, and **99.1%** agreement on the 60-minute line.

Then:
- [ ] Every number in `paper/main.pdf` and the README matches `report/stats.json`. The paper reads its numbers from that file, so check three at random.

## Part 2: Check the sources (15 min)

- [ ] Open each source link in the README. Each page still loads and is free to use.
- [ ] Licenses:
  - OpenStreetMap and Overture roads: Open Database License (ODbL). We must credit "© OpenStreetMap contributors", and the README and LICENSE-DATA.md do.
  - Census, ACS, CMS, HRSA, SAMHSA, and USDA: U.S. government works (public domain).
  - Project 1: CC BY 4.0 (yours).
- [ ] The CMS maternal health file is the October 2026 refresh. The next CMS refresh is due around January 2027 and can go in v0.2.

## Part 3: Check rows by hand (30 to 45 min)

All rows are in `data/processed/bg_drive_times.csv`. Find each one by its `geoid` (the first column; use Ctrl+F).

**Five you know personally (Nevada)**
- [ ] `320339702001`, White Pine County (Ely). Nearest delivering hospital: William Bee Ririe Hospital, **1.8 min**. [Check](https://www.google.com/maps/dir/39.25155,-114.86042/39.25609,-114.85982) ___
- [ ] `320339702001`, White Pine County. Nearest perinatal treatment facility: Central Utah Counseling Center, Delta UT, **182 min**. Is there really nothing closer, for example in Ely, Elko, or Wendover? You know this area. [Check](https://www.google.com/maps/dir/39.25155,-114.86042/39.35335,-112.57531) ___
- [ ] `320239604071`, Nye County (Pahrump). Nearest delivering hospital: Southern Hills Hospital, Las Vegas, **59.8 min**. [Check](https://www.google.com/maps/dir/36.19260,-115.98844/36.07032,-115.29438) ___
- [ ] `320130107021`, Humboldt County. Nearest delivering hospital: Humboldt General Hospital, Winnemucca, **15.0 min**. [Check](https://www.google.com/maps/dir/40.90283,-117.75451/40.97156,-117.72834) ___
- [ ] `320079514031`, Elko County. Nearest health center: Elko Family Medical & Dental Center, **24.0 min**. [Check](https://www.google.com/maps/dir/40.73729,-115.59876/40.84206,-115.75816) ___
- [ ] Also open `data/processed/access_county.csv`, filter `state` = NV, and compare the 17 rows with your Larson Institute maps. Does every county your maps showed without OB/GYN care have a long drive to a delivering hospital here? ___

**Five extreme values**
- [ ] `022400001001`, Southeast Fairbanks Census Area, AK (Tok area). Delivering hospital: Fairbanks Memorial, **281 min**, the longest routed time. Expect Google to say about 3.5 to 4 hours, which is the slow-highway effect. [Check](https://www.google.com/maps/dir/63.51841,-142.38600/64.83461,-147.73913) ___
- [ ] `022400001001`, the same block group. Perinatal treatment: Fairbanks Native Association, **279 min**. [Check](https://www.google.com/maps/dir/63.51841,-142.38600/64.81826,-147.71313) ___
- [ ] `160859701001`, Valley County, ID (backcountry). Health center: Adams County Health Center, Council, **256 min**. Is the route over seasonal gravel roads? [Check](https://www.google.com/maps/dir/44.92484,-115.48173/44.73119,-116.42940) ___
- [ ] `250250711012`, Suffolk County, MA. Delivering hospital: Boston Medical Center, **0.03 min**. This is the shortest: the neighborhood center sits at the hospital. [Check](https://www.google.com/maps/dir/42.33463,-71.07548/42.33470,-71.07540) ___
- [ ] `access_county.csv`, Yukon-Koyukuk Census Area, AK (`02290`). `ob_hosp_women_unreachable` should be most of the county's women, because these villages have no road out. ___

**Five random rows (chosen by computer, seed 7)**
- [ ] `360610191003`, New York County, NY. Mount Sinai Hospital, **4.3 min**. [Check](https://www.google.com/maps/dir/40.80063,-73.96858/40.79049,-73.95379) ___
- [ ] `371950005021`, Wilson County, NC. BHG Wilson Treatment Center, **2.4 min**. [Check](https://www.google.com/maps/dir/35.75723,-77.93703/35.76852,-77.93984) ___
- [ ] `517100044003`, Norfolk city, VA. CommuniCare Family Health Center, **4.9 min**. [Check](https://www.google.com/maps/dir/36.85795,-76.25481/36.85589,-76.28333) ___
- [ ] `340311964011`, Passaic County, NJ. Chilton Medical Center, **6.6 min**. [Check](https://www.google.com/maps/dir/40.99179,-74.28967/40.95952,-74.30829) ___
- [ ] `484019506001`, Rusk County, TX. Alcohol and Drug Abuse Council, Nacogdoches, **50.5 min**. [Check](https://www.google.com/maps/dir/32.04533,-94.68848/31.61582,-94.63973) ___

**Hospital locations (10 min)**
- [ ] Open `data/processed/qa_hospital_geocode_differences.csv`. Pick three hospitals, search each name in Google Maps, and confirm the location we used. The `geo_method` column says which point was used. ___

## Part 4: Your decisions (10 min)

The build made these choices provisionally. Agree with each one or change it. Changing one means editing `code/config.py` and re-running, which takes about 30 minutes.

- [ ] **D1. Which hospitals count as "delivering."** Option A, the current choice: hospitals confirmed by CMS (2,424) as the headline, with the 3,087-hospital upper bound shown beside it. Option B: use the upper bound as the headline. That gives fewer counties cut off, but it counts some hospitals that may not deliver. Recommended: A. Your choice: ___
- [ ] **D2. Speeds.** Option A, the current choice: OSRM standard speeds (0.8 times the posted limit). Results then match the OSRM engine and lean conservative on rural highways. Option B: use the full posted limit. That gives shorter rural times, closer to Google, but no longer matches an engine anyone can check against. Recommended: A. Your choice: ___
- [ ] **D3. Thresholds.** Option A, the current choice: 30 and 60 minutes, the cutoffs used in published obstetric access studies. Option B: add 90 or 120 minutes for frontier reporting. Recommended: A, with B as a v0.2 addition. Your choice: ___
- [ ] **D4. Private roads.** Option A, the current choice: keep private roads, so homes in gated areas and on military bases can drive out. Option B: drop them, as OSRM does. That strands about 1,000 to 2,000 women per affected county in places like Beaufort, SC and Davis County, UT. Recommended: A. Your choice: ___
- [ ] **D5. Perinatal treatment measure.** Option A, the current choice: the substance use programs flagged "pregnant/postpartum" as the headline, with any mental health facility as a supplement. Option B: make "any mental health facility" a headline measure too. Recommended: A, because the "any mental health facility" measure is not perinatal-specific. Your choice: ___

## Part 5: Before it goes public (15 to 30 min)

- [ ] The README summary ("In plain terms") and the paper abstract are rewritten in your own words. Nothing remains that you could not explain or defend. Claude can do this with you line by line.
- [ ] Your name, ORCID, affiliation, and email are correct in `AUTHORS.json` (copied from Project 1).
- [ ] You have read `docs/LIMITATIONS.md` and `docs/METHODS_ROUTING.md`, and you agree with them.
- [x] You tell Claude "verified". Claude rebuilt the files with `PANEL_FINAL=1` to remove the draft stamps (done 2026-11-13).
- [x] Published 2026-11-13: GitHub release v0.1.0, Zenodo DOI 10.5281/zenodo.24206837. `bash tools/gate.sh` passed before release.

Verified by: Munachimso A. Emesobum  Date: 2026-11-13
