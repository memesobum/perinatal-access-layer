#!/usr/bin/env python3
"""paper/figures.py: the preprint's figures, in a Matplotlib/Seaborn scientific style.

Plain-language summary: draws every figure in the detailed preprint from the released tables, using the
same fonts as the paper. Output: paper/figures/*.pdf (vector, for the paper) and *.png (previews).
"""
import json
import os

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
P = os.path.join(R, "data", "processed")
RAW = os.path.join(R, "data", "raw")
F = os.path.join(H, "figures")
os.makedirs(F, exist_ok=True)

for f in ["texgyrepagella-regular.otf", "texgyrepagella-bold.otf", "texgyrepagella-italic.otf"]:
    p = f"/usr/share/texmf/fonts/opentype/public/tex-gyre/{f}"
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
sns.set_theme(context="paper", style="ticks", font="TeX Gyre Pagella", font_scale=1.0,
              rc={"axes.linewidth": 0.8, "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True,
                  "ytick.right": True, "legend.frameon": True, "legend.framealpha": 0.9, "legend.edgecolor": "0.6",
                  "mathtext.fontset": "stix", "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 7.5,
                  "xtick.labelsize": 8, "ytick.labelsize": 8, "savefig.dpi": 300, "pdf.fonttype": 42})
PAL = sns.color_palette("colorblind")
RC = {"Metro": PAL[0], "Rural": PAL[1], "Frontier": PAL[2]}
TC = {"ob_hosp": PAL[0], "ppw_bh": PAL[3], "hc": PAL[2], "ob_hosp_upper": PAL[9], "ob_clin": PAL[4], "mh_any": PAL[7]}
LAB = {"ob_hosp": "Delivering hospital", "ob_hosp_upper": "Delivering hospital (upper bound)",
       "ob_clin": "Obstetric clinician ZIP", "ppw_bh": "Perinatal SUD treatment", "mh_any": "Mental health (any)",
       "hc": "Health center"}
ONE, TWO = 3.4, 7.0   # column widths, inches

o = pd.read_csv(os.path.join(P, "bg_drive_times.csv"), dtype={"geoid": str, "fips": str})
c = pd.read_csv(os.path.join(P, "access_county.csv"), dtype={"fips": str})
o = o.merge(c[["fips", "state", "rurality_class"]], on="fips", how="left")
o = o[o.women_15_44 > 0]
S = json.load(open(os.path.join(H, "paper_stats.json")))
CLASS = {"metro": "Metro", "rural": "Rural", "frontier": "Frontier"}


def save(fig, name):
    fig.savefig(os.path.join(F, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(F, name + ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)


# ---------------- maps ----------------
def load_geo():
    from shapely.affinity import scale, translate
    g = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")
    st = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_state_500k.zip')}")
    out = []
    for d in (g, st):
        d = d[~d.STATEFP.isin(["60", "66", "69", "72", "78"])].copy()
        d.loc[d.STATEFP == "02", "geometry"] = d.loc[d.STATEFP == "02"].geometry.clip_by_rect(-180, 50, -129, 72)
        d = d.to_crs(5070)

        def place(mask, k, x0, y0):
            geo = d.loc[mask].geometry
            mx, my, _, _ = geo.total_bounds
            d.loc[mask, "geometry"] = geo.apply(lambda x: translate(scale(x, k, k, origin=(mx, my)), x0 - mx, y0 - my))
        place(d.STATEFP == "02", 0.35, -2.55e6, -0.35e6)
        place(d.STATEFP == "15", 1.0, -1.45e6, -0.20e6)
        out.append(d)
    return out


BINS = [0, .10, .25, .50, .75, 1.0001]
BL = ["<10%", "10–24%", "25–49%", "50–74%", "≥75%"]
CM = ListedColormap(sns.color_palette("rocket_r", 5))


def draw_map(ax, g, st, col, title):
    d = g.merge(c[["fips", col, "women_15_44"]], left_on="GEOID", right_on="fips", how="left")
    nod = d[d[col].isna() | (d.women_15_44 <= 0)]
    nod.plot(ax=ax, color="0.85", linewidth=0, rasterized=True)
    d.drop(nod.index).plot(ax=ax, column=col, cmap=CM, norm=BoundaryNorm(BINS, 5), linewidth=0.03, edgecolor="white",
                           rasterized=True)
    st.boundary.plot(ax=ax, linewidth=0.35, color="white", rasterized=True)
    st.boundary.plot(ax=ax, linewidth=0.15, color="0.35", rasterized=True)
    ax.set_axis_off()
    ax.set_title(title, fontsize=9)


def maps():
    g, st = load_geo()
    handles = [Patch(facecolor=CM(i), label=BL[i]) for i in range(5)] + [Patch(facecolor="0.85", label="no women 15–44")]
    for name, pair in [("fig_map_ob_ppw", [("ob_hosp_share_gt60", "(a) Delivering hospital"),
                                           ("ppw_bh_share_gt60", "(b) Perinatal SUD treatment facility")]),
                       ("fig_map_hc_upper", [("hc_share_gt60", "(a) Health center site"),
                                             ("ob_hosp_upper_share_gt60", "(b) Delivering hospital, upper-bound list")])]:
        fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.75))
        for ax, (col, title) in zip(axs, pair):
            draw_map(ax, g, st, col, title)
        fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, fontsize=7.5,
                   title="Share of county's women aged 15–44 more than 60 minutes away", title_fontsize=8,
                   bbox_to_anchor=(0.5, -0.06))
        fig.subplots_adjust(wspace=0.02)
        save(fig, name)


# ---------------- coverage curves ----------------
def coverage():
    fig, axs = plt.subplots(1, 3, figsize=(TWO, 2.35), sharey=True)
    grid = np.arange(0, 181, 1)
    for ax, (t, lab) in zip(axs, [("ob_hosp", "(a) Delivering hospital"), ("ppw_bh", "(b) Perinatal SUD treatment"),
                                  ("hc", "(c) Health center")]):
        for cls, name in CLASS.items():
            d = o[o.rurality_class == cls]
            x = d[f"min_{t}"].fillna(np.inf).values
            w = d.women_15_44.values
            y = [w[x <= g_].sum() / w.sum() * 100 for g_ in grid]
            ax.plot(grid, y, color=RC[name], lw=1.4, label=name)
        for th in (30, 60):
            ax.axvline(th, color="0.5", lw=0.6, ls="--", zorder=0)
        ax.set_xlim(0, 180)
        ax.set_ylim(0, 100)
        ax.set_xticks([0, 30, 60, 90, 120, 150, 180])
        ax.set_xlabel("Drive time (minutes)")
        ax.set_title(lab)
    axs[0].set_ylabel("Women 15–44 within $t$ minutes (%)")
    axs[0].legend(loc="lower right")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig_coverage")


# ---------------- grouped bars, all six types ----------------
def bars():
    rows = []
    for t in ["ob_hosp", "ob_hosp_upper", "ob_clin", "ppw_bh", "mh_any", "hc"]:
        for g in ["Metro", "Rural", "Frontier"]:
            k = {"Metro": "Metro", "Rural": "Rural (nonmetro, not frontier)", "Frontier": "Frontier"}[g]
            for th in (30, 60):
                rows.append({"type": LAB[t], "group": g, "th": th, "pct": 100 * S["rurality"][k][f"{t}_share_gt{th}"]})
    d = pd.DataFrame(rows)
    fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.9), sharey=True)
    for ax, th in zip(axs, (30, 60)):
        sns.barplot(data=d[d.th == th], y="type", x="pct", hue="group", palette=RC, ax=ax, orient="h",
                    edgecolor="white", linewidth=0.5)
        ax.set_xlabel(f"Women 15–44 beyond {th} min (%)")
        ax.set_ylabel("")
        ax.set_xlim(0, 100 if th == 30 else 70)
        ax.set_title(f"({'a' if th == 30 else 'b'}) Beyond {th} minutes")
        if th == 60:
            ax.get_legend().remove()
        else:
            ax.legend(title="", loc="lower right")
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.1f", fontsize=6, padding=1.5)
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig_bars")


# ---------------- county distribution ----------------
def county_dist():
    """Stacked shares of counties by how many of their women live more than 60 minutes away."""
    d = c[c.women_15_44 > 0].copy()
    d["Class"] = d.rurality_class.map(CLASS)
    bins = [-0.001, 0.0999, 0.4999, 0.9989, 1.001]
    labs = ["<10%", "10–49%", "50–99%", "100%"]
    cols = sns.color_palette("rocket_r", 4)
    rows = []
    for t in ["ob_hosp", "ppw_bh", "hc"]:
        for g in ["Metro", "Rural", "Frontier"]:
            x = pd.cut(d.loc[d.Class == g, f"{t}_share_gt60"], bins, labels=labs).value_counts(normalize=True)
            rows.append({"label": f"{LAB[t]}\n{g}" if g == "Metro" else g, "t": t, "g": g,
                         **{k: 100 * x.get(k, 0) for k in labs}})
    r = pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(ONE, 3.2))
    left = np.zeros(len(r))
    gap = np.array([i // 3 * 1.1 for i in range(len(r))])
    y = np.arange(len(r)) + gap
    for k, col in zip(labs, cols):
        ax.barh(y, r[k], left=left, color=col, edgecolor="white", linewidth=0.5, height=0.85, label=k)
        left += r[k].values
    ax.set_yticks(y, [f"{g}" for g in r.g])
    for i, t in enumerate(["hc", "ppw_bh", "ob_hosp"]):
        ax.text(0, y[i * 3 + 2] + 0.55, LAB[t], ha="left", va="bottom", fontsize=7.5, fontweight="bold",
                transform=ax.transData)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, y.max() + 1.6)
    ax.set_xlabel("Share of counties (%)")
    ax.legend(title="Women >60 min", ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=6.5,
              title_fontsize=7, frameon=False, handlelength=1.2, columnspacing=0.8)
    ax.tick_params(axis="y", labelsize=7, right=False)
    save(fig, "fig_county_dist")


# ---------------- sensitivity: hospital list ----------------
def sensitivity():
    rows = []
    for g in ["All", "Metro", "Rural", "Frontier"]:
        x = S["sens"][g]
        for lst, a, b in [("Confirmed (CMS)", "conf30", "conf60"), ("Upper bound", "up30", "up60")]:
            rows.append({"group": g, "list": lst, "gt30": 100 * x[a], "gt60": 100 * x[b]})
    d = pd.DataFrame(rows)
    fig, axs = plt.subplots(1, 2, figsize=(ONE * 1.25, 2.3), sharey=True)
    for ax, col, lab in zip(axs, ["gt30", "gt60"], ["(a) >30 minutes", "(b) >60 minutes"]):
        sns.barplot(data=d, x="group", y=col, hue="list", palette=[PAL[0], PAL[9]], ax=ax, edgecolor="white", linewidth=0.5)
        ax.set_title(lab)
        ax.set_xlabel("")
        ax.set_ylabel("Women 15–44 beyond threshold (%)" if col == "gt30" else "")
        ax.tick_params(axis="x", labelsize=7)
        if col == "gt60":
            ax.get_legend().remove()
        else:
            ax.legend(title="", fontsize=6.5, loc="upper left")
    fig.tight_layout(w_pad=0.5)
    save(fig, "fig_sensitivity")


# ---------------- validation ----------------
def validation():
    v = pd.read_csv(os.path.join(P, "validation_osrm_sample.csv")).dropna(subset=["min_osrm"])
    v["Class"] = v.rurality_class.map(CLASS)
    fig, axs = plt.subplots(1, 2, figsize=(TWO, 2.8))
    ax = axs[0]
    sns.scatterplot(data=v, x="min_osrm", y="min_project", hue="Class", palette=RC, s=10, ax=ax, edgecolor="none",
                    hue_order=["Metro", "Rural", "Frontier"])
    m = max(v.min_osrm.max(), v.min_project.max()) * 1.05
    ax.plot([0.3, m], [0.3, m], color="0.3", lw=0.8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.3, m)
    ax.set_ylim(0.3, m)
    ax.set_xlabel("OSRM public server (minutes)")
    ax.set_ylabel("This study (minutes)")
    ax.set_title("(a) Same origin–site pairs")
    ax.legend(title="", loc="upper left")
    ax = axs[1]
    v["mean"] = (v.min_project + v.min_osrm) / 2
    v["diff"] = v.min_project - v.min_osrm
    sns.scatterplot(data=v, x="mean", y="diff", hue="Class", palette=RC, s=10, ax=ax, edgecolor="none", legend=False,
                    hue_order=["Metro", "Rural", "Frontier"])
    md, lo, hi = S["val_extra"]["mean_diff"], S["val_extra"]["loa_low"], S["val_extra"]["loa_high"]
    for y, ls in [(md, "-"), (lo, "--"), (hi, "--")]:
        ax.axhline(y, color="0.3", lw=0.8, ls=ls)
    ax.text(0.98, 0.97, f"limits of agreement: {lo:.1f} to +{hi:.1f} min", ha="right", va="top",
            fontsize=7, transform=ax.transAxes, bbox=dict(facecolor="white", edgecolor="0.7", lw=0.5, pad=2))
    ax.set_ylim(-35, 35)
    ax.set_xlabel("Mean of the two times (minutes)")
    ax.set_ylabel("This study − OSRM (minutes)")
    ax.set_title("(b) Bland–Altman agreement")
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig_validation")


# ---------------- states ----------------
def states():
    rows = []
    g = o.groupby("state")
    for st_, d in g:
        w = d.women_15_44
        rows.append({"state": st_, **{t: 100 * w[d[f"min_{t}"].isna() | (d[f"min_{t}"] > 60)].sum() / w.sum()
                                      for t in ["ob_hosp", "ppw_bh", "hc"]}})
    d = pd.DataFrame(rows).sort_values("ppw_bh", ascending=False).head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(ONE, 3.6))
    y = np.arange(len(d))
    ax.hlines(y, 0, d[["ob_hosp", "ppw_bh", "hc"]].max(axis=1), color="0.85", lw=0.8, zorder=0)
    for t, mk in [("ppw_bh", "o"), ("ob_hosp", "s"), ("hc", "^")]:
        ax.scatter(d[t], y, s=16, marker=mk, color=TC[t], label=LAB[t], zorder=3, edgecolor="white", linewidth=0.4)
    ax.set_yticks(y, d.state)
    ax.set_xlabel("Women 15–44 more than 60 minutes away (%)")
    ax.set_xlim(0, max(30, d[["ob_hosp", "ppw_bh", "hc"]].values.max() * 1.1))
    ax.legend(loc="lower right", fontsize=6.5)
    ax.tick_params(axis="y", labelsize=7)
    save(fig, "fig_states")


# ---------------- county medians: hospital vs perinatal treatment ----------------
def joint():
    d = c[(c.women_15_44 > 0) & c.ob_hosp_median_min.notna() & c.ppw_bh_median_min.notna()].copy()
    d["Class"] = d.rurality_class.map(CLASS)
    fig, ax = plt.subplots(figsize=(ONE, 3.0))
    sns.scatterplot(data=d, x="ob_hosp_median_min", y="ppw_bh_median_min", hue="Class", palette=RC, s=7, alpha=0.7,
                    edgecolor="none", ax=ax, hue_order=["Metro", "Rural", "Frontier"])
    ax.set_xscale("log")
    ax.set_yscale("log")
    lim = (0.8, 400)
    ax.set_xlim(*lim)
    ax.set_ylim(*lim)
    ax.plot(lim, lim, color="0.3", lw=0.7)
    for th in (30, 60):
        ax.axvline(th, color="0.6", lw=0.5, ls="--")
        ax.axhline(th, color="0.6", lw=0.5, ls="--")
    ax.set_xlabel("Median drive to delivering hospital (min)")
    ax.set_ylabel("Median drive to perinatal SUD treatment (min)")
    ax.legend(title="", loc="upper left", markerscale=1.5)
    save(fig, "fig_joint")


if __name__ == "__main__":
    coverage()
    bars()
    county_dist()
    sensitivity()
    validation()
    states()
    joint()
    maps()
    print("figures:", sorted(f for f in os.listdir(F) if f.endswith(".pdf")))
