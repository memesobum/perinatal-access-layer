#!/usr/bin/env python3
"""paper/make_tex_inputs.py: turn report/stats.json and the processed tables into LaTeX macros and tables.

Plain-language summary: every number the paper prints is written here from the stats file, so the
paper and the data cannot disagree (stats-file rule). Run it, then compile main.tex.
"""
import json
import os

import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
S = json.load(open(os.path.join(R, "report", "stats.json")))
RT = S["rurality"]
V = S["validation"]


def c(x):
    return f"{int(round(x)):,}".replace(",", "{,}")


def p1(x):
    return f"{100 * x:.1f}"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


A, M, RU, FR, RF = (RT[k] for k in ["All counties", "Metro", "Rural (nonmetro, not frontier)", "Frontier",
                                    "Rural or frontier"])
M_ = {
    "Version": S["version"], "NCounties": c(S["counties"]), "NMetro": c(M["counties"]), "NRural": c(RU["counties"]),
    "NFrontier": c(FR["counties"]), "NRF": c(RF["counties"]),
    "Women": c(A["women_15_44"]), "WomenRF": c(RF["women_15_44"]), "WomenFrontier": c(FR["women_15_44"]),
    "NBG": c(S["origins"]["bg_matched"]), "KmRoad": f1(S["route"]["km_road"] / 1e6),
    "Vertices": f1(S["route"]["vertices"] / 1e6), "Arcs": f1(S["route"]["arcs"] / 1e6),
    "MainNetworks": c(S["route"]["main_networks"]),
    "WomenNotConnected": c(S["route"]["women_not_connected"]), "BGNotConnected": c(S["route"]["bg_not_connected"]),
    "SitesOB": c(S["sites"]["ob_hosp"]), "SitesOBUpper": c(S["sites"]["ob_hosp_upper"]),
    "SitesOBAdded": c(S["sites"]["ob_hosp_upper"] - S["sites"]["ob_hosp"]),
    "SitesOBClin": c(S["sites"]["ob_clin"]), "SitesPPW": c(S["sites"]["ppw_bh"]), "SitesMH": c(S["sites"]["mh_any"]),
    "SitesHC": c(S["sites"]["hc"]),
    "OBWithinThirty": p1(S["this_project_ob_hosp_share_within_30"]),
    "OBWithinSixty": p1(S["this_project_ob_hosp_share_within_60"]), "OBMeanMin": f1(S["this_project_ob_hosp_mean_min"]),
    "ValN": c(V["all"]["n"]), "ValRatio": f2(V["all"]["median_ratio"]), "ValWithin": p1(V["all"]["share_within_20pct_or_5min"]),
    "ValMAD": f1(V["all"]["mean_abs_diff_min"]), "ValR": f2(V["all"]["pearson_r"]),
    "ValAgreeThirty": p1(V["all"]["agree_gt30"]), "ValAgreeSixty": p1(V["all"]["agree_gt60"]),
    "ValRatioMetro": f2(V["rurality_metro"]["median_ratio"]), "ValRatioRural": f2(V["rurality_rural"]["median_ratio"]),
    "ValRatioFrontier": f2(V["rurality_frontier"]["median_ratio"]),
    "ValWithinFrontier": p1(V["rurality_frontier"]["share_within_20pct_or_5min"]),
    "RFNoPPWInCounty": c(S["rf_ppw_none_in_county"]),
    "RFNoPPWButWithin": c(S["rf_ppw_none_in_county_but_most_within30"]),
    "RFPPWButBeyond": c(S["rf_ppw_in_county_but_most_beyond30"]),
    "RFMajSixtyPPW": c(S["rf_majority_gt60_ppw_bh"]), "RFMajSixtyOB": c(S["rf_majority_gt60_ob_hosp"]),
    "RFMajSixtyOBUpper": c(S["rf_majority_gt60_ob_hosp_upper"]), "RFMajSixtyHC": c(S["rf_majority_gt60_hc"]),
    "RFMajSixtyPPWNotOB": c(S["rf_majority_gt60_ppw_but_lt_half_ob"]),
    "RFWomenSixtyOB": c(S["rf_women_gt60_ob_hosp"]), "RFWomenSixtyOBUpper": c(S["rf_women_gt60_ob_hosp_upper"]),
    "RFWomenSixtyPPW": c(S["rf_women_gt60_ppw_bh"]), "RFWomenSixtyHC": c(S["rf_women_gt60_hc"]),
    "AllThree": c(S["counties_majority_gt60_all_three"]), "AllThreeRF": c(S["rf_counties_majority_gt60_all_three"]),
    "MajSixtyOB": c(S["counties_majority_gt60_ob_hosp"]), "MajSixtyPPW": c(S["counties_majority_gt60_ppw_bh"]),
    "MajSixtyHC": c(S["counties_majority_gt60_hc"]), "MajThirtyPPW": c(S["counties_majority_gt30_ppw_bh"]),
    "MajThirtyOB": c(S["counties_majority_gt30_ob_hosp"]),
    "RayburnThirty": p1(S["published_benchmarks"]["rayburn_2012"]["share_within_30"]),
    "RayburnSixty": p1(S["published_benchmarks"]["rayburn_2012"]["share_within_60"]),
    "FontenotMean": f1(S["published_benchmarks"]["fontenot_2024"]["mean_minutes_tract_level"]),
}
for t, tag in [("ob_hosp", "OB"), ("ob_hosp_upper", "OBU"), ("ob_clin", "OBC"), ("ppw_bh", "PPW"), ("mh_any", "MH"),
               ("hc", "HC")]:
    for g, gt in [(A, "All"), (M, "Metro"), (RU, "Rural"), (FR, "Frontier"), (RF, "RF")]:
        M_[f"{tag}{gt}Thirty"] = p1(g[f"{t}_share_gt30"])
        M_[f"{tag}{gt}Sixty"] = p1(g[f"{t}_share_gt60"])

NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
nvl = S["nv_all_beyond60_ob"]
M_["NVBeyondList"] = (", ".join(nvl[:-1]) + ", and " + nvl[-1]) if len(nvl) > 1 else "".join(nvl)
M_["NVBeyondN"] = NUM.get(len(nvl), str(len(nvl)))
M_["AllThreeFrontier"] = c(S["all_three_frontier"])
M_["AllThreeSmall"] = c(S["all_three_small_women"])
M_["AllThreeWomen"] = c(S["all_three_women"])
M_["SepNetWomen"] = c(S["route"]["women_separate_network"])
M_["KmFerry"] = c(S["route"]["km_ferry"])
doi_file = os.path.join(R, "report", "doi.txt")
M_["DOI"] = open(doi_file).read().strip() if os.path.exists(doi_file) else "[DOI pending]"

with open(os.path.join(H, "numbers.tex"), "w") as f:
    f.write("% generated by make_tex_inputs.py from report/stats.json -- do not edit\n")
    for k, v in M_.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    f.write("\\newcommand{\\DraftBanner}{" + ("DRAFT, not yet verified by the author. Do not cite." if S["draft"] else "")
            + "}\n")

# Table I: share of women beyond 30 / 60 minutes by care type and county group
rows = [("Delivering hospital (confirmed)", "ob_hosp"), ("Delivering hospital (upper bound)", "ob_hosp_upper"),
        ("Obstetric clinician ZIP", "ob_clin"), ("Perinatal treatment facility", "ppw_bh"),
        ("Mental health facility, any", "mh_any"), ("Health center", "hc")]
groups = [("All", A), ("Metro", M), ("Rural", RU), ("Frontier", FR)]
L = ["\\begin{tabular}{@{}l" + "rr" * len(groups) + "@{}}", "\\toprule",
     " & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{g}}}" for g, _ in groups) + " \\\\",
     " ".join(f"\\cmidrule(lr){{{2 + 2 * i}-{3 + 2 * i}}}" for i in range(len(groups))),
     "Care type & " + " & ".join(">30 & >60" for _ in groups) + " \\\\", "\\midrule"]
for lab, t in rows:
    L.append(lab + " & " + " & ".join(f"{p1(g[f'{t}_share_gt30'])} & {p1(g[f'{t}_share_gt60'])}" for _, g in groups)
             + " \\\\")
L += ["\\midrule", "Counties & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{c(g['counties'])}}}" for _, g in groups)
      + " \\\\", "Women 15--44 (thousands) & " + " & ".join(
          f"\\multicolumn{{2}}{{c}}{{{c(g['women_15_44'] / 1000)}}}" for _, g in groups) + " \\\\",
      "\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "table_rurality.tex"), "w").write("\n".join(L) + "\n")

# Table II: Nevada counties (the author's validation ground)
cty = pd.read_csv(os.path.join(R, "data", "processed", "access_county.csv"), dtype={"fips": str})
nv = cty[cty.state == "NV"].sort_values("county_name")
L = ["\\begin{tabular}{@{}lrrrrr@{}}", "\\toprule",
     "County & Class & Women & OB hosp. & PPW fac. & Health ctr. \\\\", "\\midrule"]


def med(x, u):
    return "no road" if u == 1 else ("--" if pd.isna(x) else f"{x:.0f}")


for _, r in nv.iterrows():
    L.append(f"{r.county_name.replace(' County', '')} & {r.rurality_class} & {c(r.women_15_44)} & "
             f"{med(r.ob_hosp_median_min, r.ob_hosp_median_unreachable)} & "
             f"{med(r.ppw_bh_median_min, r.ppw_bh_median_unreachable)} & {med(r.hc_median_min, r.hc_median_unreachable)} \\\\")
L += ["\\bottomrule", "\\end{tabular}"]
open(os.path.join(H, "table_nevada.tex"), "w").write("\n".join(L) + "\n")
print(f"wrote {len(M_)} macros, table_rurality.tex, table_nevada.tex")
