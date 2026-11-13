# Talk track

*Plain-language summary: a 60-second explanation you can say out loud, a two-sentence version, and three questions people ask, with honest answers. The numbers are the v0.1.0 numbers; recheck them against `report/stats.json` after verification.*

## 60 seconds

"In my Nevada mapping work I kept seeing counties with no obstetric or perinatal behavioral health services, and the real question families face is how far they have to drive. So I measured it for the whole country. I took the open OpenStreetMap road network, the Census Bureau's neighborhood population centers, and the number of women aged 15 to 44 in each neighborhood, and computed the drive to the nearest hospital that delivers babies, the nearest substance use treatment program for pregnant and postpartum women, and the nearest community health center.

Nationally, most women are within half an hour of a delivering hospital. But in frontier counties about a third of women are more than an hour away, and more than half are more than an hour from a perinatal treatment program. 108 rural and frontier counties, most of them very small frontier counties, have most women more than an hour from all three kinds of care. I checked the routing against OSRM, a widely used open-source routing engine running on the same roads, and they agree closely. Everything, the data, the code, and the method notes, is free on GitHub and Zenodo with a DOI, so a state agency can use it or rerun it with its own facility list."

## Two sentences

"I built an open national measure of how far women of childbearing age must drive to delivering hospitals, perinatal substance use treatment, and health centers, for every U.S. county. It shows which rural and frontier counties are cut off from perinatal behavioral health care even when services exist somewhere in the region."

## Three likely questions

**"Are these real drive times?"** They are drive times with no traffic, on the open road map, at standard speeds. On 450 test trips they matched the open-source OSRM routing engine on the same roads closely (median ratio 0.99), which confirms the routing arithmetic, and the national average to a delivering hospital, 14 minutes, matches a published study that used commercial maps. Rush hour and winter make real trips longer.

**"Why not just count facilities per county?"** Because women cross county lines. Some counties with no program are 20 minutes from one next door, and some counties with a program still leave most women more than half an hour away. Drive time answers the question a family actually faces.

**"What's missing?"** Medicare's list under-reports small rural hospitals that deliver babies, so I report a range. The perinatal treatment flag covers substance use programs only, because no open national list identifies perinatal mental health programs. And for Alaska villages, islands without a car connection, and ferry towns in Southeast Alaska, drive time isn't the right measure at all; those women are reported separately.
