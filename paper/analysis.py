#!/usr/bin/env python3
"""paper/analysis.py: every statistic and table the detailed preprint quotes.

Plain-language summary: reads the released tables (data/processed/) and report/stats.json, computes the
extra summaries the long paper needs (drive-time distributions, state results, county cross-tabulations,
validation by stratum, the hospital-list sensitivity), and writes paper/paper_stats.json plus LaTeX tables
in paper/tables/. The paper reads its numbers only from these files (stats-file rule).
"""
import json
import os

import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
P = os.path.join(R, "data", "processed")
RAW = os.path.join(R, "data", "raw")
T = os.path.join(H, "tables")
os.makedirs(T, exist_ok=True)

S0 = json.load(open(os.path.join(R, "report", "stats.json")))
o = pd.read_csv(os.path.join(P, "bg_drive_times.csv"), dtype={"geoid": str, "fips": str})
c = pd.read_csv(os.path.join(P, "access_county.csv"), dtype={"fips": str})
s = pd.read_csv(os.path.join(P, "sites.csv"), dtype=str)
v = pd.read_csv(os.path.join(P, "validation_osrm_sample.csv"), dtype={"fips": str})
f1 = pd.read_csv(os.path.join(RAW, "p1_capacity_facilities.csv"), dtype=str)
o = o.merge(c[["fips", "state", "rurality_class", "rural", "frontier"]], on="fips", how="left")
TYPES = ["ob_hosp", "ob_hosp_upper", "ob_clin", "ppw_bh", "mh_any", "hc"]
HEAD = ["ob_hosp", "ppw_bh", "hc"]
LAB = {"ob_hosp": "Delivering hospital (confirmed)", "ob_hosp_upper": "Delivering hospital (upper bound)",
       "ob_clin": "Obstetric clinician ZIP", "ppw_bh": "Perinatal SUD treatment facility",
       "mh_any": "Mental health facility (any)", "hc": "Health center site"}
S = {}


def c_(x):
    return f"{int(round(x)):,}".replace(",", "{,}")


def p_(x, d=1):
    return f"{100 * x:.{d}f}"


def wq(x, w, q):
    x = np.where(np.isnan(x), np.inf, x)
    o_ = np.argsort(x)
    cw = np.cumsum(w[o_]) / w.sum()
    return x[o_][np.searchsorted(cw, q)]


# ---------- national distribution of drive times (women-weighted) ----------
grp = {"All": o.women_15_44 >= 0, "Metro": o.rurality_class == "metro",
       "Rural": o.rurality_class == "rural", "Frontier": o.rurality_class == "frontier"}
D = {}
for t in TYPES:
    for g, m in grp.items():
        d = o[m & (o.women_15_44 > 0)]
        x, w = d[f"min_{t}"].values.astype(float), d.women_15_44.values.astype(float)
        ok = ~np.isnan(x)
        D[f"{t}|{g}"] = {
            "median": float(wq(x, w, .5)), "p75": float(wq(x, w, .75)), "p90": float(wq(x, w, .90)),
            "p95": float(wq(x, w, .95)), "p99": float(wq(x, w, .99)),
            "mean_reachable": float(np.average(x[ok], weights=w[ok])),
            "within15": float(w[ok & (x <= 15)].sum() / w.sum()),
            "within30": float(w[ok & (x <= 30)].sum() / w.sum()),
            "within60": float(w[ok & (x <= 60)].sum() / w.sum()),
            "within90": float(w[ok & (x <= 90)].sum() / w.sum()),
            "within120": float(w[ok & (x <= 120)].sum() / w.sum()),
            "women_gt60": float(w[~ok | (x > 60)].sum()), "women_gt30": float(w[~ok | (x > 30)].sum()),
            "women": float(w.sum())}
S["dist"] = D

# ---------- sites and network ----------
S["sites"] = s.groupby("service_type").size().to_dict()
S["sites_geo"] = s.groupby(["service_type", "geo_method"]).size().unstack(fill_value=0).to_dict(orient="index")
cms = pd.read_csv(os.path.join(P, "cms_hospital_ld_status.csv"), dtype=str)
S["cms_status"] = cms.ld_status.value_counts().to_dict()
up = s[(s.service_type == "ob_hosp_upper") & s.detail.str.contains("not_reported")]
S["upper_added_by_type"] = up.detail.str.split(";").str[0].value_counts().to_dict()
S["route"] = S0["route"]
S["origins"] = S0["origins"]
S["validation"] = S0["validation"]
S["rurality"] = S0["rurality"]
S["n_counties"] = int(len(c))
S["n_class"] = c.rurality_class.value_counts().to_dict()
S["n_metro_frontier"] = int(((c.rural == 0) & (c.frontier == 1)).sum())
S["n_states"] = int(c.state.nunique())
S["women_total"] = float(o.women_15_44.sum())
S["women_share_rf"] = float(o[(o.rural == 1) | (o.frontier == 1)].women_15_44.sum() / o.women_15_44.sum())
S["status_counts"] = o.origin_status.value_counts().to_dict()
S["status_women"] = o.groupby("origin_status").women_15_44.sum().to_dict()
S["snap_q"] = {str(q): float(o.snap_km.quantile(q)) for q in [.5, .9, .99]}
S["state_mismatch_rows"] = int(len(pd.read_csv(os.path.join(P, "qa_site_state_mismatches.csv"))))
S["hosp_geocode_diff_gt2km"] = int(len(pd.read_csv(os.path.join(P, "qa_hospital_geocode_differences.csv"))))

# ---------- county-level: majority beyond, all-beyond, distribution ----------
K = {}
for t in TYPES:
    for th in (30, 60):
        for g, m in {"All": c.index == c.index, "Metro": c.rurality_class == "metro",
                     "Rural": c.rurality_class == "rural", "Frontier": c.rurality_class == "frontier"}.items():
            d = c[m & (c.women_15_44 > 0)]
            K[f"{t}|{th}|{g}"] = {"majority": int((d[f"{t}_share_gt{th}"] > .5).sum()),
                                  "all": int((d[f"{t}_share_gt{th}"] >= .999).sum()),
                                  "none": int((d[f"{t}_share_gt{th}"] <= 0.001).sum()), "n": int(len(d))}
S["county"] = K

# ---------- in-county presence vs drive time (2x2), perinatal SUD and delivering hospitals ----------
c["ppw_in"] = c.fips.map(f1[f1.serves_ppw == "1"].groupby("fips").size()).fillna(0) > 0
hosp = s[s.service_type == "ob_hosp"].copy()
# hospital county: from the block-group file's county of the nearest-site? use CMS county via site ZIP is lossy;
# instead assign by point-in-county below
import geopandas as gpd  # noqa: E402
cg = gpd.read_file(f"zip://{os.path.join(RAW, 'cb_2024_us_county_500k.zip')}")[["GEOID", "geometry"]].to_crs(4326)
hp = gpd.GeoDataFrame(hosp, geometry=gpd.points_from_xy(hosp.lon.astype(float), hosp.lat.astype(float)), crs=4326)
hj = gpd.sjoin(hp, cg, how="left", predicate="within")
c["ob_in"] = c.fips.isin(set(hj.GEOID.dropna()))
X = {}
for key, pres, share in [("ppw", "ppw_in", "ppw_bh_share_gt30"), ("ob", "ob_in", "ob_hosp_share_gt30")]:
    for g, m in {"RF": (c.rural == 1) | (c.frontier == 1), "All": c.index == c.index}.items():
        d = c[m & (c.women_15_44 > 0)]
        X[f"{key}|{g}"] = {
            "in_and_reach": int((d[pres] & (d[share] <= .5)).sum()),
            "in_but_far": int((d[pres] & (d[share] > .5)).sum()),
            "none_but_reach": int((~d[pres] & (d[share] <= .5)).sum()),
            "none_and_far": int((~d[pres] & (d[share] > .5)).sum())}
S["crosstab30"] = X

# ---------- all-three counties ----------
a3 = c[(c.ob_hosp_share_gt60 > .5) & (c.ppw_bh_share_gt60 > .5) & (c.hc_share_gt60 > .5)]
S["all3"] = {"n": int(len(a3)), "frontier": int((a3.frontier == 1).sum()), "small": int((a3.women_15_44 < 500).sum()),
             "women": float(a3.women_15_44.sum()), "states": a3.state.value_counts().head(8).to_dict(),
             "n_states": int(a3.state.nunique())}

# ---------- states ----------
st = o.groupby("state").apply(lambda d: pd.Series({
    "women": d.women_15_44.sum(),
    **{f"{t}_gt60": d.loc[d[f"min_{t}"].isna() | (d[f"min_{t}"] > 60), "women_15_44"].sum() / d.women_15_44.sum()
       for t in HEAD},
    **{f"{t}_gt30": d.loc[d[f"min_{t}"].isna() | (d[f"min_{t}"] > 30), "women_15_44"].sum() / d.women_15_44.sum()
       for t in HEAD}}), include_groups=False)
st = st.sort_values("ppw_bh_gt60", ascending=False)
S["state_top_ppw60"] = st.head(12).round(4).to_dict(orient="index")
S["state_count_ppw60_gt10"] = int((st.ppw_bh_gt60 > .10).sum())
S["state_count_ob60_gt5"] = int((st.ob_hosp_gt60 > .05).sum())
S["state_zero_ob60"] = int((st.ob_hosp_gt60 < .001).sum())

# ---------- sensitivity: confirmed vs upper bound ----------
S["sens"] = {g: {"conf60": S0["rurality"][k]["ob_hosp_share_gt60"], "up60": S0["rurality"][k]["ob_hosp_upper_share_gt60"],
                 "conf30": S0["rurality"][k]["ob_hosp_share_gt30"], "up30": S0["rurality"][k]["ob_hosp_upper_share_gt30"]}
             for g, k in [("All", "All counties"), ("Metro", "Metro"), ("Rural", "Rural (nonmetro, not frontier)"),
                          ("Frontier", "Frontier")]}
dd = c[c.women_15_44 > 0]
S["sens_counties_change60"] = int(((dd.ob_hosp_share_gt60 - dd.ob_hosp_upper_share_gt60) > .25).sum())
bg_d = (o.min_ob_hosp - o.min_ob_hosp_upper)
S["sens_bg_any_change"] = float(o.loc[(bg_d > 0.01) | (o.min_ob_hosp.isna() & o.min_ob_hosp_upper.notna()),
                                      "women_15_44"].sum())

# ---------- correlation between care types (county, women-weighted median minutes) ----------
cc = c[(c.women_15_44 > 0)][[f"{t}_median_min" for t in HEAD]].dropna()
S["spearman"] = {f"{a}|{b}": float(cc[f"{a}_median_min"].rank().corr(cc[f"{b}_median_min"].rank()))
                 for i, a in enumerate(HEAD) for b in HEAD[i + 1:]}

# ---------- validation by stratum ----------
v = v.dropna(subset=["min_osrm"]).copy()
v["diff"] = v.min_project - v.min_osrm
v["ratio"] = v.min_project / v.min_osrm.clip(lower=.5)
S["val_extra"] = {"loa_low": float(v["diff"].mean() - 1.96 * v["diff"].std()),
                  "loa_high": float(v["diff"].mean() + 1.96 * v["diff"].std()),
                  "mean_diff": float(v["diff"].mean()), "n": int(len(v)),
                  "p90_absdiff": float(v["diff"].abs().quantile(.9)),
                  "n_absdiff_gt10": int((v["diff"].abs() > 10).sum())}

# ---------- Nevada ----------
nv = c[c.state == "NV"].sort_values("county_name")
S["nv_all_beyond60_ob"] = [x.replace(" County", "") for x in nv[nv.ob_hosp_share_gt60 >= .999].county_name]
S["nv_all_beyond60_ppw"] = [x.replace(" County", "") for x in nv[nv.ppw_bh_share_gt60 >= .999].county_name]
S["nv_women"] = float(nv.women_15_44.sum())
S["nv_share_ob60"] = float(nv.ob_hosp_women_gt60.sum() / nv.women_15_44.sum())
S["nv_share_ppw60"] = float(nv.ppw_bh_women_gt60.sum() / nv.women_15_44.sum())
S["nv_share_hc60"] = float(nv.hc_women_gt60.sum() / nv.women_15_44.sum())
S["benchmarks"] = S0["published_benchmarks"]
S["headline"] = {k: S0[k] for k in S0 if k.startswith(("this_project", "rf_", "counties_majority", "all_three"))}
json.dump(S, open(os.path.join(H, "paper_stats.json"), "w"), indent=1, default=float)

# ================= LaTeX tables =================
def tab(name, lines):
    open(os.path.join(T, name), "w").write("\n".join(lines) + "\n")


# Table I sources
tab("t1_sources.tex", [
    r"\begin{tabular}{@{}p{0.30\textwidth}p{0.17\textwidth}p{0.42\textwidth}@{}}", r"\toprule",
    r"Source & Vintage & Role in this study \\", r"\midrule",
    r"OpenStreetMap U.S. regional extracts (openstreetmap.fr) & 13 Nov 2026 & Road network, 48 contiguous states and DC \\",
    r"Overture Maps transportation layer (OSM-derived) & 2026-10-21.0 & Road network, Alaska and Hawaii \\",
    r"Census centers of population, block groups & 2020 & Travel origins (population-weighted centers) \\",
    r"ACS 5-year summary file, table B01001 & 2020--2024 & Women aged 15--44 per block group (weights) \\",
    r"CMS Maternal Health -- Hospital (SM-7, PC-02, PC-07) & Oct 2026 refresh & Hospital labor and delivery status \\",
    r"CMS Hospital General Information; Birthing-Friendly geocodes & Oct 2026 refresh & Hospital type, address, coordinates \\",
    r"Census Geocoder (Public\_AR\_Current) & accessed 13 Nov 2026 & Hospital address geocoding \\",
    r"Project 1 v0.1.0~\cite{emesobum_p1}: FindTreatment.gov, HRSA sites, NPPES, RUCC & Nov 2026 & Treatment facilities, health centers, clinicians, rural and frontier flags \\",
    r"Census Gazetteer (ZCTAs, places); cartographic boundaries & 2024 & Fallback locations, state checks, shorelines, maps \\",
    r"Public OSRM server (router.project-osrm.org) & queried 13 Nov 2026 & Routing check on 450 trips \\",
    r"\bottomrule", r"\end{tabular}"])

# Table II sites
gm = S["sites_geo"]
rows = []
for t in TYPES:
    g = gm.get(t, {})
    n = sum(g.values())
    placed = n - sum(v_ for k, v_ in g.items() if k.startswith("unplaced"))
    rows.append(f"{LAB[t]} & \\texttt{{{t.replace('_', chr(92) + '_')}}} & {c_(n)} & {c_(placed)} & "
                f"{c_(S['route']['sites_routed_' + t])} \\\\")
tab("t2_sites.tex", [r"\begin{tabular}{@{}llrrr@{}}", r"\toprule",
                     r"Care type & Code & Listed & Located & Routed \\", r"\midrule", *rows, r"\bottomrule",
                     r"\end{tabular}"])

# Table III rurality shares (all six types)
G4 = [("All", "All counties"), ("Metro", "Metro"), ("Rural", "Rural (nonmetro, not frontier)"), ("Frontier", "Frontier")]
L = [r"\begin{tabular}{@{}l" + "rr" * 4 + r"@{}}", r"\toprule",
     " & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{g}}}" for g, _ in G4) + r" \\",
     " ".join(f"\\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}" for i in range(4)),
     "Care type & " + " & ".join(r"$>$30 & $>$60" for _ in G4) + r" \\", r"\midrule"]
for t in TYPES:
    L.append(LAB[t] + " & " + " & ".join(f"{p_(S0['rurality'][k][t + '_share_gt30'])} & {p_(S0['rurality'][k][t + '_share_gt60'])}"
                                       for _, k in G4) + r" \\")
L += [r"\midrule", "Counties & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{c_(S0['rurality'][k]['counties'])}}}" for _, k in G4) + r" \\",
      "Women 15--44 (thousands) & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{c_(S0['rurality'][k]['women_15_44'] / 1000)}}}" for _, k in G4) + r" \\",
      r"\bottomrule", r"\end{tabular}"]
tab("t3_rurality.tex", L)

# Table IV distribution (median, p90, within 15) headline types
L = [r"\begin{tabular}{@{}llrrrrr@{}}", r"\toprule",
     r"Care type & Group & Median & P75 & P90 & P95 & $\le$15 min (\%) \\", r"\midrule"]
for t in HEAD:
    for i, g in enumerate(["All", "Metro", "Rural", "Frontier"]):
        d = D[f"{t}|{g}"]
        fmt = lambda x: "n/r" if not np.isfinite(x) else f"{x:.1f}"  # noqa: E731
        L.append(f"{LAB[t] if i == 0 else ''} & {g} & {fmt(d['median'])} & {fmt(d['p75'])} & {fmt(d['p90'])} & "
                 f"{fmt(d['p95'])} & {p_(d['within15'])} \\\\")
    if t != HEAD[-1]:
        L.append(r"\addlinespace")
L += [r"\bottomrule", r"\end{tabular}"]
tab("t4_distribution.tex", L)

# Table V counties where most women are beyond
L = [r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
     r" & \multicolumn{3}{c}{Majority $>$30 min} & \multicolumn{3}{c}{Majority $>$60 min} \\",
     r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
     r"Care type & Metro & Rural & Frontier & Metro & Rural & Frontier \\", r"\midrule"]
for t in TYPES:
    L.append(LAB[t] + " & " + " & ".join(c_(K[f"{t}|{th}|{g}"]["majority"]) for th in (30, 60)
                                       for g in ["Metro", "Rural", "Frontier"]) + r" \\")
L += [r"\midrule", "Counties in group & " + " & ".join(c_(K[f"ob_hosp|30|{g}"]["n"]) for g in ["Metro", "Rural", "Frontier"])
      + " & " + " & ".join(c_(K[f"ob_hosp|60|{g}"]["n"]) for g in ["Metro", "Rural", "Frontier"]) + r" \\",
      r"\bottomrule", r"\end{tabular}"]
tab("t5_counties.tex", L)

# Table VI cross-tab
L = [r"\begin{tabular}{@{}llrr@{}}", r"\toprule",
     r"Care type & Site inside county? & Most women $\le$30 min & Most women $>$30 min \\", r"\midrule"]
for key, lab in [("ob", "Delivering hospital"), ("ppw", "Perinatal SUD facility")]:
    x = X[f"{key}|RF"]
    L.append(f"{lab} & Yes & {c_(x['in_and_reach'])} & {c_(x['in_but_far'])} \\\\")
    L.append(f" & No & {c_(x['none_but_reach'])} & {c_(x['none_and_far'])} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
tab("t6_crosstab.tex", L)

# Table VII states
L = [r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
     r"State & Women 15--44 & Hospital & PPW SUD & Health ctr. \\", r"\midrule"]
for k_, r_ in list(S["state_top_ppw60"].items())[:12]:
    L.append(f"{k_} & {c_(r_['women'])} & {p_(r_['ob_hosp_gt60'])} & {p_(r_['ppw_bh_gt60'])} & {p_(r_['hc_gt60'])} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
tab("t7_states.tex", L)

# Table VIII validation strata
VS = S0["validation"]
L = [r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
     r"Stratum & $n$ & Median ratio & MAD (min) & $r$ & Agree 30 (\%) & Agree 60 (\%) \\", r"\midrule"]
for k_, lab in [("all", "All trips"), ("rurality_metro", "Metro"), ("rurality_rural", "Rural"),
                ("rurality_frontier", "Frontier"), ("type_ob_hosp", "Delivering hospital"),
                ("type_ppw_bh", "Perinatal SUD facility"), ("type_hc", "Health center")]:
    x = VS[k_]
    L.append(f"{lab} & {x['n']} & {x['median_ratio']:.3f} & {x['mean_abs_diff_min']:.1f} & {x['pearson_r']:.3f} & "
             f"{p_(x['agree_gt30'])} & {p_(x['agree_gt60'])} \\\\")
    if k_ in ("all", "rurality_frontier"):
        L.append(r"\addlinespace")
L += [r"\bottomrule", r"\end{tabular}"]
tab("t8_validation.tex", L)

# Table IX Nevada
L = [r"\begin{tabular}{@{}llrrrrrr@{}}", r"\toprule",
     r" & & & \multicolumn{3}{c}{Median minutes} & \multicolumn{2}{c}{$>$60 min (\%)} \\",
     r"\cmidrule(lr){4-6}\cmidrule(lr){7-8}",
     r"County & Class & Women & Hosp. & PPW & HC & Hosp. & PPW \\", r"\midrule"]
for _, r_ in nv.iterrows():
    def m_(x, u):
        return "n/r" if u == 1 else f"{x:.0f}"
    L.append(f"{r_.county_name.replace(' County', '')} & {r_.rurality_class} & {c_(r_.women_15_44)} & "
             f"{m_(r_.ob_hosp_median_min, r_.ob_hosp_median_unreachable)} & {m_(r_.ppw_bh_median_min, r_.ppw_bh_median_unreachable)} & "
             f"{m_(r_.hc_median_min, r_.hc_median_unreachable)} & {p_(r_.ob_hosp_share_gt60, 0)} & {p_(r_.ppw_bh_share_gt60, 0)} \\\\")
L += [r"\bottomrule", r"\end{tabular}"]
tab("t9_nevada.tex", L)

# Table X speeds
from importlib import util  # noqa: E402
spec = util.spec_from_file_location("config", os.path.join(R, "code", "config.py"))
cfg = util.module_from_spec(spec)
spec.loader.exec_module(cfg)
names = [("motorway", "motorway_link"), ("trunk", "trunk_link"), ("primary", "primary_link"),
         ("secondary", "secondary_link"), ("tertiary", "tertiary_link"), ("unclassified", None),
         ("residential", None), ("living_street", None)]
L = [r"\begin{tabular}{@{}lrr@{}}", r"\toprule", r"OSM class & Main (km/h) & Ramp (km/h) \\", r"\midrule"]
for a, b in names:
    L.append(f"{a.replace('_', ' ')} & {cfg.SPEED_KMH[a]} & {cfg.SPEED_KMH[b] if b else '--'} \\\\")
L += [f"ferry (no duration tag) & {cfg.FERRY_KMH} & -- \\\\", r"\bottomrule", r"\end{tabular}"]
tab("t10_speeds.tex", L)
print("paper_stats.json and", len(os.listdir(T)), "tables written")
