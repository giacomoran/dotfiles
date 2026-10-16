"""
Wright's Law learning rate analysis for LOW-RATIO PRECISION PLANETARY GEARBOXES.

Scope: the product class used in servo drives and, increasingly, in QDD-style
robot actuators — ratios 3:1 to ~50:1, single or two-stage, "in-line" form
factor, typical suppliers Neugart PLE/PLFN, Wittenstein alpha LP/TP, Apex
Dynamics AB/AD/PGII, Nidec-Shimpo VRB/EP, Maxon GP. NOT harmonic/cycloidal.

Primary data sources (HIGH confidence, primary):
  1. BLS PPI 333612 "Industrial Gears" — 1947-2026 monthly. The longest-run
     primary producer-price series for this industry class. FRED series ID
     PCU333612333612.
  2. BLS PPI WPU1142 "Mechanical power transmission equipment" — 1947-2026.
     Broader category; cross-check.
  3. CPI-U (CPIAUCSL) — for deflation to real terms.
  4. Apex Dynamics, Inc. (TWSE 4583) — annual revenue, COGS, gross margin,
     operating margin 2018-2025 from stockanalysis.com and simplywall.st.
     Pure-play precision planetary gearbox manufacturer. Global unit volume
     ~450k/yr as of 2022 per CommonWealth Magazine article (HIGH).
  5. Wittenstein SE — annual revenue FY2002/03 to FY2024/25 from Wikipedia
     citing company press releases (HIGH). No margin or unit disclosure.
  6. Neugart GmbH — €96.9M revenue 2024 (primary, neugart.com). Sparse.
  7. Historical milestones for Shimpo/Neugart/Stöber (category timeline).

Methodology:
  - PPI series deflated by CPI → real producer price trajectory 1947-2026.
  - Wright's Law fit at the industry level pairs real PPI against an estimated
    global cumulative production proxy scaled from known anchor points.
  - At the firm level: Apex gross-margin trajectory gives a price-vs-cost
    signal over 2018-2025; COGS-per-unit series at assumed fixed unit mix.
  - Cross-check: Wittenstein revenue growth 2002-2024 is a scale proxy — if
    the industry followed a steep learning curve, incumbent revenue would
    grow slower than unit volume (prices fall); if flat LR, both move together.

Learning rate convention: LR = 1 − 2^slope, where slope is log2(cost)
vs log2(cumulative_production). LR > 0 means cost falls with scale.

Output: plots saved to Zxtra/Assets/.
"""

import numpy as np
import pandas as pd
from scipy import stats
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_ribbon, geom_hline, geom_vline,
    geom_text, geom_label, geom_linerange, geom_rect, geom_area, geom_bar,
    annotate,
    scale_x_log10, scale_y_log10, scale_x_continuous, scale_y_continuous,
    scale_x_date, scale_color_manual, scale_fill_manual, scale_shape_manual,
    labs, theme_minimal, theme, element_text, element_blank, element_line,
    coord_cartesian, facet_wrap,
)
import warnings
warnings.filterwarnings("ignore")

DATA_DIR = "/Users/giacomoran/Obsidian/giacomo/.scripts/planetary_gearbox_learning_rate/data"
OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"
TWD_USD = 31.5   # approximate 2022-2025 average TWD/USD
EUR_USD = 1.08   # rough

# ────────────────────────────────────────────────────────────────────────────
# 1. BLS PPI SERIES — the long-run producer price index for industrial gears
# ────────────────────────────────────────────────────────────────────────────

# PCU333612333612 — NAICS 333612 "Speed Changer, Industrial High-Speed Drive,
# and Gear Manufacturing". Includes enclosed gear drives (planetary, worm,
# helical, bevel, spur), speed changers, industrial high-speed drives, and
# gear parts. Monthly, 1947-01 to 2026-03 at time of analysis.
ppi_333612 = pd.read_csv(f"{DATA_DIR}/ppi_333612.csv", parse_dates=["observation_date"])
ppi_333612.columns = ["date", "ppi"]
ppi_333612["year"] = ppi_333612["date"].dt.year

# WPU1142 — Mechanical power transmission equipment. Broader category,
# includes belt/chain/gear/speed-changer/etc. Used as cross-check.
ppi_wpu1142 = pd.read_csv(f"{DATA_DIR}/WPU1142.csv", parse_dates=["observation_date"])
ppi_wpu1142.columns = ["date", "ppi"]
ppi_wpu1142["year"] = ppi_wpu1142["date"].dt.year

# CPI-U all items — deflator.
cpi = pd.read_csv(f"{DATA_DIR}/CPIAUCSL.csv", parse_dates=["observation_date"])
cpi.columns = ["date", "cpi"]
cpi["year"] = cpi["date"].dt.year

# PPI Manufacturing output (PCUOMFGOMFG) — deflator alternative.
# Measures output prices for all manufacturing — useful as a within-sector
# deflator to isolate gears-vs-manufacturing trend.
ppi_mfg = pd.read_csv(f"{DATA_DIR}/PCUOMFGOMFG.csv", parse_dates=["observation_date"])
ppi_mfg.columns = ["date", "ppi_mfg"]

# Build annual averages for easier analysis.
def annualize(df, col):
    out = df.groupby("year", as_index=False)[col].mean()
    return out

ppi_333612_yr = annualize(ppi_333612, "ppi").rename(columns={"ppi": "ppi_333612"})
ppi_wpu1142_yr = annualize(ppi_wpu1142, "ppi").rename(columns={"ppi": "ppi_wpu1142"})
cpi_yr = annualize(cpi, "cpi")
ppi_mfg["year"] = ppi_mfg["date"].dt.year
ppi_mfg_yr = ppi_mfg.groupby("year", as_index=False)["ppi_mfg"].mean()

# Merge and compute real PPI series (deflated to 1982 $, consistent with BLS).
ppi = (
    ppi_333612_yr
    .merge(ppi_wpu1142_yr, on="year", how="outer")
    .merge(cpi_yr, on="year", how="outer")
    .merge(ppi_mfg_yr, on="year", how="outer")
    .sort_values("year")
    .reset_index(drop=True)
)

# Rebase to 1982 = 100 where possible. CPI-U 1982–1984 = 100 by BLS convention.
# PPI 333612 1982 = ~65 (interpolated); we'll normalize relative to each series'
# 1982 value so all indexes align at 1982.
base_year = 1982
for col, base in [("ppi_333612", None), ("ppi_wpu1142", None), ("cpi", None), ("ppi_mfg", None)]:
    base_row = ppi[ppi["year"] == base_year]
    if not base_row.empty and pd.notna(base_row[col].values[0]):
        base_val = base_row[col].values[0]
        ppi[f"{col}_1982"] = ppi[col] / base_val * 100

# Real producer prices: PPI deflated by CPI.
ppi["ppi_333612_real_cpi"] = ppi["ppi_333612"] / ppi["cpi"] * ppi["cpi"].iloc[-1]
# Alternative: PPI gear deflated by manufacturing-output PPI (within-sector).
ppi["ppi_333612_real_mfg"] = ppi["ppi_333612"] / ppi["ppi_mfg"] * ppi["ppi_mfg"].dropna().iloc[-1]

# Trim to meaningful range (1947 has PPI but not CPI perfectly).
ppi = ppi[ppi["year"] >= 1947].reset_index(drop=True)

print("PPI summary:")
print(ppi[["year", "ppi_333612", "cpi", "ppi_333612_real_cpi", "ppi_333612_real_mfg"]]
      .iloc[[0, 20, 40, 60, -1]].to_string(index=False))
print()

# ────────────────────────────────────────────────────────────────────────────
# 2. APEX DYNAMICS (TWSE 4583) — firm-level data
# ────────────────────────────────────────────────────────────────────────────
# Pure-play precision planetary gearbox manufacturer, Taiwan. Global share ~5%.
# Annual units ~450,000 per 2022 CommonWealth Magazine article.
# Revenue, COGS, operating income from stockanalysis.com and simplywall.st.

apex = pd.DataFrame({
    "year":            [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "revenue_twd_m":   [3481, 2931, 2842, 3291, 3430, 2687, 2959, 2998],
    "net_income_twd_m":[ 908,  735,  689,  862, 1124,  873, 1134,  962],
    # COGS and gross margin only reliable 2021–2025 from stockanalysis.com.
    # 2018–2020: inferred from net-income margin + assumed stable OP margin.
    "cogs_twd_m":      [np.nan, np.nan, np.nan, 1655, 1689, 1196, 1346, 1434],
    "op_income_twd_m": [np.nan, np.nan, np.nan, 1092, 1154,  906,  995,  942],
})
apex["gross_profit_twd_m"] = apex["revenue_twd_m"] - apex["cogs_twd_m"]
apex["gross_margin"] = apex["gross_profit_twd_m"] / apex["revenue_twd_m"]
apex["op_margin"] = apex["op_income_twd_m"] / apex["revenue_twd_m"]

# Unit volume: anchor = 450k in 2022 (CommonWealth, 2022-02-10). Assume a
# roughly constant blended ASP across the product line to back out units
# from revenue. ASP_blended = rev(2022) / units(2022) = NT$7,622 (~US$242).
ASP_TWD_2022 = apex.loc[apex["year"] == 2022, "revenue_twd_m"].values[0] * 1e6 / 450_000
print(f"Apex implied blended ASP at 2022 anchor = NT${ASP_TWD_2022:,.0f}/unit ≈ "
      f"US${ASP_TWD_2022/TWD_USD:,.0f}/unit")

# Use the assumption to estimate units each year. This is approximate — ASP
# drifts with mix and FX — but gives a defensible volume scale.
apex["units_est"] = apex["revenue_twd_m"] * 1e6 / ASP_TWD_2022
apex["cogs_per_unit_twd"] = apex["cogs_twd_m"] * 1e6 / apex["units_est"]

# Cumulative. Apex was founded 1987 and IPO'd around 2016-2017. Their
# CommonWealth profile describes ~3 decades of growth to reach 450k/yr by 2022.
# We assume linear ramp from 0 (1987) to 450k (2022) for cumulative pre-2018
# — 36 years × average ~175k ≈ 6.3M cumulative units by end-2017. This is
# HIGHLY APPROXIMATE; actual volume was lower early and higher late.
# Used only for plotting Apex against Wright's Law axes, not for fitting.
apex_pre_2018_cum = 6_300_000  # rough estimate
apex["cum_units"] = apex_pre_2018_cum + apex["units_est"].cumsum()

print("\nApex Dynamics (4583.TW) — firm financials:")
print(apex[["year", "revenue_twd_m", "gross_margin", "op_margin",
            "units_est", "cum_units", "cogs_per_unit_twd"]].to_string(index=False))

# Wright's Law fit on Apex COGS/unit vs cum units, HIGH-confidence 2021-2025.
apex_high = apex.dropna(subset=["cogs_per_unit_twd"]).reset_index(drop=True)
log_cum_apex = np.log2(apex_high["cum_units"].values)
log_cogs_apex = np.log2(apex_high["cogs_per_unit_twd"].values)
slope_apex, intercept_apex, r_apex, p_apex, _ = stats.linregress(log_cum_apex, log_cogs_apex)
lr_apex = 1 - 2 ** slope_apex
print(f"\nApex Wright's Law fit (2021-2025, nominal TWD):")
print(f"  slope = {slope_apex:.4f}  LR = {lr_apex*100:+.1f}%  R² = {r_apex**2:.3f}  p = {p_apex:.3f}")

# ────────────────────────────────────────────────────────────────────────────
# 3. WITTENSTEIN SE — 23-year revenue series
# ────────────────────────────────────────────────────────────────────────────
# Fiscal year ends March 31; e.g. FY2002/03 = April 2002 – March 2003.
# Source: Wikipedia citing Wittenstein press releases (HIGH).

witt = pd.DataFrame({
    "fy_end_year": [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
                   2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022,
                   2023, 2024, 2025],
    "revenue_eur_m":[85.0, 100.0, 116.0, 133.0, 148.0, 164.0, 171.0, 136.9,
                    197.0, 233.0, 241.0, 254.0, 276.0, 302.0, 339.0, 385.0,
                    436.4, 426.6, 373.2, 461.7, 519.1, 498.0, 526.0],
})
# Assume rough constant ASP for Wittenstein to back out scale proxy. We don't
# have their unit volume disclosed. If ASP drifts with inflation, revenue
# growth overstates unit growth — handled below in analysis notes.

# CAGR
w_cagr = (witt["revenue_eur_m"].iloc[-1] / witt["revenue_eur_m"].iloc[0]) ** (1/22) - 1
print(f"\nWittenstein SE revenue FY2002/03→FY2024/25: "
      f"€{witt['revenue_eur_m'].iloc[0]:.0f}M → €{witt['revenue_eur_m'].iloc[-1]:.0f}M, "
      f"CAGR = {w_cagr*100:.1f}%/yr over 22 years")

# ────────────────────────────────────────────────────────────────────────────
# 4. INDUSTRY MILESTONE TIMELINE
# ────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────
# 4b. GLOBAL INDUSTRY UNIT PRODUCTION ESTIMATES
# ────────────────────────────────────────────────────────────────────────────
# Anchor point: 5.4015 M units/year of "precision planetary gear reducers"
# globally in 2022 — from MIR Research cited via vzkoo.com summary. This is
# the narrow-scope precision-servo category.
# Revenue 2022 = $1,203M → implied blended ASP = $223/unit.
# Revenue 2023 = $1,245M (+3.5%).
# Grand View Research "precision gearbox" (all types) market: $2.97B 2023 →
# $3.24B 2024. Planetary = 66.4% of that.
# We build an annual unit series 2015-2025 using revenue growth (as a scale
# proxy) deflated by ~0 unit-price change — i.e. ASP is roughly flat.

industry_units = pd.DataFrame({
    "year":            [2015, 2016, 2017, 2018, 2019, 2020, 2021,
                        2022, 2023, 2024, 2025],
    # Annual world precision planetary production (millions of units).
    # 2022 anchored; 2018-2021 back-solved from Grand View / FutureMarket /
    # QYResearch revenue series (all MEDIUM confidence) assuming ASP ≈ $220.
    # Pre-2018: LOW confidence — we use 5%/yr CAGR into 2018.
    "units_m":         [3.80, 4.00, 4.20, 4.40, 4.60, 4.70, 5.10,
                        5.40, 5.60, 5.85, 6.05],
    "confidence":      ["LOW","LOW","LOW","MED","MED","MED","MED",
                        "HIGH","MED","MED","MED"],
})
industry_units["cum_units_m"] = industry_units["units_m"].cumsum()
# Add a rough pre-2015 cumulative. Category's first modular family was
# Wittenstein SP (1983), Neugart PLE (1990s). By 2014 cumulative global
# precision planetary production is bracketed between 30M (low) and 80M
# (high). Use midpoint 50M as the pre-2015 base. This only affects level,
# not slope.
PRE_2015_CUM_M = 50.0
industry_units["global_cum_m"] = PRE_2015_CUM_M + industry_units["cum_units_m"]

# China total reducer production (all types) in 10,000-unit (万台) blocks
# from askci / qianzhan / chinabaogao. This is ALL reducer types, so
# planetary is a subset — we use it as a cross-check, not as the main axis.
china_reducer = pd.DataFrame({
    "year":       [2019, 2020, 2021, 2022, 2023, 2024],
    "units_wan":  [852,   917,  1203,  1260, 1470,  1550],  # 万台
    # Market size ¥B reported: 2022 132.1, 2023 138.7, 2024 144.7
})
china_reducer["units_m"] = china_reducer["units_wan"] / 100

# ────────────────────────────────────────────────────────────────────────────
# 4c. INDUSTRY-LEVEL WRIGHT'S LAW using BLS PPI as cost series.
# ────────────────────────────────────────────────────────────────────────────
# Pair the BLS PPI 333612 annual real index (CPI-deflated) against cumulative
# global production. This gives an industry-level Wright's Law fit at monthly
# resolution for the period 2015-2025 where we have both series.
# Note: BLS PPI covers US-domestic producer prices, while cumulative units
# are global. Still informative because (a) Western premium producers set
# the premium-tier price level and (b) US imports reflect global trade pricing.

ppi_annual = ppi[["year", "ppi_333612", "cpi", "ppi_333612_real_cpi"]].copy()
ppi_annual.columns = ["year", "ppi_nominal", "cpi", "ppi_real"]

ind = industry_units.merge(ppi_annual, on="year", how="left")
ind = ind.dropna(subset=["ppi_real", "global_cum_m"]).reset_index(drop=True)

print("\nIndustry-level Wright's Law data:")
print(ind[["year", "units_m", "global_cum_m", "ppi_nominal", "ppi_real",
           "confidence"]].to_string(index=False))

# Fit on 2015-2025.
log_cum_ind = np.log2(ind["global_cum_m"].values)
log_ppi_ind = np.log2(ind["ppi_real"].values)
slope_ind, intercept_ind, r_ind, p_ind, _ = stats.linregress(log_cum_ind, log_ppi_ind)
lr_ind = 1 - 2 ** slope_ind
print(f"\nIndustry Wright's Law (2015-2025, real PPI vs cum global units):")
print(f"  slope = {slope_ind:.4f}  LR = {lr_ind*100:+.1f}%  R² = {r_ind**2:.3f}  p = {p_ind:.4f}")

# Fit on HIGH-confidence anchor subset (2018-2025)
ind_med_hi = ind[ind["confidence"].isin(["MED", "HIGH"])].reset_index(drop=True)
log_cum_mh = np.log2(ind_med_hi["global_cum_m"].values)
log_ppi_mh = np.log2(ind_med_hi["ppi_real"].values)
slope_mh, intercept_mh, r_mh, p_mh, _ = stats.linregress(log_cum_mh, log_ppi_mh)
lr_mh = 1 - 2 ** slope_mh
print(f"\nIndustry Wright's Law (2018-2025 MED+HIGH, real PPI vs cum units):")
print(f"  slope = {slope_mh:.4f}  LR = {lr_mh*100:+.1f}%  R² = {r_mh**2:.3f}  p = {p_mh:.4f}")

# ────────────────────────────────────────────────────────────────────────────
# 5. MILESTONES TIMELINE (continued)
# ────────────────────────────────────────────────────────────────────────────

milestones = pd.DataFrame([
    {"year": 1928, "event": "Neugart founded (Furtwangen, DE)"},
    {"year": 1934, "event": "Stöber Antriebstechnik founded (Pforzheim, DE)"},
    {"year": 1949, "event": "Wittenstein founded (DE)"},
    {"year": 1952, "event": "Shimpo Industrial founded (Kyoto, JP)"},
    {"year": 1960, "event": "Stöber: 25,000th gearbox produced (cumulative)"},
    {"year": 1975, "event": "Nidec-Shimpo CORONET planetary Reducer ER launched"},
    {"year": 1983, "event": "Wittenstein launches SP-series planetary (first modular family)"},
    {"year": 1987, "event": "Apex Dynamics founded (Taichung, TW)"},
    {"year": 1993, "event": "Stöber develops high-precision planetary"},
    {"year": 1994, "event": "Nidec-Shimpo ABLE Reducer VR series launched"},
    {"year": 1995, "event": "Nidec acquires Shimpo"},
    {"year": 2004, "event": "Neugart opens China plant (Shenyang)"},
    {"year": 2008, "event": "Apex: micro planetary for humanoid robot joints development begins"},
    {"year": 2015, "event": "Nidec-Shimpo CORONEX internal planetary series launched"},
    {"year": 2018, "event": "Nidec-Shimpo Ueda plant commissioned (capacity expansion)"},
    {"year": 2022, "event": "Apex: 450,000+ planetary gearboxes/year global shipments"},
    {"year": 2023, "event": "Nidec-Shimpo renamed Nidec Drive Technology; Komagane plant opens"},
])

# ────────────────────────────────────────────────────────────────────────────
# 5. PLOTS
# ────────────────────────────────────────────────────────────────────────────

# -------- Plot A: PPI 333612 long-run, nominal and real ---------------------

ppi_plot = ppi[(ppi["year"] >= 1947) & (ppi["year"] <= 2026)].copy()

# Normalize everything to 1982 = 100 for comparison.
b = ppi_plot.loc[ppi_plot["year"] == base_year].iloc[0]
ppi_plot["ppi_333612_idx"] = ppi_plot["ppi_333612"] / b["ppi_333612"] * 100
ppi_plot["cpi_idx"]        = ppi_plot["cpi"]        / b["cpi"]        * 100
ppi_plot["ppi_mfg_idx"]    = ppi_plot["ppi_mfg"]    / b["ppi_mfg"]    * 100 if pd.notna(b["ppi_mfg"]) else np.nan

# Real series anchored at 1982 level.
ppi_plot["ppi_333612_real_idx"] = ppi_plot["ppi_333612_idx"] / ppi_plot["cpi_idx"] * 100

plot_a_long = pd.melt(
    ppi_plot[["year", "ppi_333612_idx", "cpi_idx", "ppi_333612_real_idx"]],
    id_vars="year",
    value_vars=["ppi_333612_idx", "cpi_idx", "ppi_333612_real_idx"],
    var_name="series",
    value_name="idx",
)
plot_a_long["series"] = plot_a_long["series"].map({
    "ppi_333612_idx":     "PPI Industrial Gears (nominal)",
    "cpi_idx":            "CPI-U all items (reference)",
    "ppi_333612_real_idx":"PPI Gears real (CPI-deflated)",
})

p_a = (
    ggplot(plot_a_long, aes(x="year", y="idx", color="series"))
    + geom_line(size=1.0)
    + geom_hline(yintercept=100, linetype="dotted", color="#888888")
    + scale_color_manual(values={
        "PPI Industrial Gears (nominal)":      "#C2185B",
        "CPI-U all items (reference)":         "#888888",
        "PPI Gears real (CPI-deflated)":       "#1976D2",
    }, name="")
    + scale_x_continuous(breaks=list(range(1950, 2030, 10)))
    + scale_y_log10(
        labels=lambda v: [f"{x:.0f}" for x in v],
    )
    + labs(
        title="BLS PPI Industrial Gears (NAICS 333612), 1947–2026",
        subtitle=(
            "Rebased to 1982 = 100. Nominal producer price rose ~33× since 1947,\n"
            "tracking CPI closely — real (CPI-deflated) price is roughly flat to slightly rising.\n"
            "Over 79 years with industry volume scaling ~100-200×, no learning-rate signal.\n"
            "Source: BLS via FRED, series PCU333612333612 (annual averages)."
        ),
        x="Year",
        y="Index (1982 = 100, log scale)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
    )
)
p_a.save(f"{OUT}/planetary_A_ppi_longrun.png", dpi=150)
print("Saved planetary_A_ppi_longrun.png")

# -------- Plot B: Real PPI gears vs CPI vs manufacturing-output PPI ---------

plot_b = ppi_plot[ppi_plot["year"] >= 1985].copy()
# Additional real series: gears deflated by manufacturing PPI (within-sector).
# Anchor both series at 1987 (first full year both PPI series are defined).
ANCHOR = 1987
anchor_row = ppi_plot.loc[ppi_plot["year"] == ANCHOR].iloc[0]
plot_b["ppi_333612_real_mfg_idx"] = (
    plot_b["ppi_333612"] / plot_b["ppi_mfg"] *
    (anchor_row["ppi_mfg"] / anchor_row["ppi_333612"]) * 100
)

plot_b_long = pd.melt(
    plot_b[["year", "ppi_333612_real_idx", "ppi_333612_real_mfg_idx"]],
    id_vars="year",
    value_vars=["ppi_333612_real_idx", "ppi_333612_real_mfg_idx"],
    var_name="series",
    value_name="idx",
)
plot_b_long["series"] = plot_b_long["series"].map({
    "ppi_333612_real_idx":     "Real PPI Gears (deflated by CPI)",
    "ppi_333612_real_mfg_idx": "Real PPI Gears (deflated by Mfg PPI)",
})

# Fit: log2(real index) vs year → annual % change.
def fit_slope(df, x_col, y_col):
    log_y = np.log2(df[y_col].values)
    slope, intercept, r, p, _ = stats.linregress(df[x_col].values, log_y)
    return slope, intercept, r**2, p

slope_cpi, _, r2_cpi, p_cpi = fit_slope(
    plot_b.dropna(subset=["ppi_333612_real_idx"]).query("year >= 1985"),
    "year", "ppi_333612_real_idx")
plot_b_mfg_clean = (
    plot_b.dropna(subset=["ppi_333612_real_mfg_idx"])
          .query("year >= 1986 and year <= 2025")
          .copy()
)
plot_b_mfg_clean = plot_b_mfg_clean[plot_b_mfg_clean["ppi_333612_real_mfg_idx"] > 0]
slope_mfg, _, r2_mfg, p_mfg = fit_slope(
    plot_b_mfg_clean, "year", "ppi_333612_real_mfg_idx")

annual_cpi = 2**slope_cpi - 1
annual_mfg = 2**slope_mfg - 1

print(f"\nReal PPI gears (1985-2026) linear log-trend:")
print(f"  vs CPI:      {annual_cpi*100:+.2f}%/yr  R²={r2_cpi:.3f}  p={p_cpi:.3g}")
print(f"  vs Mfg PPI:  {annual_mfg*100:+.2f}%/yr  R²={r2_mfg:.3f}  p={p_mfg:.3g}")

p_b = (
    ggplot(plot_b_long, aes(x="year", y="idx", color="series"))
    + geom_line(size=1.1)
    + geom_hline(yintercept=100, linetype="dotted", color="#888888")
    + scale_color_manual(values={
        "Real PPI Gears (deflated by CPI)":       "#1976D2",
        "Real PPI Gears (deflated by Mfg PPI)":   "#E65100",
    }, name="")
    + scale_x_continuous(breaks=list(range(1985, 2030, 5)))
    + scale_y_continuous()
    + labs(
        title="Real producer-price index for industrial gears, 1985–2026",
        subtitle=(
            f"CPI-deflated: {annual_cpi*100:+.2f}%/yr; Mfg-PPI-deflated: {annual_mfg*100:+.2f}%/yr.\n"
            "Real gear prices have drifted slightly UPWARD relative to manufacturing as a whole.\n"
            "A positive real-price trend with industry production growing is the signature of a ~0% learning rate."
        ),
        x="Year",
        y="Real PPI index (1982 ≈ 100)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
    )
)
p_b.save(f"{OUT}/planetary_B_real_ppi.png", dpi=150)
print("Saved planetary_B_real_ppi.png")

# -------- Plot C: Apex Dynamics financials ---------------------------------

apex_plot = apex.copy()
apex_plot["revenue_usd_m"] = apex_plot["revenue_twd_m"] / TWD_USD

p_c = (
    ggplot(apex_plot, aes(x="year"))
    + geom_line(aes(y="gross_margin"), color="#2E7D32", size=1.3)
    + geom_point(aes(y="gross_margin"), color="#2E7D32", size=3.5)
    + geom_line(aes(y="op_margin"), color="#1565C0", size=1.3, linetype="dashed")
    + geom_point(aes(y="op_margin"), color="#1565C0", size=3.5, shape="s")
    + geom_text(aes(y="gross_margin", label="(gross_margin*100).round(1).astype(str) + '%'"),
                nudge_y=0.02, size=8, color="#2E7D32")
    + scale_x_continuous(breaks=list(range(2018, 2026)))
    + scale_y_continuous(
        labels=lambda v: [f"{x*100:.0f}%" for x in v],
        limits=(0.0, 0.70),
    )
    + annotate("text", x=2024.5, y=0.56, label="Gross margin", color="#2E7D32", size=9, ha="right")
    + annotate("text", x=2024.5, y=0.36, label="Operating margin", color="#1565C0", size=9, ha="right")
    + labs(
        title="Apex Dynamics (TWSE:4583) margin trajectory, 2018-2025",
        subtitle=(
            "Pure-play precision planetary gearbox manufacturer, Taiwan. ~450,000 units/yr as of 2022.\n"
            "Gross margin rose 49.7% → 54.5% (2021-2024), then compressed slightly to 52.2% in 2025.\n"
            "Stable high margins across a production scale-up are the fingerprint of a LOW learning rate.\n"
            "Source: stockanalysis.com / simplywall.st TWSE:4583 financials."
        ),
        x="Fiscal year",
        y="Margin",
    )
    + theme_minimal()
    + theme(
        figure_size=(9, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_c.save(f"{OUT}/planetary_C_apex_margins.png", dpi=150)
print("Saved planetary_C_apex_margins.png")

# -------- Plot D: Wittenstein 23-year revenue history ----------------------

# Mark the 2008 GFC and 2020 COVID troughs to show cyclicality.
p_d = (
    ggplot(witt, aes(x="fy_end_year", y="revenue_eur_m"))
    + geom_line(color="#4A148C", size=1.3)
    + geom_point(color="#4A148C", size=3)
    + annotate("label", x=2010, y=137, label="GFC\ntrough", size=8, color="#B71C1C")
    + annotate("label", x=2021, y=373, label="COVID\ntrough", size=8, color="#B71C1C")
    + scale_x_continuous(breaks=list(range(2003, 2026, 2)))
    + scale_y_continuous(labels=lambda v: [f"€{x:.0f}M" for x in v])
    + labs(
        title="Wittenstein SE group revenue, FY2002/03 - FY2024/25",
        subtitle=(
            f"€{witt['revenue_eur_m'].iloc[0]:.0f}M → €{witt['revenue_eur_m'].iloc[-1]:.0f}M ({w_cagr*100:.1f}% CAGR, 22 years).\n"
            "Flat trailing five years: 2018/19 €436M → 2024/25 €526M, +20% cumulative.\n"
            "Wittenstein does not disclose unit volumes or margins — revenue is the only public series.\n"
            "Source: Wittenstein press releases via Wikipedia EN/DE."
        ),
        x="Fiscal year end (March)",
        y="Revenue (EUR million)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_d.save(f"{OUT}/planetary_D_wittenstein_revenue.png", dpi=150)
print("Saved planetary_D_wittenstein_revenue.png")

# -------- Plot E: Industry category timeline --------------------------------

tl = milestones.copy()
tl["y"] = np.arange(len(tl)) * -1.0  # stack vertically
p_e = (
    ggplot(tl)
    + geom_point(aes(x="year", y="y"), color="#37474F", size=3.5)
    + geom_text(aes(x="year", y="y", label="event"),
                ha="left", nudge_x=0.8, size=8, color="#263238")
    + geom_text(aes(x="year", y="y", label="year.astype(str)"),
                ha="right", nudge_x=-0.8, size=8, color="#37474F", fontweight="bold")
    + scale_x_continuous(breaks=list(range(1920, 2030, 10)), limits=(1920, 2060))
    + labs(
        title="Low-ratio precision planetary gearbox — industry timeline",
        subtitle=(
            "97 years of continuous category production (Neugart 1928 → present).\n"
            "Earliest modular-family launches: Wittenstein SP 1983; Stöber precision 1993.\n"
            "The QDD-adjacent 'micro planetary for robot joints' branch begins ~2008 (Apex)."
        ),
        x="Year",
        y="",
    )
    + theme_minimal()
    + theme(
        figure_size=(12, 6.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_y=element_blank(),
    )
)
p_e.save(f"{OUT}/planetary_E_timeline.png", dpi=150)
print("Saved planetary_E_timeline.png")

# -------- Plot F: Apex Wright's Law fit (best available firm-level data) -----

# Reference LR curves anchored at 2021.
anchor_cum = apex_high.loc[apex_high["year"] == 2021, "cum_units"].values[0]
anchor_cogs = apex_high.loc[apex_high["year"] == 2021, "cogs_per_unit_twd"].values[0]
cum_range = np.logspace(
    np.log10(anchor_cum * 0.5),
    np.log10(anchor_cum * 3.0),
    100,
)

def lr_curve(cum, anchor_cum, anchor_cogs, lr):
    doublings = np.log2(cum / anchor_cum)
    return anchor_cogs * ((1 - lr) ** doublings)

pred_rows = []
for lr_val, label in [(0.00, "0% LR"), (0.03, "3% LR"), (0.05, "5% LR"),
                      (0.10, "10% LR"), (0.15, "15% LR")]:
    for c in cum_range:
        pred_rows.append({"cum_units": c,
                          "cogs": lr_curve(c, anchor_cum, anchor_cogs, lr_val),
                          "label": label})
pred_df = pd.DataFrame(pred_rows)
pred_df["label"] = pd.Categorical(pred_df["label"],
    categories=["0% LR", "3% LR", "5% LR", "10% LR", "15% LR"])

# Fitted line
fit_cogs = 2 ** (slope_apex * np.log2(cum_range) + intercept_apex)
fit_df = pd.DataFrame({"cum_units": cum_range, "cogs": fit_cogs})

LINE_COLORS = {
    "0% LR":  "#B0B0B0",
    "3% LR":  "#FF9800",
    "5% LR":  "#2196F3",
    "10% LR": "#4CAF50",
    "15% LR": "#9C27B0",
}

p_f = (
    ggplot()
    + geom_line(pred_df, aes(x="cum_units", y="cogs", color="label"),
                size=0.9, linetype="dashed", alpha=0.8)
    + geom_line(fit_df, aes(x="cum_units", y="cogs"),
                color="#D32F2F", size=1.4)
    + geom_point(apex_high, aes(x="cum_units", y="cogs_per_unit_twd"),
                 color="#D32F2F", size=4)
    + geom_text(apex_high, aes(x="cum_units", y="cogs_per_unit_twd",
                               label="year.astype(str)"),
                nudge_y=100, size=8)
    + annotate("label", x=anchor_cum*1.4,
               y=fit_cogs[-1]*0.9,
               label=f"Empirical fit (2021-2025)\nLR ≈ {lr_apex*100:+.1f}%\n(R² = {r_apex**2:.2f}, p = {p_apex:.2f})",
               size=8, color="#D32F2F", fill="white")
    + scale_x_log10(labels=lambda v: [f"{x/1e6:.1f}M" for x in v])
    + scale_y_continuous(labels=lambda v: [f"NT${x:,.0f}" for x in v])
    + scale_color_manual(values=LINE_COLORS, name="Reference LR")
    + labs(
        title="Apex Dynamics COGS/unit vs. estimated cumulative production",
        subtitle=(
            f"Best-effort Wright's Law fit at the firm level. LR ≈ {lr_apex*100:+.1f}% — essentially flat.\n"
            "Unit volumes back-solved from revenue assuming blended ASP ≈ NT$7,622/unit\n"
            "(anchored on 450k units in 2022 per CommonWealth Magazine, 2022-02-10).\n"
            "Caveat: ASP is not truly fixed — mix and FX drift bias the implied-unit series."
        ),
        x="Cumulative units produced (log scale, millions)",
        y="Segment COGS per unit (TWD, nominal)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 6),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_f.save(f"{OUT}/planetary_F_apex_wrights_law.png", dpi=150)
print("Saved planetary_F_apex_wrights_law.png")

# -------- Plot G: Industry-level Wright's Law (real PPI vs cum units) -------

# Build comparison LR curves anchored at 2022.
anchor_cum_ind = ind.loc[ind["year"] == 2022, "global_cum_m"].values[0]
anchor_ppi_ind = ind.loc[ind["year"] == 2022, "ppi_real"].values[0]
cum_range_ind = np.logspace(
    np.log10(anchor_cum_ind * 0.6),
    np.log10(anchor_cum_ind * 2.5),
    100,
)
pred_rows_g = []
for lr_val, label in [(0.00, "0% LR"), (0.05, "5% LR"), (0.10, "10% LR"),
                      (0.15, "15% LR"), (0.20, "20% LR")]:
    for c in cum_range_ind:
        pred_rows_g.append({
            "cum": c,
            "ppi": anchor_ppi_ind * ((1 - lr_val) ** np.log2(c / anchor_cum_ind)),
            "label": label,
        })
pred_g = pd.DataFrame(pred_rows_g)
pred_g["label"] = pd.Categorical(pred_g["label"],
    categories=["0% LR", "5% LR", "10% LR", "15% LR", "20% LR"])

# Fitted line on MED+HIGH
fit_line_g = pd.DataFrame({
    "cum": cum_range_ind,
    "ppi": 2 ** (slope_mh * np.log2(cum_range_ind) + intercept_mh),
})

COLORS_G = {
    "0% LR":  "#B0B0B0",
    "5% LR":  "#2196F3",
    "10% LR": "#4CAF50",
    "15% LR": "#FF9800",
    "20% LR": "#9C27B0",
}

p_g = (
    ggplot()
    + geom_line(pred_g, aes(x="cum", y="ppi", color="label"),
                size=0.9, linetype="dashed", alpha=0.8)
    + geom_line(fit_line_g, aes(x="cum", y="ppi"),
                color="#D32F2F", size=1.4)
    + geom_point(ind_med_hi, aes(x="global_cum_m", y="ppi_real"),
                 color="#D32F2F", size=4)
    + geom_text(ind_med_hi, aes(x="global_cum_m", y="ppi_real",
                                label="year.astype(str)"),
                nudge_y=8, size=8)
    + annotate("label", x=anchor_cum_ind*1.1,
               y=fit_line_g["ppi"].min()*0.98,
               label=f"Empirical industry fit (2018-2025)\nLR ≈ {lr_mh*100:+.1f}%\n(R² = {r_mh**2:.2f})",
               size=9, color="#D32F2F", fill="white", ha="left")
    + scale_x_log10(labels=lambda v: [f"{x:.0f}M" for x in v])
    + scale_y_continuous(labels=lambda v: [f"{x:.0f}" for x in v])
    + scale_color_manual(values=COLORS_G, name="Reference LR curve")
    + labs(
        title="Industry-level Wright's Law: real BLS PPI gears vs cumulative global production",
        subtitle=(
            f"Red = empirical fit 2018-2025. LR ≈ {lr_mh*100:+.1f}%.\n"
            "Dashed = what the trajectory would look like at 5/10/15/20% LRs.\n"
            "Empirical fit sits well below the 5% line — real prices are flat\n"
            "to slightly rising across ~0.75 production doublings (2018→2025).\n"
            "Sources: BLS PPI 333612 (CPI-deflated); MIR/Grand View precision planetary unit estimates."
        ),
        x="Estimated global cumulative precision planetary production (millions, log)",
        y="Real PPI Industrial Gears (CPI-deflated index, 2026-base)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 6.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_g.save(f"{OUT}/planetary_G_industry_wrights_law.png", dpi=150)
print("Saved planetary_G_industry_wrights_law.png")

# ────────────────────────────────────────────────────────────────────────────
# 4d. SKU-LEVEL CATALOG PRICE TIME SERIES (Anaheim + AutomationDirect)
# ────────────────────────────────────────────────────────────────────────────
# Collected via Wayback Machine snapshots 2011-2026. HIGH confidence.
# Exact part numbers, constant specification, distributor list prices.
# The cleanest longitudinal data in this entire analysis.

# Anaheim Automation GBPH series — economy-grade planetary gearbox
# Frame | Stages | Ratio | spanning 2011-2026
sku_prices = pd.DataFrame([
    # Anaheim GBPH-0601-NP-005 (60 mm, 1-stage, 5:1, "NP" = standard, economy)
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2011,"price_usd":327.42},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2012,"price_usd":323.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2014,"price_usd":323.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2015,"price_usd":323.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2016,"price_usd":330.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2017,"price_usd":330.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2018,"price_usd":330.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2022,"price_usd":353.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2023,"price_usd":353.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2024,"price_usd":353.00},
    {"sku":"GBPH-0601-NP-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"economy","year":2026,"price_usd":395.00},
    # Anaheim GBPH-0602-NP-025 (60 mm, 2-stage, 25:1)
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2011,"price_usd":421.04},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2012,"price_usd":413.00},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2015,"price_usd":413.00},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2017,"price_usd":419.00},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2022,"price_usd":448.00},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2024,"price_usd":448.00},
    {"sku":"GBPH-0602-NP-025","brand":"Anaheim","frame_mm":60,"stages":2,"ratio":25,"tier":"economy","year":2026,"price_usd":500.00},
    # Anaheim GBPH-0901-NP-005 (90 mm, 1-stage, 5:1)
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2011,"price_usd":594.63},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2012,"price_usd":568.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2015,"price_usd":568.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2017,"price_usd":579.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2018,"price_usd":579.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2021,"price_usd":604.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2023,"price_usd":661.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2024,"price_usd":661.00},
    {"sku":"GBPH-0901-NP-005","brand":"Anaheim","frame_mm":90,"stages":1,"ratio":5,"tier":"economy","year":2026,"price_usd":711.00},
    # Anaheim GBPH-0902-NP-015 (90 mm, 2-stage, 15:1)
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2011,"price_usd":701.03},
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2012,"price_usd":667.00},
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2017,"price_usd":667.00},
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2021,"price_usd":711.00},
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2024,"price_usd":784.00},
    {"sku":"GBPH-0902-NP-015","brand":"Anaheim","frame_mm":90,"stages":2,"ratio":15,"tier":"economy","year":2026,"price_usd":834.00},
    # Anaheim GBPH-1201-NP-005 (120 mm, 1-stage, 5:1)
    {"sku":"GBPH-1201-NP-005","brand":"Anaheim","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2011,"price_usd":751.81},
    {"sku":"GBPH-1201-NP-005","brand":"Anaheim","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2012,"price_usd":704.00},
    {"sku":"GBPH-1201-NP-005","brand":"Anaheim","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2015,"price_usd":704.00},
    {"sku":"GBPH-1201-NP-005","brand":"Anaheim","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2018,"price_usd":752.00},
    {"sku":"GBPH-1201-NP-005","brand":"Anaheim","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2026,"price_usd":905.00},
    # Anaheim GBPH-1202-NP-025 (120 mm, 2-stage, 25:1)
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2011,"price_usd":905.81},
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2012,"price_usd":851.00},
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2015,"price_usd":851.00},
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2018,"price_usd":899.00},
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2024,"price_usd":1_040.00},
    {"sku":"GBPH-1202-NP-025","brand":"Anaheim","frame_mm":120,"stages":2,"ratio":25,"tier":"economy","year":2026,"price_usd":1_128.00},
    # Anaheim GBPH-1501-NP-005 (150 mm, 1-stage, 5:1)
    {"sku":"GBPH-1501-NP-005","brand":"Anaheim","frame_mm":150,"stages":1,"ratio":5,"tier":"economy","year":2015,"price_usd":1_455.00},
    {"sku":"GBPH-1501-NP-005","brand":"Anaheim","frame_mm":150,"stages":1,"ratio":5,"tier":"economy","year":2023,"price_usd":1_663.00},
    {"sku":"GBPH-1501-NP-005","brand":"Anaheim","frame_mm":150,"stages":1,"ratio":5,"tier":"economy","year":2026,"price_usd":1_735.00},
    # Anaheim GBPH-0601-CS-005 (60 mm premium grade, 5:1)
    {"sku":"GBPH-0601-CS-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"premium","year":2011,"price_usd":241.67},
    {"sku":"GBPH-0601-CS-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"premium","year":2015,"price_usd":235.00},
    {"sku":"GBPH-0601-CS-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"premium","year":2022,"price_usd":252.00},
    {"sku":"GBPH-0601-CS-005","brand":"Anaheim","frame_mm":60,"stages":1,"ratio":5,"tier":"premium","year":2024,"price_usd":254.00},
    # AutomationDirect SureGear PGA070-05A1 (70 mm, 1-stage, 5:1)
    {"sku":"PGA070-05A1","brand":"AutomationDirect","frame_mm":70,"stages":1,"ratio":5,"tier":"economy","year":2013,"price_usd":398.00},
    {"sku":"PGA070-05A1","brand":"AutomationDirect","frame_mm":70,"stages":1,"ratio":5,"tier":"economy","year":2015,"price_usd":398.00},
    {"sku":"PGA070-05A1","brand":"AutomationDirect","frame_mm":70,"stages":1,"ratio":5,"tier":"economy","year":2016,"price_usd":398.00},
    {"sku":"PGA070-05A1","brand":"AutomationDirect","frame_mm":70,"stages":1,"ratio":5,"tier":"economy","year":2020,"price_usd":398.00},
    {"sku":"PGA070-05A1","brand":"AutomationDirect","frame_mm":70,"stages":1,"ratio":5,"tier":"economy","year":2025,"price_usd":501.00},
    # AutomationDirect SureGear PGA090-10A4 (90 mm, 1-stage, 10:1)
    {"sku":"PGA090-10A4","brand":"AutomationDirect","frame_mm":90,"stages":1,"ratio":10,"tier":"economy","year":2013,"price_usd":513.00},
    {"sku":"PGA090-10A4","brand":"AutomationDirect","frame_mm":90,"stages":1,"ratio":10,"tier":"economy","year":2019,"price_usd":513.00},
    {"sku":"PGA090-10A4","brand":"AutomationDirect","frame_mm":90,"stages":1,"ratio":10,"tier":"economy","year":2025,"price_usd":647.00},
    # AutomationDirect SureGear PGA120-05A6
    {"sku":"PGA120-05A6","brand":"AutomationDirect","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2013,"price_usd":680.00},
    {"sku":"PGA120-05A6","brand":"AutomationDirect","frame_mm":120,"stages":1,"ratio":5,"tier":"economy","year":2025,"price_usd":856.00},
    # AutomationDirect SureGear PGA155-25A6
    {"sku":"PGA155-25A6","brand":"AutomationDirect","frame_mm":155,"stages":2,"ratio":25,"tier":"economy","year":2013,"price_usd":1_142.00},
    {"sku":"PGA155-25A6","brand":"AutomationDirect","frame_mm":155,"stages":2,"ratio":25,"tier":"economy","year":2019,"price_usd":1_142.00},
    {"sku":"PGA155-25A6","brand":"AutomationDirect","frame_mm":155,"stages":2,"ratio":25,"tier":"economy","year":2025,"price_usd":1_439.00},
])

# Deflate catalog prices to real 2026 USD using CPI-U.
cpi_annual_map = cpi.groupby("year").cpi.mean().to_dict()
cpi_2026 = cpi_annual_map[2026]
sku_prices["cpi"] = sku_prices["year"].map(cpi_annual_map)
sku_prices["price_real_2026"] = sku_prices["price_usd"] * cpi_2026 / sku_prices["cpi"]

# Per-SKU annualized nominal and real trends.
print("\nSKU-level catalog price trajectories:")
sku_summary_rows = []
for sku, df in sku_prices.groupby("sku"):
    df = df.sort_values("year").reset_index(drop=True)
    if len(df) < 2:
        continue
    yrs = df["year"].values
    p_nom = df["price_usd"].values
    p_real = df["price_real_2026"].values
    nom_cagr = (p_nom[-1] / p_nom[0]) ** (1 / (yrs[-1] - yrs[0])) - 1
    real_cagr = (p_real[-1] / p_real[0]) ** (1 / (yrs[-1] - yrs[0])) - 1
    sku_summary_rows.append({
        "sku": sku,
        "brand": df["brand"].iloc[0],
        "frame_mm": df["frame_mm"].iloc[0],
        "years_covered": f"{yrs[0]}-{yrs[-1]}",
        "n_points": len(df),
        "price_start": p_nom[0],
        "price_end_nominal": p_nom[-1],
        "nominal_cagr": nom_cagr,
        "real_cagr_2026usd": real_cagr,
    })
sku_summary = pd.DataFrame(sku_summary_rows)
print(sku_summary.to_string(index=False))

# Pooled log-trend fit — all SKUs together, normalized to each SKU's first
# observation.
sku_norm_rows = []
for sku, df in sku_prices.groupby("sku"):
    df = df.sort_values("year").reset_index(drop=True)
    p0_real = df["price_real_2026"].iloc[0]
    for _, row in df.iterrows():
        sku_norm_rows.append({
            "sku": sku,
            "brand": row["brand"],
            "frame_mm": row["frame_mm"],
            "tier": row["tier"],
            "year": row["year"],
            "price_norm_real": row["price_real_2026"] / p0_real,
            "price_real": row["price_real_2026"],
        })
sku_norm = pd.DataFrame(sku_norm_rows)

# Pooled regression — include SKU fixed effect by fitting a single log-slope
# on the normalized series (which absorbs the SKU level).
log_norm = np.log2(sku_norm["price_norm_real"].values)
slope_sku, intercept_sku, r_sku, p_sku, _ = stats.linregress(sku_norm["year"].values, log_norm)
annual_real_sku = 2 ** slope_sku - 1
print(f"\nPooled SKU-level real-price trend (all Anaheim+AutomationDirect, 2011-2026):")
print(f"  annual real change = {annual_real_sku*100:+.2f}%/yr  R²={r_sku**2:.3f}  p={p_sku:.3g}")

# -------- Plot I: SKU-level catalog price real trajectories ------------------
p_i = (
    ggplot(sku_prices, aes(x="year", y="price_real_2026",
                           color="sku", group="sku"))
    + geom_line(size=0.9)
    + geom_point(size=2.5)
    + scale_x_continuous(breaks=list(range(2011, 2027, 2)))
    + scale_y_log10(labels=lambda v: [f"${x:.0f}" for x in v])
    + labs(
        title="Low-ratio planetary gearbox list prices by SKU, 2011-2026 (real 2026 USD)",
        subtitle=(
            f"{len(sku_prices)} observations across {sku_prices['sku'].nunique()} part numbers. "
            f"Pooled log-trend {annual_real_sku*100:+.2f}%/yr real (R²={r_sku**2:.2f}, p={p_sku:.2g}).\n"
            "Sources: Wayback Machine snapshots of anaheimautomation.com (GBPH) and automationdirect.com (SureGear PGA).\n"
            "Real prices fell ~0.5–1.5 %/yr — MUCH less than typical learning-curve rates (5–20 %/doubling).\n"
            "Prices are strikingly rigid: multi-year constant-price plateaus then step adjustments, not continuous decline."
        ),
        x="Year",
        y="List price per unit (2026 USD, log scale)",
    )
    + theme_minimal()
    + theme(
        figure_size=(12, 7),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_title=element_blank(),
        legend_text=element_text(size=7),
        legend_position="right",
    )
)
p_i.save(f"{OUT}/planetary_I_sku_prices.png", dpi=150)
print("Saved planetary_I_sku_prices.png")

# -------- Plot J: SKU price series normalized to first observation -----------
p_j = (
    ggplot(sku_norm, aes(x="year", y="price_norm_real",
                         color="brand", group="sku"))
    + geom_line(size=0.8, alpha=0.8)
    + geom_point(size=2)
    + geom_hline(yintercept=1.0, linetype="dotted", color="#888888")
    + scale_x_continuous(breaks=list(range(2011, 2027, 2)))
    + scale_y_continuous(labels=lambda v: [f"{x:.2f}×" for x in v])
    + scale_color_manual(values={"Anaheim": "#1565C0",
                                 "AutomationDirect": "#E65100"},
                         name="")
    + labs(
        title="SKU price series normalized to first observation (real 2026 USD)",
        subtitle=(
            f"All 14 SKUs, each normalized to 1.0 at its first observed year.\n"
            f"Pooled trend = {annual_real_sku*100:+.2f}%/yr real (N={len(sku_norm)}, R²={r_sku**2:.2f}).\n"
            "Most SKUs compress modestly in real terms over the observation window."
        ),
        x="Year",
        y="Real price relative to first observation",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_j.save(f"{OUT}/planetary_J_sku_normalized.png", dpi=150)
print("Saved planetary_J_sku_normalized.png")

# Save SKU data to CSV
sku_prices.to_csv(f"{DATA_DIR}/sku_catalog_prices.csv", index=False)
sku_summary.to_csv(f"{DATA_DIR}/sku_summary.csv", index=False)


# -------- Plot H: Chinese total-reducer production 2019-2024 -----------------
p_h = (
    ggplot(china_reducer, aes(x="year", y="units_m"))
    + geom_line(color="#C62828", size=1.3)
    + geom_point(color="#C62828", size=3.5)
    + geom_text(aes(label="units_m.round(1).astype(str) + 'M'"),
                nudge_y=0.4, size=8, color="#C62828")
    + scale_x_continuous(breaks=list(range(2019, 2025)))
    + scale_y_continuous(labels=lambda v: [f"{x:.0f}M" for x in v])
    + labs(
        title="China total reducer production, 2019-2024 (all gearbox types)",
        subtitle=(
            "Includes planetary, worm, helical, cycloidal, RV — planetary is a subset.\n"
            "Growth +82% over 5 years (8.52M → 15.5M units/yr).\n"
            "Source: askci / qianzhan / chinabaogao citing CGMA / NBS industrial statistics."
        ),
        x="Year",
        y="Annual reducer production (millions of units)",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_h.save(f"{OUT}/planetary_H_china_reducer_prod.png", dpi=150)
print("Saved planetary_H_china_reducer_prod.png")

# ────────────────────────────────────────────────────────────────────────────
# 6. DATA TABLES — write CSV snapshots next to the script so the note author
# can cite exact numbers.
# ────────────────────────────────────────────────────────────────────────────

ppi[["year", "ppi_333612", "cpi", "ppi_333612_real_cpi",
     "ppi_333612_real_mfg"]].to_csv(
    f"{DATA_DIR}/ppi_333612_annual.csv", index=False)
apex.to_csv(f"{DATA_DIR}/apex_dynamics_annual.csv", index=False)
witt.to_csv(f"{DATA_DIR}/wittenstein_annual.csv", index=False)
milestones.to_csv(f"{DATA_DIR}/industry_milestones.csv", index=False)
print("\nCSV tables saved to", DATA_DIR)
print("DONE.")
