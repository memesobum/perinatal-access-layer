#!/usr/bin/env python3
"""paper/make_numbers.py: write paper/numbers.tex (LaTeX macros) from report/stats.json and paper/paper_stats.json.

Plain-language summary: the detailed preprint never contains a typed number. Every value is a macro defined
here from the pipeline's statistics files, so the paper and the data cannot disagree. Run after analysis.py.
"""
import json
import os

H = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(H)
S0 = json.load(open(os.path.join(R, "report", "stats.json")))
S = json.load(open(os.path.join(H, "paper_stats.json")))
RT = S0["rurality"]
V = S0["validation"]
D = S["dist"]
K = S["county"]
X = S["crosstab30"]


def c(x):
    return f"{int(round(x)):,}".replace(",", "{,}")


def p(x, d=1):
    return f"{100 * x:.{d}f}"


def f(x, d=1):
    return f"{x:.{d}f}"


def lst(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + ", and " + xs[-1]


NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
G = {"All": "All counties", "Metro": "Metro", "Rural": "Rural (nonmetro, not frontier)", "Frontier": "Frontier",
     "RF": "Rural or frontier"}
TT = {"ob_hosp": "OB", "ob_hosp_upper": "OBU", "ob_clin": "OBC", "ppw_bh": "PPW", "mh_any": "MH", "hc": "HC"}
GT = {"All": "All", "Metro": "Metro", "Rural": "Rural", "Frontier": "Frontier"}
M = {}
M["Version"] = S0["version"]
doi_f = os.path.join(R, "report", "doi.txt")
M["DOI"] = open(doi_f).read().strip() if os.path.exists(doi_f) else "10.5281/zenodo.24206837"
M["NCounties"] = c(S["n_counties"])
M["NMetro"] = c(S["n_class"]["metro"])
M["NRural"] = c(S["n_class"]["rural"])
M["NFrontier"] = c(S["n_class"]["frontier"])
M["NMetroFrontier"] = c(S["n_metro_frontier"])
M["NRF"] = c(RT["Rural or frontier"]["counties"])
M["NBG"] = c(S["origins"]["bg_matched"])
M["NBGZero"] = c(S["origins"]["bg_zero_women"])
M["Women"] = c(S["women_total"])
M["WomenMillions"] = f(S["women_total"] / 1e6, 1)
M["WomenRF"] = c(RT["Rural or frontier"]["women_15_44"])
M["WomenRFShare"] = p(S["women_share_rf"])
M["WomenFrontier"] = c(RT["Frontier"]["women_15_44"])
M["WomenRural"] = c(RT["Rural (nonmetro, not frontier)"]["women_15_44"])
M["WomenMetro"] = c(RT["Metro"]["women_15_44"])
r = S["route"]
M["Vertices"] = f(r["vertices"] / 1e6)
M["Arcs"] = f(r["arcs"] / 1e6)
M["KmRoad"] = f(r["km_road"] / 1e6)
M["KmFerry"] = c(r["km_ferry"])
M["Components"] = c(r["components"])
M["MainNetworks"] = c(r["main_networks"])
M["ShareMain"] = p(r["share_vertices_in_main"], 2)
M["BGNoRoad"] = c(S["status_counts"].get("no_road_within_25km", 0))
M["WomenNoRoad"] = c(S["status_women"].get("no_road_within_25km", 0))
M["BGSep"] = c(S["status_counts"].get("separate_road_network", 0))
M["WomenSep"] = c(S["status_women"].get("separate_road_network", 0))
M["SnapMedianM"] = c(S["snap_q"]["0.5"] * 1000)
M["SnapPNinetyM"] = c(S["snap_q"]["0.9"] * 1000)
M["SnapPNinetyNineKm"] = f(S["snap_q"]["0.99"], 2)
ss = S["sites"]
for t, tag in TT.items():
    M[f"Sites{tag}"] = c(ss[t])
    M[f"Routed{tag}"] = c(r[f"sites_routed_{t}"])
M["SitesOBAdded"] = c(ss["ob_hosp_upper"] - ss["ob_hosp"])
M["AddedCAH"] = c(S["upper_added_by_type"].get("Critical Access Hospitals", 0))
M["AddedAcute"] = c(S["upper_added_by_type"].get("Acute Care Hospitals", 0))
cs = S["cms_status"]
M["CMSConfSM"] = c(cs["confirmed_sm7"])
M["CMSConfPC"] = c(cs["confirmed_pc_measures"])
M["CMSNoLD"] = c(cs["no_labor_delivery"])
M["CMSNotRep"] = c(cs["not_reported"])
M["CMSTotal"] = c(sum(cs.values()))
sg = S["sites_geo"]["ob_hosp_upper"]
M["HospExact"] = c(sg.get("census_geocoder_exact", 0))
M["HospCMS"] = c(sg.get("cms_birthing_friendly_geocode", 0))
M["HospNonexact"] = c(sg.get("census_geocoder_nonexact", 0))
M["HospTown"] = c(sg.get("town_interior_point", 0))
M["HospZip"] = c(sg.get("zip_interior_point", 0))
M["StateMismatch"] = c(S["state_mismatch_rows"])
M["GeocodeDiff"] = c(S["hosp_geocode_diff_gt2km"])
for t, tag in TT.items():
    for g, gt in GT.items():
        M[f"{tag}{gt}Thirty"] = p(RT[G[g]][f"{t}_share_gt30"])
        M[f"{tag}{gt}Sixty"] = p(RT[G[g]][f"{t}_share_gt60"])
    M[f"{tag}RFSixty"] = p(RT["Rural or frontier"][f"{t}_share_gt60"])
    M[f"{tag}RFThirty"] = p(RT["Rural or frontier"][f"{t}_share_gt30"])
    for g in ["All", "Metro", "Rural", "Frontier"]:
        d = D[f"{t}|{g}"]
        M[f"{tag}{GT[g]}Median"] = f(d["median"]) if d["median"] < 1e9 else "n/r"
        M[f"{tag}{GT[g]}PNinety"] = f(d["p90"]) if d["p90"] < 1e9 else "n/r"
        M[f"{tag}{GT[g]}Mean"] = f(d["mean_reachable"])
        M[f"{tag}{GT[g]}WithinFifteen"] = p(d["within15"])
        M[f"{tag}{GT[g]}WithinThirty"] = p(d["within30"])
        M[f"{tag}{GT[g]}WithinSixty"] = p(d["within60"])
        M[f"{tag}{GT[g]}WithinNinety"] = p(d["within90"])
        M[f"{tag}{GT[g]}WithinOneTwenty"] = p(d["within120"])
        M[f"{tag}{GT[g]}WomenSixty"] = c(d["women_gt60"])
        M[f"{tag}{GT[g]}WomenThirty"] = c(d["women_gt30"])
    for th, w in [(30, "Thirty"), (60, "Sixty")]:
        M[f"Maj{w}{tag}"] = c(K[f"{t}|{th}|All"]["majority"])
        M[f"All{w}{tag}"] = c(K[f"{t}|{th}|All"]["all"])
        for g in ["Metro", "Rural", "Frontier"]:
            M[f"Maj{w}{tag}{g}"] = c(K[f"{t}|{th}|{g}"]["majority"])
            M[f"All{w}{tag}{g}"] = c(K[f"{t}|{th}|{g}"]["all"])
    M[f"RFMajSixty{tag}"] = c(S0[f"rf_majority_gt60_{t}"])
    M[f"RFWomenSixty{tag}"] = c(S0[f"rf_women_gt60_{t}"])
M["OBWithinThirtyNat"] = p(S0["this_project_ob_hosp_share_within_30"])
M["OBWithinSixtyNat"] = p(S0["this_project_ob_hosp_share_within_60"])
M["OBMeanNat"] = f(S0["this_project_ob_hosp_mean_min"])
M["RFMajSixtyPPWNotOB"] = c(S0["rf_majority_gt60_ppw_but_lt_half_ob"])
a3 = S["all3"]
M["AllThree"] = c(a3["n"])
M["AllThreeFrontier"] = c(a3["frontier"])
M["AllThreeSmall"] = c(a3["small"])
M["AllThreeWomen"] = c(a3["women"])
M["AllThreeStates"] = c(a3["n_states"])
top = list(a3["states"].items())
M["AllThreeTopStates"] = lst([f"{k} ({v})" for k, v in top[:5]])
for key, tag in [("ppw", "PPW"), ("ob", "OB")]:
    x = X[f"{key}|RF"]
    M[f"X{tag}InReach"] = c(x["in_and_reach"])
    M[f"X{tag}InFar"] = c(x["in_but_far"])
    M[f"X{tag}NoneReach"] = c(x["none_but_reach"])
    M[f"X{tag}NoneFar"] = c(x["none_and_far"])
    M[f"X{tag}None"] = c(x["none_but_reach"] + x["none_and_far"])
    M[f"X{tag}In"] = c(x["in_and_reach"] + x["in_but_far"])
    M[f"X{tag}Agree"] = p((x["in_and_reach"] + x["none_and_far"]) / sum(x.values()))
sv = S["sens"]
M["SensCountiesChange"] = c(S["sens_counties_change60"])
M["SensWomenChange"] = c(S["sens_bg_any_change"])
M["SensWomenChangeMillions"] = f(S["sens_bg_any_change"] / 1e6)
sp = S["spearman"]
M["RhoOBPPW"] = f(sp["ob_hosp|ppw_bh"], 2)
M["RhoOBHC"] = f(sp["ob_hosp|hc"], 2)
M["RhoPPWHC"] = f(sp["ppw_bh|hc"], 2)
ve = S["val_extra"]
M["ValN"] = c(V["all"]["n"])
M["ValRatio"] = f(V["all"]["median_ratio"], 3)
M["ValRatioTwo"] = f(V["all"]["median_ratio"], 2)
M["ValWithin"] = p(V["all"]["share_within_20pct_or_5min"])
M["ValMAD"] = f(V["all"]["mean_abs_diff_min"])
M["ValR"] = f(V["all"]["pearson_r"], 3)
M["ValAgreeThirty"] = p(V["all"]["agree_gt30"])
M["ValAgreeSixty"] = p(V["all"]["agree_gt60"])
M["ValMeanDiff"] = f(ve["mean_diff"], 2)
M["ValLoaLow"] = f(ve["loa_low"])
M["ValLoaHigh"] = f(ve["loa_high"])
M["ValPNinetyAbs"] = f(ve["p90_absdiff"])
M["ValNAbsTen"] = c(ve["n_absdiff_gt10"])
for k_, tag in [("rurality_metro", "Metro"), ("rurality_rural", "Rural"), ("rurality_frontier", "Frontier")]:
    M[f"ValRatio{tag}"] = f(V[k_]["median_ratio"], 2)
    M[f"ValWithin{tag}"] = p(V[k_]["share_within_20pct_or_5min"])
    M[f"ValAgreeSixty{tag}"] = p(V[k_]["agree_gt60"])
M["StatesPPWOverTen"] = c(S["state_count_ppw60_gt10"])
M["StatesOBOverFive"] = c(S["state_count_ob60_gt5"])
st = list(S["state_top_ppw60"].items())
for i, (k_, v_) in enumerate(st[:5]):
    w = ["One", "Two", "Three", "Four", "Five"][i]
    M[f"TopState{w}"] = k_
    M[f"TopState{w}PPW"] = p(v_["ppw_bh_gt60"])
M["NVList"] = lst(S["nv_all_beyond60_ob"])
M["NVN"] = NUM.get(len(S["nv_all_beyond60_ob"]), str(len(S["nv_all_beyond60_ob"])))
M["NVListPPW"] = lst(S["nv_all_beyond60_ppw"])
M["NVNPPW"] = NUM.get(len(S["nv_all_beyond60_ppw"]), str(len(S["nv_all_beyond60_ppw"])))
M["NVWomen"] = c(S["nv_women"])
M["NVOBSixty"] = p(S["nv_share_ob60"])
M["NVPPWSixty"] = p(S["nv_share_ppw60"])
M["NVHCSixty"] = p(S["nv_share_hc60"])
B = S["benchmarks"]
M["RayburnThirty"] = p(B["rayburn_2012"]["share_within_30"])
M["RayburnSixty"] = p(B["rayburn_2012"]["share_within_60"])
M["RayburnHosp"] = c(B["rayburn_2012"]["hospitals"])
M["FontenotMean"] = f(B["fontenot_2024"]["mean_minutes_tract_level"])
with open(os.path.join(H, "numbers.tex"), "w") as fh:
    fh.write("% generated by make_numbers.py from report/stats.json and paper/paper_stats.json -- do not edit\n")
    for k, v in M.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    fh.write("\\newcommand{\\DraftBanner}{" + ("DRAFT, not yet verified by the author. Do not cite." if S0["draft"] else "") + "}\n")
print(f"{len(M)} macros")
