# Next steps

*Plain-language summary: what later versions will add. v0.1.0 is a first, complete national release; these items make it more useful, not correct.*

## Toward the July 2027 Public Perinatal Behavioral Health Readiness Map

1. **Join Project 1 and Project 2 on the county key `fips`.** Both releases share it, so the map can show need (Project 1), capacity (Project 1), and travel (Project 2) for each county from the two DOIs.
2. **Build the interactive national county map.** It will be a single public web page, with a static preview image for print. Layers will be: need score, capacity score, gap score, and the share of women beyond 30 or 60 minutes from each care type. The rural and frontier filter and a county search come from the shared table.
3. **Add a "facility exists but is out of reach" view.** It will flag counties that have a listed site, yet most of whose women live more than 30 minutes from any site of that type. Both inputs are already in the two releases.

## Measurement improvements

4. **Hospital obstetric status.** Resolve the 663 "status not reported" hospitals with state hospital licensing lists and hospital websites, starting with the states where the confirmed and upper-bound results differ most. Add freestanding birth centers.
5. **Level of care.** Add drive time to hospitals with a neonatal intensive care unit, or to the highest-level maternal care, where an open list exists.
6. **Clinician locations.** Place obstetric and behavioral health clinicians at their practice address instead of their ZIP center, by geocoding NPPES addresses.
7. **Perinatal mental health programs.** Add the HRSA Maternal Mental Health Hotline partner lists and state perinatal psychiatry access programs, if open lists become available.
8. **Typical-traffic times.** Add a peak-hour sensitivity version for metro counties.
9. **Winter and seasonal roads.** Flag frontier counties where the quickest route uses a seasonal or unpaved road.
10. **Annual refresh.** Re-run each spring with new OSM, CMS, and FindTreatment.gov data. Each refresh gets its own Zenodo version under the same concept DOI.
