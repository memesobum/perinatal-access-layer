#!/usr/bin/env python3
"""paper/graphic_abstract.py: graphic abstract for preprints.org (PNG, 2400 x 1200 px). Numbers from the stats files."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("figs", os.path.join(H, "figures.py"))
figs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figs)
S0 = json.load(open(os.path.join(R, "report", "stats.json")))
S = json.load(open(os.path.join(H, "paper_stats.json")))
RT = S0["rurality"]
for f in ["texgyrepagella-regular.otf", "texgyrepagella-bold.otf"]:
    font_manager.fontManager.addfont(f"/usr/share/texmf/fonts/opentype/public/tex-gyre/{f}")
plt.rcParams["font.family"] = "TeX Gyre Pagella"
INK, INK2 = "#111111", "#4a4a4a"
CM = ListedColormap(sns.color_palette("rocket_r", 5))
BINS = [0, .10, .25, .50, .75, 1.0001]

fig = plt.figure(figsize=(12, 6), dpi=200, facecolor="white")
fig.text(0.03, 0.925, "How far to perinatal care?", fontsize=24, weight="bold", color=INK)
fig.text(0.03, 0.875, "Open drive-time measures for all 3,144 U.S. counties: delivering hospitals, "
         "perinatal substance use treatment, and health centers", fontsize=12.5, color=INK2)

ax = fig.add_axes([0.0, 0.11, 0.60, 0.66])
g, st = figs.load_geo()
d = g.merge(figs.c[["fips", "ppw_bh_share_gt60", "women_15_44"]], left_on="GEOID", right_on="fips", how="left")
nod = d[d.ppw_bh_share_gt60.isna() | (d.women_15_44 <= 0)]
nod.plot(ax=ax, color="0.85", linewidth=0)
d.drop(nod.index).plot(ax=ax, column="ppw_bh_share_gt60", cmap=CM, norm=BoundaryNorm(BINS, 5), linewidth=0.03,
                       edgecolor="white", rasterized=True)
st.boundary.plot(ax=ax, linewidth=0.3, color="0.35")
ax.set_axis_off()
ax.set_title("Share of each county's women aged 15–44 living more than 60 minutes\nfrom a substance use "
             "treatment program for pregnant or postpartum women", fontsize=11, color=INK, loc="left", x=0.05, pad=14)
ax.legend(handles=[Patch(fc=CM(i), label=l) for i, l in enumerate(["<10%", "10–24%", "25–49%", "50–74%", "≥75%"])],
          loc="lower center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.07), handlelength=1.3)

x0 = 0.62


def stat(y, big, small, col):
    fig.text(x0, y, big, fontsize=27, weight="bold", color=col)
    fig.text(x0, y - 0.05, small, fontsize=11.5, color=INK, va="top", linespacing=1.35)


stat(0.74, f"{100 * S0['this_project_ob_hosp_share_within_30']:.0f}%",
     "of women aged 15–44 live within 30 minutes of a\nhospital that delivers babies", "#1f5f9e")
fr = RT["Frontier"]
stat(0.53, f"{100 * fr['ob_hosp_share_gt60']:.0f}% · {100 * fr['ppw_bh_share_gt60']:.0f}% · {100 * fr['hc_share_gt60']:.0f}%",
     "of frontier women live more than an hour from a delivering\nhospital · perinatal SUD treatment · a health center",
     "#a3282c")
stat(0.31, f"{S['all3']['n']} counties",
     f"have most women more than an hour from all three\n({S['all3']['frontier']} of them frontier counties)", "#6b2a6b")
fig.text(0.03, 0.055, "Drive times on OpenStreetMap roads from 239,741 population-weighted Census block group "
         "centers; women 15–44 from ACS 2020–2024; sites from CMS, SAMHSA FindTreatment.gov, and HRSA.",
         fontsize=9, color=INK2)
fig.text(0.03, 0.025, f"Emesobum M.A. (2026). Rural and Frontier Perinatal Care Access Layer v{S0['version']}. "
         "doi:10.5281/zenodo.24206837 · Map data © OpenStreetMap contributors (ODbL).", fontsize=9, color=INK2)
out = os.path.join(H, "submission", "Graphic_Abstract.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=200, facecolor="white")
print(out)
