#!/usr/bin/env python3
"""09_figures.py: draw the maps and charts, and write report/stats.json.

Plain-language summary: makes the county maps (share of women aged 15 to 44 living
more than 60 minutes from each type of care), a chart comparing metro, rural, and
frontier counties, and the stats file that every number in the paper and README is
copied from. Figures carry a DRAFT tag until the author verifies the release.
"""

import json
import os
import sys

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from config import DRAFT, PROC, RAW, REPORT, SERVICE_TYPES, VERSION  # noqa: E402

FIG = os.path.join(REPORT, "figures")
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SEQ = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]   # reference sequential blue, steps 100-700
BINS = [0, 0.10, 0.25, 0.50, 0.75, 1.0001]
BIN_LABELS = ["under 10%", "10 to 24%", "25 to 49%", "50 to 74%", "75% or more"]
NODATA = "#d9d8d4"
CAT = {"Metro": "#2a78d6", "Rural": "#eb6834", "Frontier": "#1baf7a"}
TITLES = {"ob_hosp": "a hospital that delivers babies", "ppw_bh": "a treatment facility serving pregnant or postpartum women",
          "hc": "a community health center"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": GRID})


def stamp(fig):
    if DRAFT:
        fig.text(0.99, 0.01, "DRAFT, not yet verified", ha="right", va="bottom", fontsize=8, color="#d03b3b")


def shift_ak_hi(g):
    """Move Alaska and Hawaii into insets at the lower left of the lower 48 (Albers equal area)."""
    from shapely.affinity import scale, translate
    g = g.to_crs(5070).copy()

    def place(mask, factor, x0, y0):
        if not mask.any():
            return
        geo = g.loc[mask].geometry
        minx, miny, _, _ = geo.total_bounds
        geo = geo.apply(lambda x: scale(x, factor, factor, origin=(minx, miny)))
        g.loc[mask, "geometry"] = geo.apply(lambda x: translate(x, x0 - minx, y0 - miny))

    place(g.STATEFP == "02", 0.35, -2.55e6, -0.35e6)
    place(g.STATEFP == "15", 1.0, -1.45e6, -0.20e6)
    return g


def load_geo():
    g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")
    g = g[~g.STATEFP.isin(["60", "66", "69", "72", "78"])]
    st = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_state_500k.zip')}")
    st = st[~st.STATEFP.isin(["60", "66", "69", "72", "78"])]
    g = g.copy()
    g.loc[g.STATEFP == "02", "geometry"] = g.loc[g.STATEFP == "02"].geometry.clip_by_rect(-180, 50, -129, 72)
    st.loc[st.STATEFP == "02", "geometry"] = st.loc[st.STATEFP == "02"].geometry.clip_by_rect(-180, 50, -129, 72)
    return shift_ak_hi(g), shift_ak_hi(st)


def county_map(g, st, c, t, path):
    d = g.merge(c[["fips", f"{t}_share_gt60", "women_15_44"]], left_on="GEOID", right_on="fips", how="left")
    fig, ax = plt.subplots(figsize=(10, 6.4), facecolor=SURF)
    ax.set_facecolor(SURF)
    nod = d[d[f"{t}_share_gt60"].isna() | (d.women_15_44 <= 0)]
    nod.plot(ax=ax, color=NODATA, linewidth=0)
    ok = d.drop(nod.index)
    ok.plot(ax=ax, column=f"{t}_share_gt60", cmap=ListedColormap(SEQ), norm=BoundaryNorm(BINS, 5),
            linewidth=0.05, edgecolor=SURF)
    st.boundary.plot(ax=ax, linewidth=0.5, color=SURF)
    ax.set_axis_off()
    ax.set_title(f"Share of women aged 15 to 44 living more than 60 minutes' drive from\n{TITLES[t]}",
                 loc="left", fontsize=12, color=INK)
    handles = [Patch(facecolor=col, label=lab) for col, lab in zip(SEQ, BIN_LABELS)] + [
        Patch(facecolor=NODATA, label="no women 15 to 44")]
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1.0, -0.02), frameon=False, fontsize=8, ncol=2,
              title="Share of county's women beyond 60 minutes", title_fontsize=8)
    fig.text(0.01, 0.005, f"Drive times on OpenStreetMap roads from 2020 population-weighted block group centers; "
             f"women 15-44 from ACS 2020-2024. Perinatal Care Access Layer v{VERSION}.",
             fontsize=7, color=INK2)
    stamp(fig)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def rurality_chart(rt, path, th=60):
    groups = [("Metro", "Metro"), ("Rural", "Rural (nonmetro, not frontier)"), ("Frontier", "Frontier")]
    types = ["ob_hosp", "ppw_bh", "hc"]
    labels = ["Delivering hospital", "Perinatal treatment\nfacility (pregnant/postpartum)", "Health center"]
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=SURF)
    ax.set_facecolor(SURF)
    x = np.arange(len(types))
    bw = 0.26
    for i, (short, g) in enumerate(groups):
        r = rt[rt.group == g].iloc[0]
        vals = [r[f"{t}_share_gt{th}"] * 100 for t in types]
        bars = ax.bar(x + (i - 1) * (bw + 0.01), vals, bw, color=CAT[short], label=short, zorder=3)
        for b_, v_ in zip(bars, vals):
            ax.text(b_.get_x() + b_.get_width() / 2, v_ + 1, f"{v_:.1f}%" if v_ < 10 else f"{v_:.0f}%", ha="center", va="bottom", fontsize=8,
                    color=INK)
    ax.set_xticks(x, labels)
    ax.set_ylabel(f"Women 15-44 living more than {th} minutes away (%)")
    ax.yaxis.grid(True, color=GRID, linewidth=0.6, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.set_title(f"Women living more than {th} minutes from care, by county type", loc="left", fontsize=11)
    stamp(fig)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def validation_chart(path):
    v = pd.read_csv(os.path.join(PROC, "validation_osrm_sample.csv")).dropna(subset=["min_osrm"])
    fig, ax = plt.subplots(figsize=(5, 5), facecolor=SURF)
    ax.set_facecolor(SURF)
    for rc, col in [("metro", CAT["Metro"]), ("rural", CAT["Rural"]), ("frontier", CAT["Frontier"])]:
        d = v[v.rurality_class == rc]
        ax.scatter(d.min_osrm, d.min_project, s=14, color=col, label=rc.capitalize(), edgecolor=SURF,
                   linewidth=0.6, zorder=3)
    m = max(v.min_osrm.max(), v.min_project.max()) * 1.05
    ax.plot([0, m], [0, m], color=INK2, linewidth=1, zorder=2)
    ax.text(m * 0.62, m * 0.66, "same time", rotation=45, color=INK2, fontsize=8)
    for th in (30, 60):
        ax.axhline(th, color=GRID, linewidth=0.8, zorder=1)
        ax.axvline(th, color=GRID, linewidth=0.8, zorder=1)
    ax.set_xlim(0, m)
    ax.set_ylim(0, m)
    ax.set_xlabel("OSRM public routing engine (minutes)")
    ax.set_ylabel("This project (minutes)")
    ax.set_title("Same trips, two routing methods", loc="left", fontsize=11)
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    stamp(fig)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)


def stats(c, rt):
    S = {"version": VERSION, "draft": DRAFT}
    S["route"] = json.load(open(os.path.join(PROC, "route_stats.json")))
    S["origins"] = json.load(open(os.path.join(PROC, "origins_stats.json")))
    S["validation"] = json.load(open(os.path.join(PROC, "validation_summary.json")))
    s = pd.read_csv(os.path.join(PROC, "sites.csv"))
    S["sites"] = s.service_type.value_counts().to_dict()
    S["counties"] = int(len(c))
    S["rurality"] = rt.set_index("group").to_dict(orient="index")
    for t in SERVICE_TYPES:
        for th in (30, 60):
            S[f"counties_majority_gt{th}_{t}"] = int((c[f"{t}_share_gt{th}"] > 0.5).sum())
            S[f"counties_all_gt{th}_{t}"] = int((c[f"{t}_share_gt{th}"] >= 0.999).sum())
    f = pd.read_csv(os.path.join(RAW, "p1_capacity_facilities.csv"), dtype=str)
    c = c.copy()
    c["ppw_in_county"] = c.fips.map(f[f.serves_ppw == "1"].groupby("fips").size()).fillna(0)
    rf = c[(c.rural == 1) | (c.frontier == 1)]
    S["rf_ppw_none_in_county"] = int((rf.ppw_in_county == 0).sum())
    S["rf_ppw_none_in_county_but_most_within30"] = int(((rf.ppw_in_county == 0) & (rf.ppw_bh_share_gt30 <= 0.5)).sum())
    S["rf_ppw_in_county_but_most_beyond30"] = int(((rf.ppw_in_county > 0) & (rf.ppw_bh_share_gt30 > 0.5)).sum())
    for t in SERVICE_TYPES:
        S[f"rf_majority_gt60_{t}"] = int((rf[f"{t}_share_gt60"] > 0.5).sum())
        S[f"rf_women_gt60_{t}"] = float(rf[f"{t}_women_gt60"].sum())
    S["counties_majority_gt60_all_three"] = int(((c.ppw_bh_share_gt60 > .5) & (c.ob_hosp_share_gt60 > .5)
                                                & (c.hc_share_gt60 > .5)).sum())
    a3 = c[(c.ppw_bh_share_gt60 > .5) & (c.ob_hosp_share_gt60 > .5) & (c.hc_share_gt60 > .5)]
    S["all_three_frontier"] = int((a3.frontier == 1).sum())
    S["all_three_small_women"] = int((a3.women_15_44 < 500).sum())
    S["all_three_women"] = float(a3.women_15_44.sum())
    nv = c[(c.state == "NV") & (c.ob_hosp_share_gt60 >= 0.999)].sort_values("county_name")
    S["nv_all_beyond60_ob"] = [x.replace(" County", "") for x in nv.county_name]
    S["rf_counties_majority_gt60_all_three"] = int(((rf.ppw_bh_share_gt60 > .5) & (rf.ob_hosp_share_gt60 > .5)
                                                   & (rf.hc_share_gt60 > .5)).sum())
    S["rural_frontier_counties"] = int(len(rf))
    S["rf_majority_gt60_ppw_but_lt_half_ob"] = int(((rf.ppw_bh_share_gt60 > 0.5) & (rf.ob_hosp_share_gt60 <= 0.5)).sum())
    S["published_benchmarks"] = {
        "rayburn_2012": {"citation": "Rayburn WF, Richards ME, Elwell EC. Drive times to hospitals with perinatal care "
                         "in the United States. Obstet Gynecol. 2012;119(3):611-616.",
                         "hospitals": 2606, "data_year": "2007 AHA survey; 2010 Census; women 18-39",
                         "share_within_30": 0.875, "share_within_60": 0.973},
        "fontenot_2024": {"citation": "Fontenot J, Brigance C, Lucas R, Stoneburner A. Navigating geographical disparities: "
                          "access to obstetric hospitals in maternity care deserts and across the United States. "
                          "BMC Pregnancy Childbirth. 2024;24:350. doi:10.1186/s12884-024-06535-7",
                          "mean_minutes_tract_level": 14.1}}
    S["this_project_ob_hosp_share_within_30"] = round(1 - rt.set_index("group").loc["All counties", "ob_hosp_share_gt30"], 4)
    S["this_project_ob_hosp_share_within_60"] = round(1 - rt.set_index("group").loc["All counties", "ob_hosp_share_gt60"], 4)
    o = pd.read_csv(os.path.join(PROC, "bg_drive_times.csv"), usecols=["women_15_44", "min_ob_hosp"])
    ok = o.min_ob_hosp.notna()
    S["this_project_ob_hosp_mean_min"] = round(float(np.average(o.min_ob_hosp[ok], weights=o.women_15_44[ok])), 1)
    with open(os.path.join(REPORT, "stats.json"), "w") as f:
        json.dump(S, f, indent=1, default=lambda x: int(x) if isinstance(x, np.integer) else float(x))
    return S


def main():
    os.makedirs(FIG, exist_ok=True)
    c = pd.read_csv(os.path.join(PROC, "access_county.csv"), dtype={"fips": str})
    rt = pd.read_csv(os.path.join(PROC, "access_by_rurality.csv"))
    g, st = load_geo()
    for i, t in enumerate(["ob_hosp", "ppw_bh", "hc"], 1):
        county_map(g, st, c, t, os.path.join(FIG, f"fig{i}_map_{t}_gt60.png"))
    rurality_chart(rt, os.path.join(FIG, "fig4_rurality_gt60.png"), 60)
    rurality_chart(rt, os.path.join(FIG, "fig5_rurality_gt30.png"), 30)
    validation_chart(os.path.join(FIG, "fig6_validation_osrm.png"))
    S = stats(c, rt)
    print(json.dumps({k: S[k] for k in S if k.startswith("this_project")}, indent=1))


if __name__ == "__main__":
    main()
