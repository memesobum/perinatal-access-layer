# Codebook

*Plain-language summary: every column in every released table, what it means, and where it comes from. Open this when you need to know exactly what a column holds. Minutes are free-flow car minutes (see METHODS_ROUTING.md). "Women" always means women aged 15 to 44 (ACS 2020-2024 5-year).*

## Care type codes (`<t>` below)

| Code | Care type | Role |
|---|---|---|
| `ob_hosp` | Hospital providing inpatient labor and delivery care, confirmed in CMS Maternal Health - Hospital (SM_7 = Yes or No, or perinatal care measures PC_02/PC_07 reported with a nonzero sample) | headline |
| `ob_hosp_upper` | `ob_hosp` plus general acute care and critical access hospitals whose labor and delivery status CMS lists as "Not Available" | sensitivity (upper bound on access) |
| `ob_clin` | ZIP code with at least one obstetric clinician (OB/GYN, midwife, women's health or perinatal NP or CNS; NPPES primary practice ZIP, from Project 1), placed at the ZIP's interior point | supplement |
| `ppw_bh` | FindTreatment.gov listing flagged "Pregnant/postpartum women" (Project 1 `serves_ppw = 1`; substance use listings) | headline |
| `mh_any` | FindTreatment.gov mental health listing (facility type MH), any population | supplement |
| `hc` | HRSA health center site (Project 1 rules: active, permanent, not school or correctional) | headline |

## `data/processed/access_county.csv` (one row per county; main deliverable)

| Column | Meaning | Source |
|---|---|---|
| `fips` | 5-digit county FIPS code, Census Vintage 2024 geography (Connecticut planning regions) | Census |
| `state`, `county_name` | State abbreviation, county name | Project 1 |
| `rucc_2023` | USDA ERS Rural-Urban Continuum Code 2023 | Project 1 |
| `pop_density_2024` | Persons per square mile of land, 2024 | Project 1 |
| `rural` | 1 if RUCC 4 to 9 (nonmetro) | Project 1 |
| `frontier` | 1 if fewer than 6 persons per square mile | Project 1 |
| `rurality_class` | metro, rural, or frontier (frontier wins when both apply) | Project 1 |
| `births` | Annual births (Project 1 rule) | Project 1 |
| `women_15_44` | Women aged 15 to 44 in the county's block groups | ACS B01001 |
| `block_groups`, `block_groups_no_women` | Number of block groups; how many have zero women 15 to 44 | Census |
| `<t>_women_gt30`, `<t>_women_gt60` | Women whose drive to the nearest `<t>` site is more than 30 (60) minutes, or who cannot reach one by road | computed |
| `<t>_share_gt30`, `<t>_share_gt60` | The same as a share of the county's women (0 to 1). Blank where the county has no women 15 to 44 | computed |
| `<t>_women_unreachable` | Women in block groups with no road route to any `<t>` site (or more than 25 km from a road) | computed |
| `<t>_median_min` | Women-weighted median drive, minutes. Blank if the median woman cannot reach a site by road (see next column) | computed |
| `<t>_median_unreachable` | 1 if more than half the county's women cannot reach a `<t>` site by road | computed |
| `<t>_mean_min` | Women-weighted mean drive among women who can reach a site, minutes | computed |
| `<t>_max_min` | Longest block group drive in the county, minutes | computed |
| `ob_hosp_main_site_id`, `_name` (also `ppw_bh_`, `hc_`) | The site that is nearest for the largest number of the county's women. Site ids: `CCN` + CMS certification number; `FT` + Project 1 facility id; HRSA BPHC site number | computed |
| `flag_small_women` | 1 if fewer than 500 women 15 to 44: shares rest on few people | computed |
| `flag_some_unreachable` | 1 if any women cannot reach a delivering hospital by road | computed |

## `data/processed/access_by_rurality.csv`

One row per group (All counties, Metro, Rural (nonmetro, not frontier), Frontier, Rural or frontier). Columns: `counties`, `women_15_44`; for each `<t>`: `<t>_share_gt30`, `<t>_share_gt60` (women beyond, divided by women in the group), `<t>_counties_majority_gt30`, `<t>_counties_majority_gt60` (counties where more than half of women are beyond), and `<t>_women_unreachable`.

Note: "Frontier" includes 22 counties that are metro by RUCC but have fewer than 6 people per square mile; "Metro" excludes them. "Rural or frontier" is RUCC 4 to 9 or frontier.

## `data/processed/bg_drive_times.csv` (one row per block group)

| Column | Meaning |
|---|---|
| `geoid` | 12-digit block group GEOID (Connecticut re-keyed to planning regions) |
| `fips` | County FIPS |
| `lat`, `lon` | 2020 population-weighted center |
| `pop2020` | 2020 Census population (from the center file) |
| `women_15_44`, `women_15_44_moe` | ACS estimate and 90% margin of error (summed by the Census approximation) |
| `snap_km` | Straight-line km from the center to its road point |
| `connected` | False if more than 25 km from any usable road |
| `origin_conn_min` | Connector minutes from center to road |
| `min_<t>` | Drive minutes to the nearest `<t>` site; blank = not reachable by road within 600 minutes |
| `site_<t>` | Id of that nearest site |

## `data/processed/sites.csv` (one row per site per care type)

`service_type` (care type code), `site_id`, `name`, `address`, `city`, `state`, `zip`, `lat`, `lon`, `geo_method` (how the point was found: `census_geocoder_exact`, `cms_birthing_friendly_geocode`, `census_geocoder_nonexact`, `findtreatment_coordinates`, `hrsa_coordinates`, `zip_interior_point`, or unplaced), `detail` (hospital type and labor and delivery status; clinician count; facility type and setting), `census_vs_cms_km` (hospitals: distance between the Census and CMS geocodes where both exist).

## Other files

- `cms_hospital_ld_status.csv`: every CMS hospital in the 50 states and DC with its SM_7 answer, whether perinatal care measures were reported, and the resulting labor and delivery status.
- `validation_osrm_sample.csv`: the 450 OSRM check trips (origin, site, this project's minutes, OSRM minutes and km).
- `validation_summary.json`, `route_stats.json`, `origins_stats.json`: numbers quoted in the QA report and paper.
- `qa_report.txt`, `qa_hospital_geocode_differences.csv`: quality checks (read first).
