# Limitations

*Plain-language summary: what these drive times cannot tell you. Read before using or citing any number. Each item is specific, so a reader can judge how much it matters for their use. Counts quoted here come from `data/processed/qa_report.txt`.*

1. **Free-flow drive times, not real trips.** Times assume no traffic, no waiting at lights, good weather, open roads, and a car. In the check against OSRM, they ran about 5% faster than OSRM in metro areas, where OSRM adds turn and signal penalties. Real metro trips at rush hour take longer still. Winter closures and gravel roads matter most in frontier counties, and these times do not capture them. Women without a car, and women who rely on public transit, face much longer trips than shown.

2. **Speeds are standard values, not measured ones.** Each road class gets the OSRM car-profile speed, or 0.8 times the posted limit where one is mapped. On a 55 mph two-lane highway, that is about 44 mph. Rural highway times may therefore run long compared with how people actually drive. This choice is conservative: it counts more women as beyond the thresholds, not fewer.

3. **The map is only as good as OpenStreetMap.** Missing, misclassified, or wrongly tagged roads change routes. A one-way tag in error can strand a neighborhood. Coverage of U.S. roads in OSM is close to complete, and the agreement with OSRM checks the routing, not the map itself. Alaska and Hawaii roads come from Overture Maps, a cleaned copy of OSM roads, because the open download mirror used for the other states does not include them.

4. **"Nearest" is not "the one she would use."** A woman may go past the nearest site because of insurance, the level of care she needs (for example a hospital with a neonatal unit), language, referral patterns, or trust. Nearest-site times show the minimum travel burden, not actual travel.

5. **Delivering hospitals are under-listed in rural areas.** CMS's maternal health file confirms labor and delivery status for 2,424 hospitals. It does not report status for many critical access hospitals, and some of them deliver babies. The upper-bound list (`ob_hosp_upper`) adds them. The truth for rural counties lies between the two measures. Freestanding birth centers are not included. Hospitals that closed their units after CMS's reporting period may still be listed.

6. **The perinatal treatment measure covers substance use programs only.** FindTreatment.gov records the "Pregnant/postpartum women" program only for substance use listings. No open national list flags mental health programs for perinatal women. `mh_any` (any mental health facility) is a supplement, not a perinatal measure. Telehealth care is not counted, although it may reduce the need to travel.

7. **Obstetric clinicians are placed at their ZIP code's center.** NPPES gives a practice ZIP, not an exact address. In large rural ZIPs, the ZIP center can be many miles from the actual office. 200 clinician ZIPs are PO box or business ZIPs with no area, and they could not be placed.

8. **Neighborhood centers stand in for every home.** Each block group's women are placed at its population center. Women at the far edge of a large rural block group may live much farther from care. In frontier block groups that cover hundreds of square miles, the true spread of drive times is wider than shown.

9. **Some places have no road to care.** Women in Alaska villages, on some islands (for example Lanai and the San Juan Islands), and in other off-road places cannot reach some care types by road. They are counted as beyond every threshold and reported separately (`<t>_women_unreachable`). For these places, air and boat travel is the real question, and drive time does not measure it.

10. **Site locations can be off.** Hospital addresses were geocoded by the Census Bureau, with CMS's own coordinates used for non-exact matches. For 55 hospitals, the two sources disagree by more than 2 km (listed in `qa_hospital_geocode_differences.csv`). FindTreatment.gov and HRSA coordinates are taken as published. Listings without coordinates were placed at their ZIP center.

11. **Data years differ.** Roads: November 2026. Hospitals: CMS October 2026 refresh, with reporting periods in 2024 and 2025. Treatment facilities, health centers, and clinicians: November 2026 (from Project 1). Women 15 to 44: ACS 2020-2024. Neighborhood centers: 2020 Census. Rural codes: 2023.

12. **Small counties are unstable.** Where few women live (`flag_small_women`), one block group can move the county share from 0% to 100%. Loving County, Texas has no women aged 15 to 44 in the ACS, so its shares are blank.

13. **Territories are excluded** in v0.1, as in Project 1.
