# Start Here: Rural and Frontier Perinatal Care Access Layer

*Read this first. It explains Project 2 in plain language. Unfamiliar words are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

A free table, with one row for every U.S. county, showing how many women of childbearing age live more than a 30-minute or 60-minute drive from the nearest hospital that delivers babies, the nearest treatment program that serves pregnant or postpartum women, and the nearest community health center.

## Why it matters

Your Nevada mapping showed that seven counties had no OB/GYN providers and more than half lacked dedicated perinatal behavioral health services. Counting services inside county lines misses the real question a family faces: how far do I have to drive? A county can have no facility and still be 20 minutes from one next door. Another county can have a facility and still leave most of its women two hours away. Drive time answers the question directly, for every county, using the same method everywhere.

Think of it like a weather map, but for how long the drive to care is.

## Where the information comes from

All sources are free and public.

| Source | In plain terms | What one row looks like |
|---|---|---|
| OpenStreetMap | The free, volunteer-built map of every road in the country | One road segment: its type (highway, local street) and its shape |
| Census population-weighted block group centers | For each small neighborhood (a "block group", about 600 to 3,000 people), the point where its residents are centered | One neighborhood: an ID and a latitude and longitude |
| Census American Community Survey | How many women aged 15 to 44 live in each block group | One neighborhood: number of women 15 to 44 |
| CMS hospital maternal health data | Medicare's list of hospitals, with whether each delivers babies | One hospital: name, address, "provides labor and delivery: yes / no" |
| Your Project 1 panel (Zenodo DOI 10.5281/zenodo.24025395) | The treatment listings and health center sites you already verified | One facility: name, location, "serves pregnant/postpartum women: yes / no" |
| USDA rural codes (through Project 1) | Which counties are metro, rural, or frontier | One county: its rural code |

## What you will have at the end

- [ ] **A public project page** on GitHub with the code and the county table
- [ ] **A permanent citation number (DOI)** from Zenodo for the drive-time measures, with routing method notes (your May 2027 target)
- [ ] **A short paper** describing the measures, ready for a preprint server
- [ ] **The data the July 2027 interactive map will draw on** (need and capacity from Project 1, travel time from Project 2)

## How it connects to your work

It is the travel piece of the same national picture. Project 1 counts need and services in each county. Project 2 measures how far women actually are from those services, and reports rural and frontier counties separately.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Answer five setup questions (defaults offered) | Now | 10 min |
| Check the results using the checklist | When the draft is ready | 1 to 2 hours |
| Approve publishing | After checking | 5 min |
| Publish on GitHub and Zenodo, submit the preprint, using the guide | After approving | 30 min |

Your ORCID, GitHub, and Zenodo accounts from Project 1 are all you need.

## The steps ahead

1. **Data collected.** Roads, neighborhoods, population, and care sites downloaded, each with its source recorded.
2. **Road network built and drive times computed.** Every neighborhood gets a drive time to each type of care.
3. **County summaries and quality checks,** including a check of a sample of drive times against an outside routing service.
4. **First map and figures.**
5. **Draft paper and documents.** Every number comes straight from the data.
6. **Ready for your check.** You verify, then we publish.

*You are here: released. v0.1.0 is on GitHub and Zenodo (DOI 10.5281/zenodo.24206837). Next: the preprint (docs/PUBLISH_GUIDE.md).*
