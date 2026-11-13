# Changelog

*Plain-language summary: what changed, and when. Each release on Zenodo matches one entry here.*

## v0.1.0 (verified by the author 2026-11-13; not yet released)

### Changes made after the author's review, 2026-11-13

The author's review re-computed every headline number and checklist row from the released files and found them correct. It raised the issues below. All were fixed before release. Every checklist row in VERIFY_CHECKLIST.md gives the same value after the fixes.

1. **Nevada paragraph (paper).** Five Nevada counties have no woman within an hour of a delivering hospital: Esmeralda, Eureka, Lincoln, Mineral, and Pershing. The draft named three. The list is now generated from the data.
2. **Publish gate.**
   - `tools/gate.sh` runs the gate with a short, explained list of files that legitimately mention draft stamps.
   - `tools/reserve_doi.py` and `tools/set_doi.py` reserve the Zenodo DOI first and write it into the README, CITATION.cff, and paper before release.
   - PUBLISH_GUIDE.md now follows that order.
3. **Sites in the wrong state.** `03_sites.py` now checks every site's coordinates against its listed state. Points in the wrong state move to the ZIP center, or are left unplaced if that is also wrong. Six rows were affected, listed in `qa_site_state_mismatches.csv`:
   - Community Counseling Solutions, Arlington, OR, which had been placed in Arlington, TX
   - Lost River Treatment Center, Wyandotte, OK
   - four mental-health listings
4. **Islands attached across water.** A new rule marks neighborhoods on islands and shores with no car connection as having no road route out, instead of attaching them to the mainland across the water. Examples are Kalaupapa (HI), Bald Head Island (NC), Mackinac Island, the Maine islands, Fire Island, and Point Roberts (WA). This affects 259 block groups and 2,083 women, most in block groups with no women.
5. **Hospitals placed at a distant ZIP center.** 125 hospitals whose address the geocoder cannot match are now placed at their town's Census place point instead of the ZIP center. This mattered most in Alaska: Norton Sound Regional Hospital had been placed about 40 km from Nome, and Maniilaq Health Center far from Kotzebue.
6. **Wording.**
   - The OSRM check is described as checking the routing computation on the same roads, not as an independent check of the map.
   - The Rayburn comparison now notes that study's population (women 18 to 39), its years (2007 hospitals, 2010 population), and its network.
   - The 108 "all three" counties are described as mostly very small frontier counties.
   - Southeast Alaska ferry towns are explained correctly. The ferry is in the data, but long crossings at the OSRM default of 5 km/h exceed the 600-minute limit.
7. **Road length.** The abstract no longer quotes a road total. The methods now give 8.0 million km of mapped road lines, counted once across regional files, with divided highways counted in both directions and private roads included, plus 15,000 km of ferry routes.
8. **References.** Every DOI was checked against Crossref. The Ranchoff et al. volume and article number (71(2):108315) were added.
9. **Health center count.** 11,769 health center sites is the same as Project 1's 11,769 counted sites: 11,768 have HRSA coordinates and 1 is placed at its ZIP point. The QA report now says so.

**Effect on headline numbers (before → after).**

| Measure | Before | After |
|---|---|---|
| Women within 30 / 60 minutes of a delivering hospital | 91.0% / 99.0% | unchanged |
| Rural women more than 60 minutes from a delivering hospital | 5.0% | unchanged |
| Frontier women more than 60 minutes from a delivering hospital | 34.7% | 34.1% |
| Frontier women more than 60 minutes from a delivering hospital, upper bound | 17.3% | 15.9% |
| Frontier women more than 60 minutes from a perinatal treatment facility | 53.4% | unchanged |
| Frontier women more than 60 minutes from a health center | 33.6% | 33.9% |
| Counties with most women more than 60 minutes from all three care types | 107 | 108 |
| Rural and frontier women more than 60 minutes from a delivering hospital, confirmed list | 528,879 | 525,205 |
| Same, upper-bound list | 249,798 | 240,903 |
| OSRM check (re-run on the final routes): median ratio | 0.99 | 0.99 |
| OSRM check: within 20% or 5 minutes | 97.3% | 98.2% |
| OSRM check: agreement at 60 minutes | 99.1% | 99.1% |
