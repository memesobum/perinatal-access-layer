# Routing method notes

*Plain-language summary: this file explains, step by step, how every drive time in this release was computed, and why each choice was made. It is the "routing method notes" promised with the Zenodo release. Someone who wants to check or repeat the work should read it after the README. Every setting named here lives in `code/config.py` or at the top of `code/05_route.py`.*

## 1. The question each number answers

For a woman aged 15 to 44 living at the population center of her Census block group, how many minutes does it take to drive, with no traffic, to the nearest site of a given type of care? "Nearest" means quickest by road, not closest in a straight line. Routes may cross state lines.

## 2. Road network

**Source.** OpenStreetMap (OSM), the open, volunteer-built world map. The lower 48 states and DC come from four regional extracts published by openstreetmap.fr (data timestamp 13 November 2026), each checked against its published MD5 checksum. Alaska and Hawaii are not in those extracts. Their roads come from the Overture Maps Foundation transportation layer, release 2026-10-21.0. That layer is built from OSM roads, published under the same Open Database License (ODbL), and queried by bounding box.

**Roads kept.** The roads kept are these OSM `highway` classes: motorway, trunk, primary, secondary, tertiary (each with its ramps), unclassified, residential, and living_street. Ferries (`route=ferry`) are kept as well, as in the OSRM car profile. Roads tagged closed to cars (`access`, `motor_vehicle`, `motorcar`, or `vehicle` = no) are dropped. Ferries tagged closed to cars are also dropped.

Private roads are kept. Gated subdivisions, military bases, and campuses are reached by private roads, and the people who live behind a gate can drive out through it.

Service roads (driveways, parking aisles) and tracks are left out. Homes and sites reach the network through the connector rule in section 4.

**Speeds.** Speeds are free-flow car speeds by road class, using the defaults of the OSRM car profile (car.lua): motorway 90 km/h, trunk 85, primary 65, secondary 55, tertiary 40, unclassified and residential 25, and living street 10. Ramps are slower.

Where a road has a posted limit (`maxspeed`), the speed is 0.8 times the limit, as OSRM does. U.S. limits without a unit are read as miles per hour. That speed is capped at 1.5 times the class default.

Ferries use their tagged duration where present. Otherwise they use 5 km/h, the OSRM default, which deliberately makes long ferry crossings slow. Southeast Alaska's state ferries are in the data, but at that speed a crossing such as Haines to Juneau takes far longer than the 600-minute search limit (section 5). These towns therefore show as having no route within 600 minutes, not as having no ferry. One-way streets and roundabouts are respected.

**What is not modeled.** Traffic, time of day, weather, seasonal road closures, turn penalties, and traffic signals are not modeled. The times are therefore free-flow times. In the check against OSRM (section 6), they ran about 5% faster than OSRM in metro areas, where OSRM adds turn and signal penalties. Rural and frontier times showed almost no difference.

**Graph.** Each road is split into links at every junction, at its ends, and every 1 km along its length. Splitting every 1 km means a home beside a long rural highway joins the highway near the home, not at the next junction miles away.

Links carry minutes in each allowed direction. Where the regional files overlap at their borders, duplicate links are merged, keeping the fastest. The national network has about 24 million road points and 56 million one-way links. Mapped road lines total about 8.0 million km, plus about 15,000 km of ferry routes. That is more than the 6.7 million km of U.S. public roads, because each direction of a divided highway is a separate line and private roads are included. Exact counts are in `data/processed/qa_report.txt`.

## 3. Where people are

**Hospital locations.** Hospitals are placed in this order of preference:

1. Census Geocoder exact address match.
2. CMS's own geocode (birthing-friendly file).
3. Census non-exact match.
4. The Census place (town) interior point for the listed city.
5. The ZIP code's interior point.

The town step matters in Alaska. There, ZIP areas are huge, and Nome, Kotzebue, and Dillingham hospitals list addresses the geocoder cannot match.

**Origins.** The starting points are the Census Bureau's 2020 population-weighted block group centers (`CenPop2020_Mean_BG`). This is the same origin used by published drive-time studies, such as Rayburn et al. (2012) and the Illinois Department of Public Health study in *Preventing Chronic Disease* (2026).

**Weights.** Each block group is weighted by its number of women aged 15 to 44 in the ACS 2020-2024 5-year table B01001, which is the sum of the female age groups from 15-17 through 40-44.

**Connecticut.** The ACS uses Connecticut's nine planning regions, while the 2020 center file uses the eight old counties. Each Connecticut center point is placed in its planning region before matching.

## 4. Getting on and off the network (connectors)

Each block group center and each care site is joined to the nearest road point that meets three conditions:

1. The point is not on a freeway or ramp, because you cannot drive onto a freeway from the roadside.
2. The point lies in a **main road network**.
3. The point is within 25 km.

The straight-line distance to that point is converted to minutes as if driven at 25 km/h, after multiplying by 1.3 to allow for bends. The median connector is 0.08 km. Centers more than 25 km from any usable road are "not connected", and their women count as beyond every threshold.

**Main road networks.** A main road network is a piece of the network in which every point can drive to every other point (a "strongly connected" piece) and that meets one of two tests:

- It is very large, with 50,000 or more points.
- It received a care site. Sites are attached to the largest piece available nearby: first a very large piece within 2 km, then a piece with 1,000 or more points within 2 km (islands such as Oahu), then any piece with 50 or more points within 25 km (towns with no road to the outside, such as Bethel or Nome, Alaska).

This rule keeps neighborhoods from joining small closed-off fragments that lead nowhere. It still lets road-isolated towns reach their own clinic or hospital.

**Islands and shores with no car connection.** A neighborhood is treated as having no road route out when all three of these hold:

1. Its nearest main-network road is more than 2 km away.
2. Either the nearest road of any kind is a closed-off piece (three or more times closer), or there is no closer road at all.
3. The straight line to the main network crosses open water, judged against the Census Bureau's shoreline-clipped state boundaries with a 100 m allowance for bridges.

Without this rule, the 25 km connector would attach an island neighborhood to the mainland across the water. Examples are Kalaupapa (Kalawao County, Hawaii), Bald Head Island (North Carolina), Mackinac Island, the Maine islands, Fire Island, and Point Roberts, Washington, whose only road runs through Canada. On land, a closed-off piece usually means the map is missing an unpaved or service road. So a mainland neighborhood keeps its longer connector instead of being marked unreachable.

## 5. Shortest paths

For each care type, one shortest-path search (Dijkstra's method, from SciPy) runs on the reversed network from all sites at once. Each site enters through its own entry point, which carries the site's connector minutes. The search therefore gives, for every road point, the time to drive from that point to the nearest site, and which site that is.

A block group's drive time is the time from its road point plus its own connector minutes. Searches stop at 600 minutes. A block group whose road network holds no site of that type is "not reachable by road", for example an Alaska village with no road out. Its women count as beyond every threshold.

This calculation produces the same answer a routing engine such as OSRM would give on the same roads with the same speeds. The search is simply run directly, because a national OSRM server needs about 64 GB of memory.

## 6. Checks

- **Against OSRM.** 450 random trips (50 for each combination of delivering hospital, perinatal treatment facility, or health center with metro, rural, or frontier county) were sent to the public OSRM routing server (router.project-osrm.org), which runs the OSRM car profile on OSM. Agreement statistics are in `data/processed/validation_summary.json` and the QA report. Figure 6 plots every pair. OSRM uses the same OpenStreetMap roads and similar speeds, and it was asked to route to the site this project picked. So this check confirms the routing computation, not the road map itself or the choice of nearest site.
- **Against published studies.** The national share of women within 30 and 60 minutes of a delivering hospital is set beside Rayburn et al. (2012) and Fontenot et al. (2024) in `report/stats.json` and the paper. Those studies used different hospital lists, years, population groups (Rayburn: women 18 to 39, 2007 hospitals, 2010 population), and commercial road networks. They are reference points, not exact targets.
- **State check on site locations.** A care site whose coordinates fall in a different state from its address (for example, a program in Arlington, Oregon placed in Arlington, Texas) is moved to its ZIP code's center when that point is in the right state. Otherwise it is left unplaced. Every case is listed in `data/processed/qa_site_state_mismatches.csv`.
- **Logic checks.** Adding hospitals (upper-bound list) never lengthens a drive. No time is negative. No county has more women beyond 60 minutes than beyond 30. County totals add up to the block group totals.

## 7. County summaries

For each county and care type, the summaries are:

- women aged 15 to 44 beyond 30 and beyond 60 minutes, as counts and shares (women not reachable by road count as beyond)
- the women-weighted median minutes
- the women-weighted mean among women who can reach a site
- the longest block group time
- the site nearest to the most women in the county

Rural and frontier labels are taken unchanged from Project 1: rural means RUCC 2023 codes 4 to 9, and frontier means fewer than 6 people per square mile of land.

## 8. Reproducing

Run `bash run_all.sh`. You need about 30 GB of free disk and 8 GB of memory. On a 2-core machine, the build takes about an hour after the downloads. OSM changes daily, so a later run will differ slightly. The fingerprints of every file used for this release are in `data/raw/PROVENANCE.txt`, and the hospital geocodes are committed (`data/raw/census_geocoder_hospitals.csv`) so they do not drift.
