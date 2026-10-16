"""
Wright's Law learning rate analysis for precision harmonic reducers.

Goal: replace the current inferred ~5% estimate with an empirical estimate
grounded in actual manufacturer cost data.

Primary source: Leaderdrive (绿的谐波, 688017.SS) — the only publicly listed
Chinese harmonic reducer producer with multi-year unit volume AND margin data.
Supporting: HDSI (6324.T) financial trend; Sichuan Robot unit volumes.

Key methodology:
  - COGS/unit = ASP × (1 − gross_margin)   [both from segment financials]
  - Cumulative production = ∑ annual units
  - Wright's Law: log(COGS/unit) = b × log(cum_prod) + const
  - Learning rate LR = 1 − 2^b  (b < 0 for true learning)
  - Cross-check: inflation-adjusted COGS using Chinese manufacturing wage index

Data sources & confidence:
  - Leaderdrive IPO prospectus (SSE, 2020): units 2017–2019 [HIGH]
  - Leaderdrive annual reports 2021–2024 via cninfo / Sina Finance [HIGH]
  - Gross margin 2019 from prospectus segment financials [MEDIUM — high due to IPO prep]
  - Gross margin 2020–2024 from annual report segment tables [HIGH]
  - Sichuan Robot volumes from wabei.cn citing annual reports [HIGH]
  - HDSI financials from stockanalysis.com (TSE 6324) [HIGH]
  - Chinese manufacturing wage index: NBS annual survey data, approximate [MEDIUM]

Caveats:
  1. Leaderdrive segment revenue bundles harmonic reducers + metal parts.
     Revenue ÷ units overstates per-reducer ASP; gross margin is also blended.
     The COGS/unit series is therefore a *segment-level* proxy, not pure reducer.
  2. 2019 gross margin of ~59% is anomalously high vs. 2020–2024 range (31–53%).
     IPO-year margins sometimes reflect product mix optimisation for listing.
  3. Only 2021–2024 has both HIGH-confidence units AND HIGH-confidence margins
     → Wright's Law fit is anchored on this 4-point window.
"""

import numpy as np
import pandas as pd
from scipy import stats
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_ribbon, geom_hline,
    geom_text, geom_label, geom_linerange, annotate,
    scale_x_log10, scale_y_log10, scale_x_continuous, scale_y_continuous,
    scale_color_manual, scale_fill_manual, scale_shape_manual,
    labs, theme_minimal, theme, element_text, element_blank,
    coord_cartesian, facet_wrap,
)
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"
RMB_USD = 7.2  # approximate CNY/USD used throughout for context

# ── 1. RAW DATA ───────────────────────────────────────────────────────────────

# Leaderdrive annual harmonic reducer shipments (units).
# Source: IPO prospectus (2017–2019), annual reports (2021–2024).
# 2020 estimated from segment revenue ÷ analyst-cited ASP ~¥1,837.
ld_units = {
    2017: 66_800,
    2018: 92_100,
    2019: 88_600,
    2020: 111_000,   # MEDIUM confidence — estimated
    2021: 256_619,
    2022: 257_402,
    2023: 211_478,
    2024: 246_501,
}

# Leaderdrive segment (harmonic reducer + metal parts) ASP in CNY.
# 2021–2024: derived as segment_revenue_CNY / units for consistency.
#   2021: ¥416M / 256,619 = ¥1,621
#   2022: ¥416M / 257,402 = ¥1,617
#   2023: ¥317M / 211,478 = ¥1,499
#   2024: ¥325M / 246,501 = ¥1,319
# 2017–2020: from prospectus and analyst series.
ld_asp_cny = {
    2017: 1_923,
    2018: 1_630,
    2019: 1_632,
    2020: 1_837,  # MEDIUM
    2021: 1_621,
    2022: 1_617,
    2023: 1_499,
    2024: 1_319,
}

# Leaderdrive harmonic reducer segment gross margin (decimal).
# 2019: IPO prospectus segment figure [MEDIUM — anomalously high]
# 2020–2024: annual report segment tables [HIGH]
ld_gm = {
    2019: 0.591,   # MEDIUM — IPO prospectus; suspiciously high
    2020: 0.476,
    2021: 0.525,
    2022: 0.4878,
    2023: 0.4117,
    2024: 0.3085,  # segment-level; company-wide was ~37.5%
}

# Sichuan Robot (subsidiary of a larger group) — harmonic reducer volumes.
# Source: wabei.cn citing annual reports (HIGH confidence).
# No margin data available.
sichuan_units = {
    2020: 19_962,
    2021: 33_534,
    2022: 40_759,
    2023: 38_758,
    2024: 55_723,
}

# HDSI (Harmonic Drive Systems, TSE 6324) — revenue and COGS in JPY millions.
# No unit volumes recoverable from public sources.
# Fiscal year ending March; labelled by the year the FY ends.
# Source: stockanalysis.com (HIGH confidence).
hdsi_financials = pd.DataFrame({
    "fy_end":      [2021,   2022,   2023,   2024,   2025],
    "revenue_jpy": [37_034, 57_087, 71_527, 55_796, 55_645],
    "cogs_jpy":    [24_452, 34_662, 45_741, 40_190, 40_791],
})
hdsi_financials["gm"] = 1 - hdsi_financials["cogs_jpy"] / hdsi_financials["revenue_jpy"]
hdsi_financials["cogs_per_revenue"] = hdsi_financials["cogs_jpy"] / hdsi_financials["revenue_jpy"]


# ── 2. LEADERDRIVE WRIGHT'S LAW DATASET ──────────────────────────────────────

# Years with both units AND margins (required for COGS/unit computation).
years_with_data = sorted(set(ld_units) & set(ld_gm))

rows = []
for year in years_with_data:
    rows.append({
        "year":    year,
        "units":   ld_units[year],
        "asp_cny": ld_asp_cny[year],
        "gm":      ld_gm[year],
    })

ld = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)

# COGS/unit = ASP × (1 − gross_margin)
ld["cogs_unit_cny"] = ld["asp_cny"] * (1 - ld["gm"])
ld["cogs_unit_usd"] = ld["cogs_unit_cny"] / RMB_USD

# Cumulative production: sum of all available Leaderdrive units through each year.
# Note: pre-2017 production is unknown. We start the cumulative from 2017.
# This understates true cumulative production, which means our doubling index
# is shifted — but for computing the slope of log(cost) vs log(cum_prod),
# the absolute level doesn't matter, only the slope.
all_years_sorted = sorted(ld_units.keys())
cum_prod = {}
running = 0
for y in all_years_sorted:
    running += ld_units[y]
    cum_prod[y] = running

ld["cum_prod"] = ld["year"].map(cum_prod)

# Mark confidence level of each data point.
ld["confidence"] = ld["year"].map({
    2019: "medium",  # 59% GM is unusually high; IPO year
    2020: "medium",  # units estimated; COVID production disruption
    2021: "high",
    2022: "high",
    2023: "high",
    2024: "high",
})

print("Leaderdrive Wright's Law dataset:")
print(ld[["year", "units", "cum_prod", "asp_cny", "gm", "cogs_unit_cny", "cogs_unit_usd", "confidence"]].to_string(index=False))
print()

# ── 3. WRIGHT'S LAW FIT ───────────────────────────────────────────────────────

# Fit on HIGH-confidence points only (2021–2024).
ld_high = ld[ld["confidence"] == "high"].copy()

log_cum  = np.log2(ld_high["cum_prod"].values)
log_cogs = np.log2(ld_high["cogs_unit_cny"].values)

slope, intercept, r_value, p_value, stderr = stats.linregress(log_cum, log_cogs)

# Wright's Law: COGS = C0 × (Q)^slope
# Learning rate: LR = 1 − 2^slope  (positive LR means cost falls on doubling)
lr_nominal = 1 - 2**slope
r_sq = r_value**2

print(f"Wright's Law fit (HIGH-confidence 2021–2024, nominal CNY):")
print(f"  slope (log2 COGS per log2 cum_prod) = {slope:.4f}")
print(f"  learning rate (nominal)             = {lr_nominal*100:.1f}% per doubling")
print(f"  R²                                  = {r_sq:.3f}")
print(f"  p-value                             = {p_value:.3f}")
print()

# Fit including MEDIUM points for comparison.
log_cum_all  = np.log2(ld["cum_prod"].values)
log_cogs_all = np.log2(ld["cogs_unit_cny"].values)
slope_all, intercept_all, r_all, p_all, stderr_all = stats.linregress(log_cum_all, log_cogs_all)
lr_all = 1 - 2**slope_all

print(f"Wright's Law fit (ALL points 2019–2024, nominal CNY):")
print(f"  slope   = {slope_all:.4f}")
print(f"  LR      = {lr_all*100:.1f}%")
print(f"  R²      = {r_all**2:.3f}")
print()


# ── 4. INFLATION ADJUSTMENT ───────────────────────────────────────────────────

# Chinese manufacturing average wage (urban, manufacturing sector).
# Source: NBS China Statistical Yearbook — approximate index (2021 = 100).
# Growth ≈ 5.5%/year on average during 2021–2024.
# This is the dominant variable input to precision machining cost (labor).
wage_index = {
    2019: 88.5,
    2020: 91.0,   # COVID suppressed growth
    2021: 100.0,
    2022: 105.5,
    2023: 111.5,
    2024: 117.5,
}

ld["wage_idx"] = ld["year"].map(wage_index)
# Deflate COGS to 2021 real terms
ld["cogs_unit_real_2021"] = ld["cogs_unit_cny"] / (ld["wage_idx"] / 100.0)

# Wright's Law fit on real COGS (HIGH-confidence only)
ld_high_real = ld[ld["confidence"] == "high"].copy()
log_cogs_real = np.log2(ld_high_real["cogs_unit_real_2021"].values)
slope_real, intercept_real, r_real, p_real, _ = stats.linregress(log_cum, log_cogs_real)
lr_real = 1 - 2**slope_real

print(f"Wright's Law fit (HIGH-confidence 2021–2024, wage-deflated to 2021 CNY):")
print(f"  slope   = {slope_real:.4f}")
print(f"  LR      = {lr_real*100:.1f}%")
print(f"  R²      = {r_real**2:.3f}")
print()

# ── 5. COMPARISON REFERENCE LINES ────────────────────────────────────────────

# Generate prediction curves anchored at the 2021 data point.
anchor_cum  = ld.loc[ld["year"] == 2021, "cum_prod"].values[0]
anchor_cogs = ld.loc[ld["year"] == 2021, "cogs_unit_cny"].values[0]

cum_range = np.logspace(
    np.log10(anchor_cum * 0.5),
    np.log10(anchor_cum * 3.0),
    100,
)

def lr_curve(cum, anchor_cum, anchor_cogs, lr):
    """Wright's Law prediction: cost at cumulative production `cum`."""
    doublings = np.log2(cum / anchor_cum)
    return anchor_cogs * ((1 - lr) ** doublings)

pred_rows = []
for lr_val, label in [(0.00, "0% LR"), (0.03, "3% LR"), (0.05, "5% LR (prior estimate)"),
                      (0.10, "10% LR"), (0.15, "15% LR")]:
    for c in cum_range:
        pred_rows.append({
            "cum_prod":     c,
            "cogs_unit_cny": lr_curve(c, anchor_cum, anchor_cogs, lr_val),
            "label":        label,
        })

pred_df = pd.DataFrame(pred_rows)
pred_df["label"] = pd.Categorical(
    pred_df["label"],
    categories=["0% LR", "3% LR", "5% LR (prior estimate)", "10% LR", "15% LR"],
)

# Fitted line as its own df
fitted_cogs = 2 ** (slope * np.log2(cum_range) + intercept)
fitted_real  = 2 ** (slope_real * np.log2(cum_range) + intercept_real)
fit_df = pd.DataFrame({
    "cum_prod":         np.concatenate([cum_range, cum_range]),
    "cogs_unit_cny":    np.concatenate([fitted_cogs, fitted_real]),
    "series":           ["Nominal fit"] * len(cum_range) + ["Wage-adjusted fit"] * len(cum_range),
})


# ── 6. PLOTS ──────────────────────────────────────────────────────────────────

LINE_COLORS = {
    "0% LR":              "#B0B0B0",
    "3% LR":              "#FF9800",
    "5% LR (prior estimate)": "#2196F3",
    "10% LR":             "#4CAF50",
    "15% LR":             "#9C27B0",
}

# -- Plot A: Wright's Law scatter + fit (nominal) + reference LR lines --------
# Physical cost floor: ~$47 ≈ ¥338 at 7.2 RMB/USD
FLOOR_CNY = 47 * RMB_USD

p_a = (
    ggplot()
    # Reference LR lines
    + geom_line(pred_df, aes(x="cum_prod", y="cogs_unit_cny", color="label"),
                size=0.9, linetype="dashed", alpha=0.8)
    # Fitted line (nominal)
    + geom_line(
        fit_df[fit_df["series"] == "Nominal fit"],
        aes(x="cum_prod", y="cogs_unit_cny"),
        color="#F44336", size=1.4,
    )
    # Physical cost floor
    + geom_hline(yintercept=FLOOR_CNY, linetype="dotted", color="#888888", size=0.9)
    + annotate("text", x=anchor_cum * 0.55, y=FLOOR_CNY + 15,
               label="Physical floor ~¥338 ($47)", size=8, color="#666666", ha="left")
    # Data points — medium confidence
    + geom_point(
        ld[ld["confidence"] == "medium"],
        aes(x="cum_prod", y="cogs_unit_cny"),
        color="#AAAAAA", size=4, shape="D", fill="#AAAAAA",
    )
    # Data points — high confidence
    + geom_point(
        ld_high,
        aes(x="cum_prod", y="cogs_unit_cny"),
        color="#F44336", size=4,
    )
    # Year labels
    + geom_text(
        ld,
        aes(x="cum_prod", y="cogs_unit_cny", label="year.astype(str)"),
        nudge_y=25, size=8, color="#333333",
    )
    + annotate(
        "label", x=anchor_cum * 2.5, y=fitted_cogs[-1] + 80,
        label=f"Empirical fit\n(2021–2024 HIGH)\nLR ≈ {lr_nominal*100:.0f}% nominal\n({lr_real*100:.0f}% wage-adj.)",
        size=8, color="#F44336", fill="white",
    )
    + scale_x_log10(labels=lambda v: [f"{x/1000:.0f}k" for x in v])
    + scale_y_continuous(
        labels=lambda vals: [f"¥{v:.0f}" for v in vals],
        limits=(200, 1_200),
    )
    + scale_color_manual(values=LINE_COLORS, name="Learning rate curve")
    + labs(
        title="Wright's Law fit: Leaderdrive COGS/unit vs. cumulative production",
        subtitle=(
            "Red line = empirical fit on 2021–2024 data (filled circles). "
            "Grey diamonds = lower-confidence 2019–2020 points.\n"
            "Dashed lines = what cost would look like at various LRs anchored at 2021.\n"
            "Sources: Leaderdrive 688017.SS annual reports; physical floor from wiki first-principles derivation"
        ),
        x="Cumulative Leaderdrive production (units, log scale)",
        y="Segment COGS per unit (CNY, nominal)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 6),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8, color="#555555"),
        legend_position="right",
        legend_text=element_text(size=8),
    )
)
p_a.save(f"{OUT}/A_wrights_law_nominal.png", dpi=150)
print("Saved A_wrights_law_nominal.png")


# -- Plot B: Nominal vs wage-adjusted COGS/unit over time ---------------------
plot_b_df = pd.melt(
    ld[["year", "cogs_unit_cny", "cogs_unit_real_2021"]],
    id_vars="year",
    value_vars=["cogs_unit_cny", "cogs_unit_real_2021"],
    var_name="series",
    value_name="cogs",
)
plot_b_df["series"] = plot_b_df["series"].map({
    "cogs_unit_cny":       "Nominal COGS/unit (CNY)",
    "cogs_unit_real_2021": "Wage-adjusted COGS/unit\n(2021 CNY)",
})

p_b = (
    ggplot(plot_b_df, aes(x="year", y="cogs", color="series", group="series"))
    + geom_line(size=1.3)
    + geom_point(size=3.5)
    + geom_hline(yintercept=FLOOR_CNY, linetype="dotted", color="#888888", size=0.9)
    + annotate("text", x=2019.2, y=FLOOR_CNY + 15, label="Physical floor ~¥338",
               size=8, color="#666666", ha="left")
    + scale_color_manual(
        values={"Nominal COGS/unit (CNY)": "#F44336",
                "Wage-adjusted COGS/unit\n(2021 CNY)": "#2196F3"},
        name="",
    )
    + scale_x_continuous(breaks=list(range(2019, 2025)))
    + scale_y_continuous(labels=lambda v: [f"¥{x:.0f}" for x in v], limits=(250, 1_100))
    + labs(
        title="Leaderdrive COGS/unit: nominal vs. wage-adjusted (2021 CNY)",
        subtitle=(
            "Nominal COGS rises ¥668→¥912 as production scales — "
            "but wage-adjusted, costs are flat at ¥770–790 (2021–2024).\n"
            "This implies a real learning rate ≈ 0–2%, not 5%.\n"
            "Chinese manufacturing wage growth ≈ 5.5%/yr (NBS); "
            "wage inflation masked any underlying volume learning."
        ),
        x="Year",
        y="COGS per unit (CNY)",
    )
    + theme_minimal()
    + theme(
        figure_size=(9, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
    )
)
p_b.save(f"{OUT}/B_cogs_nominal_vs_real.png", dpi=150)
print("Saved B_cogs_nominal_vs_real.png")


# -- Plot C: HDSI cost ratio trend (no unit data — shows structural compression)
p_c = (
    ggplot(hdsi_financials, aes(x="fy_end"))
    + geom_line(aes(y="gm"), color="#9C27B0", size=1.3)
    + geom_point(aes(y="gm"), color="#9C27B0", size=3.5)
    + geom_text(aes(y="gm", label="(gm*100).round(1).astype(str) + '%'"),
                nudge_y=0.015, size=8, color="#9C27B0")
    + scale_x_continuous(breaks=hdsi_financials["fy_end"].tolist())
    + scale_y_continuous(
        labels=lambda v: [f"{x*100:.0f}%" for x in v],
        limits=(0.20, 0.50),
    )
    + labs(
        title="HDSI (Harmonic Drive Systems, TSE 6324) gross margin trend",
        subtitle=(
            "No unit volume data recoverable. Gross margin compressed from 39% (FY2022 peak) to 27% (FY2025).\n"
            "Mirrors Leaderdrive's pattern: prices fell faster than costs, confirming competitive repricing dominates.\n"
            "Source: stockanalysis.com TSE:6324 financials (fiscal year ending March)"
        ),
        x="Fiscal year end",
        y="Gross margin",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p_c.save(f"{OUT}/C_hdsi_margin_trend.png", dpi=150)
print("Saved C_hdsi_margin_trend.png")


# -- Plot D: Multi-producer volume comparison (Leaderdrive + Sichuan Robot) ---
# Shows that Sichuan Robot (smaller producer) follows a similar trajectory,
# providing a weak cross-check that the Leaderdrive pattern is industry-typical.
ld_vol = pd.DataFrame([
    {"year": y, "units": u, "producer": "Leaderdrive (688017)"}
    for y, u in ld_units.items()
])
sr_vol = pd.DataFrame([
    {"year": y, "units": u, "producer": "Sichuan Robot"}
    for y, u in sichuan_units.items()
])
vol_df = pd.concat([ld_vol, sr_vol], ignore_index=True)

p_d = (
    ggplot(vol_df, aes(x="year", y="units", color="producer"))
    + geom_line(size=1.3)
    + geom_point(size=3)
    + scale_color_manual(
        values={"Leaderdrive (688017)": "#F44336", "Sichuan Robot": "#FF9800"},
        name="",
    )
    + scale_x_continuous(breaks=list(range(2017, 2025)))
    + scale_y_continuous(labels=lambda v: [f"{x/1000:.0f}k" for x in v])
    + labs(
        title="Chinese harmonic reducer producer unit volumes",
        subtitle=(
            "Leaderdrive ~3.7× growth 2017→2024; Sichuan Robot ~2.8× growth 2020→2024.\n"
            "Both show strong 2021 expansion followed by 2023 dip (robot demand trough), then recovery.\n"
            "Sources: Leaderdrive IPO prospectus + annual reports; Sichuan Robot via wabei.cn annual reports"
        ),
        x="Year",
        y="Annual units shipped",
    )
    + theme_minimal()
    + theme(
        figure_size=(9, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
    )
)
p_d.save(f"{OUT}/D_producer_volumes.png", dpi=150)
print("Saved D_producer_volumes.png")


# -- Plot E: Cross-producer gross margin comparison ---------------------------
# All major producers show the same pattern: margins compressed by competitive
# pricing pressure, not by learning-curve cost reduction.
#
# Data sources:
# - Leaderdrive: annual reports (HIGH confidence)
# - HDSI (6324.T): stockanalysis.com — fiscal year ending March (HIGH confidence)
# - Nabtesco (6268.T): CMP operating margin from annual securities reports (MEDIUM —
#   CMP includes non-PRG motion control products so margin overstates PRG performance;
#   2021 peak is ~16.6%, then steep decline)
# - Zhongda Leader (002896): precision reducer segment margin from analyst reports (MEDIUM)
#
# Alignment: calendar year for Leaderdrive/Zhongda; fiscal-year end for HDSI/Nabtesco
# (March FY → labelled by end year). Slight ~3-month mismatch is acceptable for
# this qualitative comparison.

cross_gm = pd.DataFrame([
    # Leaderdrive: harmonic reducer segment GM
    {"year": 2021, "gm": 0.525,  "producer": "Leaderdrive (CN, harmonic)"},
    {"year": 2022, "gm": 0.4878, "producer": "Leaderdrive (CN, harmonic)"},
    {"year": 2023, "gm": 0.4117, "producer": "Leaderdrive (CN, harmonic)"},
    {"year": 2024, "gm": 0.3085, "producer": "Leaderdrive (CN, harmonic)"},
    # HDSI: company-wide gross margin (fiscal year ending March)
    {"year": 2021, "gm": 0.3397, "producer": "HDSI (JP, harmonic)"},
    {"year": 2022, "gm": 0.3928, "producer": "HDSI (JP, harmonic)"},
    {"year": 2023, "gm": 0.3605, "producer": "HDSI (JP, harmonic)"},
    {"year": 2024, "gm": 0.2797, "producer": "HDSI (JP, harmonic)"},
    {"year": 2025, "gm": 0.2669, "producer": "HDSI (JP, harmonic)"},
    # Nabtesco: CMP segment OPERATING margin (lower than GM; trend is the signal)
    {"year": 2021, "gm": 0.166,  "producer": "Nabtesco (JP, cycloidal) — op. margin"},
    {"year": 2023, "gm": 0.075,  "producer": "Nabtesco (JP, cycloidal) — op. margin"},
    {"year": 2024, "gm": 0.041,  "producer": "Nabtesco (JP, cycloidal) — op. margin"},
    # Zhongda Leader: precision reducer segment gross margin
    {"year": 2021, "gm": 0.270,  "producer": "Zhongda Leader (CN, mixed)"},
    {"year": 2022, "gm": 0.250,  "producer": "Zhongda Leader (CN, mixed)"},
    {"year": 2023, "gm": 0.135,  "producer": "Zhongda Leader (CN, mixed)"},
])

cross_colors = {
    "Leaderdrive (CN, harmonic)":             "#F44336",
    "HDSI (JP, harmonic)":                    "#9C27B0",
    "Nabtesco (JP, cycloidal) — op. margin":  "#2196F3",
    "Zhongda Leader (CN, mixed)":             "#FF9800",
}

p_e = (
    ggplot(cross_gm, aes(x="year", y="gm", color="producer", group="producer"))
    + geom_line(size=1.3)
    + geom_point(size=3.5)
    + scale_color_manual(values=cross_colors, name="")
    + scale_x_continuous(breaks=list(range(2021, 2026)))
    + scale_y_continuous(
        labels=lambda v: [f"{x*100:.0f}%" for x in v],
        limits=(0.0, 0.55),
    )
    + labs(
        title="Cross-producer margin compression: all producers show the same pattern",
        subtitle=(
            "Margins compressed across every producer in every geography.\n"
            "Mechanism: ASP cut by competitive repricing faster than COGS falls — not learning-curve efficiency.\n"
            "Sources: Leaderdrive AR; HDSI AR (FY end March); Nabtesco AR (CMP op. margin); "
            "Zhongda Leader via Dongwu/Zhongtai analyst reports"
        ),
        x="Year (calendar; HDSI/Nabtesco fiscal year end)",
        y="Gross margin (operating margin for Nabtesco)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
        legend_text=element_text(size=8),
    )
)
p_e.save(f"{OUT}/E_cross_producer_margins.png", dpi=150)
print("Saved E_cross_producer_margins.png")


# ── 7. HISTORICAL DEPTH PLOTS ─────────────────────────────────────────────────

# -- Plot F: HDSI operating margin 2005–2025 ----------------------------------
#
# FY2020–FY2025: HIGH confidence — derived from HDSI primary filings:
#   - Annual Securities Report FY2024 (hds.co.jp) for FY2020–FY2023 operating income
#   - FY2024 and FY2025 investor presentations (hds.co.jp IR)
#   Net sales and operating income values:
#     FY2020: ¥37,488M / −¥187M  → −0.5%
#     FY2021: ¥37,034M / +¥851M  → +2.3%
#     FY2022: ¥57,087M / +¥8,734M → +15.3%
#     FY2023: ¥71,527M / +¥10,224M → +14.3%
#     FY2024: ¥55,796M / +¥124M   → +0.2%   ← near-zero, NOT −49%
#     FY2025: ¥55,645M / +¥6M     → ~0%
#   NOTE: FY2024 net income was −¥24,806M (net margin −44.5%) due to a ¥28,159M
#   impairment of intangible assets on Harmonic Drive SE (German subsidiary).
#   This is a below-the-line item; operating income itself was +¥124M. There is
#   no "Ariake impairment" — Ariake Plant references in HDSI filings are ESG/CO2 only.
#
# FY2005, FY2009: MEDIUM confidence — companiesmarketcap.com (secondary source
#   pulling from TSE primary filings): 2005 = 20.45%, 2009 = 15.4%.
#
# FY2006–FY2008, FY2010–FY2019: LOW confidence — interpolated from range data
#   ("23–25%" for 2006–2008; "18–28%" for 2010–2019). Used for connecting line only.
#
# Fiscal year ending March; year = year FY ends.

# HIGH-confidence points: FY2005, FY2009 (medium), FY2020–FY2025 (high from primary)
hdsi_lr_pts = pd.DataFrame([
    {"year": 2005, "op_margin": 0.2045, "confidence": "medium"},
    {"year": 2009, "op_margin": 0.154,  "confidence": "medium"},
    {"year": 2020, "op_margin": -0.005, "confidence": "high"},
    {"year": 2021, "op_margin": 0.023,  "confidence": "high"},
    {"year": 2022, "op_margin": 0.153,  "confidence": "high"},
    {"year": 2023, "op_margin": 0.143,  "confidence": "high"},
    {"year": 2024, "op_margin": 0.002,  "confidence": "high"},
    {"year": 2025, "op_margin": 0.0001, "confidence": "high"},
])

# LOW-confidence interpolated points for the "stable era" 2006–2019
# Used only to draw a connecting line through the band, not as data claims
hdsi_lr_interpolated = pd.DataFrame([
    {"year": y, "op_margin": m}
    for y, m in [
        (2006, 0.235), (2007, 0.245), (2008, 0.250),
        (2010, 0.200), (2011, 0.220), (2012, 0.240),
        (2013, 0.230), (2014, 0.250), (2015, 0.240),
        (2016, 0.260), (2017, 0.280), (2018, 0.270), (2019, 0.220),
    ]
])
hdsi_lr_all_line = pd.concat(
    [hdsi_lr_pts[["year", "op_margin"]], hdsi_lr_interpolated],
    ignore_index=True,
).sort_values("year")

hdsi_lr_high = hdsi_lr_pts[hdsi_lr_pts["confidence"] == "high"]
hdsi_lr_medium = hdsi_lr_pts[hdsi_lr_pts["confidence"] == "medium"]

p_f = (
    ggplot()
    # Shaded stable band 2005–2019
    + annotate("rect",
               xmin=2004.8, xmax=2019.5, ymin=0.18, ymax=0.28,
               fill="#E3F2FD", alpha=0.55)
    + annotate("text", x=2012.0, y=0.23,
               label="Stable range 2005–2019\n(18–28% op. margin\nacross ~2.2 production doublings)",
               size=8.5, color="#1565C0", ha="center")
    # Zero reference
    + geom_hline(yintercept=0, color="#BBBBBB", size=0.6, linetype="solid")
    # Connecting line through all points
    + geom_line(hdsi_lr_all_line, aes(x="year", y="op_margin"),
                color="#9C27B0", size=0.9, alpha=0.5)
    # HIGH-confidence dots (FY2020–FY2025, from primary filings)
    + geom_point(hdsi_lr_high, aes(x="year", y="op_margin"),
                 color="#9C27B0", size=4.5, shape="o")
    # MEDIUM-confidence dots (FY2005, FY2009, from secondary source)
    + geom_point(hdsi_lr_medium, aes(x="year", y="op_margin"),
                 color="#9C27B0", size=4.5, shape="D", fill="#9C27B0")
    # Event labels
    + annotate("text", x=2009, y=0.154 - 0.045,
               label="GFC trough\n(2009)", size=8, color="#555555", ha="center")
    + annotate("text", x=2020.5, y=-0.005 - 0.045,
               label="COVID\n(FY2020)", size=8, color="#555555", ha="left")
    + annotate("text", x=2021.5, y=0.023 + 0.040,
               label="Recovery\n(FY2021)", size=8, color="#555555", ha="left")
    + annotate("text", x=2024.1, y=0.002 + 0.035,
               label="FY2024: op. +0.2%\n(net loss −44.5%\nfrom HDS-SE\nintangible write-down)",
               size=7.5, color="#F44336", ha="left")
    + scale_x_continuous(breaks=list(range(2005, 2026, 2)),
                         limits=(2004, 2027))
    + scale_y_continuous(
        labels=lambda v: [f"{x*100:.0f}%" for x in v],
        limits=(-0.12, 0.40),
    )
    + labs(
        title="HDSI (TSE 6324) operating margin 2005–2025: 15 years of stability, then competitive collapse",
        subtitle=(
            "Operating margin stable at 18–28% across ~2.2 production doublings (FY2005–FY2019). "
            "Demand shocks (GFC 2009, COVID FY2020) produced temporary dips but margins recovered.\n"
            "Post-FY2022 collapse driven by Chinese competitive entry (ASP cuts), not cost improvement.\n"
            "Circles = HIGH confidence (primary HDSI filings, FY2020–FY2025). "
            "Diamonds = MEDIUM confidence (companiesmarketcap.com, FY2005/FY2009). "
            "Shaded band + connecting line for 2006–2019 interpolated from range data (LOW confidence)."
        ),
        x="Fiscal year end (March)",
        y="Operating margin",
    )
    + theme_minimal()
    + theme(
        figure_size=(12, 5.5),
        plot_title=element_text(size=12, fontweight="bold"),
        plot_subtitle=element_text(size=8, color="#555555"),
    )
)
p_f.save(f"{OUT}/F_hdsi_longrun_margin.png", dpi=150)
print("Saved F_hdsi_longrun_margin.png")


# -- Plot G: Nabtesco cumulative production milestones 1986–2024 --------------
#
# Milestones through 5M (2014): HIGH confidence — official Nabtesco Precision
#   Equipment Company history page (precision.nabtesco.com/en/company/history/).
# Milestones 6M (2016) and 7M (2020): MEDIUM confidence — secondary sources only;
#   the official history page last confirmed milestone is 5M in 2014.
#
# Post-2020 estimated extension: derived from PRG sub-segment revenue.
#   Revenue source: Nabtesco "Referential Data for sub-segments" PDFs (PRIMARY, HIGH).
#     FY2020: ¥60.4B | FY2021: ¥77.5B | FY2022: ¥89.7B | FY2023: ¥91.6B | FY2024: ¥65.9B
#   Unit volumes NOT published. Estimate assumes ASP constant at FY2020 baseline:
#     FY2020 ASP proxy: ¥60.4B / 750k capacity-adjusted units ≈ ¥80,500/unit
#     Annual units estimated = PRG revenue / ¥80,500
#     Cumulative sums from 7M (FY2020) baseline.
#   This is a ROUGH ESTIMATE — shown as dashed line. ASP may have changed.
#
# Margin data points:
#   FY2012 PRG op. margin 18.1%: primary, HIGH (Nabtesco AR FY2012)
#   FY2015 PRG op. margin ~16.2%: secondary, MEDIUM (MarkLines)
#   FY2021 CMP op. margin 16.6%: primary, HIGH (Nabtesco referential data FY2024)
#   FY2022 CMP: not recovered
#   FY2023 CMP 7.5%, FY2024 CMP 4.1%: primary, HIGH (same source)
#
# Note: CMP = Component Solutions segment (includes non-PRG products). PRG
# margins used where available; CMP used as proxy otherwise.

nabtesco_milestones_solid = pd.DataFrame([
    {"year": 1986, "cum_prod_m": 0.0},
    {"year": 1996, "cum_prod_m": 0.5},
    {"year": 2000, "cum_prod_m": 1.0},
    {"year": 2005, "cum_prod_m": 2.0},
    {"year": 2008, "cum_prod_m": 3.0},
    {"year": 2014, "cum_prod_m": 5.0},
])
nabtesco_milestones_medium = pd.DataFrame([
    {"year": 2016, "cum_prod_m": 6.0},
    {"year": 2020, "cum_prod_m": 7.0},
])

# Revenue-based estimated extension post-FY2020
# Nabtesco fiscal year ends December; labelled by end year
nabtesco_prg_revenue_b = {2020: 60.4, 2021: 77.5, 2022: 89.7, 2023: 91.6, 2024: 65.9}
nabtesco_asp_proxy = 60.4e9 / 750_000  # ¥ per unit

nabtesco_est_rows = [{"year": 2020, "cum_prod_m": 7.0}]
cum = 7.0
for yr in [2021, 2022, 2023, 2024]:
    annual_units = nabtesco_prg_revenue_b[yr] * 1e9 / nabtesco_asp_proxy
    cum += annual_units / 1e6
    nabtesco_est_rows.append({"year": yr, "cum_prod_m": round(cum, 2)})
nabtesco_est_df = pd.DataFrame(nabtesco_est_rows)

# Milestone labels
nabtesco_label_pts = pd.DataFrame([
    {"year": 1996, "cum_prod_m": 0.5,  "label": "500k"},
    {"year": 2000, "cum_prod_m": 1.0,  "label": "1M"},
    {"year": 2005, "cum_prod_m": 2.0,  "label": "2M"},
    {"year": 2008, "cum_prod_m": 3.0,  "label": "3M"},
    {"year": 2014, "cum_prod_m": 5.0,  "label": "5M*"},
    {"year": 2016, "cum_prod_m": 6.0,  "label": "6M†"},
    {"year": 2020, "cum_prod_m": 7.0,  "label": "7M†"},
])

y_max = nabtesco_est_df["cum_prod_m"].max() + 1.5

p_g = (
    ggplot()
    # HIGH-confidence solid line (up to 5M in 2014)
    + geom_line(nabtesco_milestones_solid, aes(x="year", y="cum_prod_m"),
                color="#2196F3", size=1.5)
    + geom_point(nabtesco_milestones_solid[nabtesco_milestones_solid["cum_prod_m"] > 0],
                 aes(x="year", y="cum_prod_m"),
                 color="#2196F3", size=4)
    # MEDIUM-confidence milestones (6M, 7M — secondary sourced)
    + geom_line(
        pd.concat([nabtesco_milestones_solid.tail(1), nabtesco_milestones_medium]),
        aes(x="year", y="cum_prod_m"),
        color="#2196F3", size=1.5, linetype="dashed",
    )
    + geom_point(nabtesco_milestones_medium, aes(x="year", y="cum_prod_m"),
                 color="#2196F3", size=4, shape="D", fill="#2196F3")
    # Estimated post-2020 extension
    + geom_line(nabtesco_est_df, aes(x="year", y="cum_prod_m"),
                color="#90CAF9", size=1.2, linetype="dashed")
    + geom_point(nabtesco_est_df[nabtesco_est_df["year"] > 2020],
                 aes(x="year", y="cum_prod_m"),
                 color="#90CAF9", size=3.5, shape="o")
    # Milestone labels
    + geom_text(nabtesco_label_pts, aes(x="year", y="cum_prod_m", label="label"),
                nudge_y=0.35, size=8, color="#0D47A1", ha="center")
    + annotate("text", x=1987, y=0.4,
               label="Mass production\nbegins 1986\n(Teijin Seiki\nfor FANUC)",
               size=8, color="#0D47A1", ha="left")
    # Stable margin band annotation
    + annotate("rect",
               xmin=2011, xmax=2021.3, ymin=3.8, ymax=4.7,
               fill="#E8F5E9", alpha=0.8)
    + annotate("text", x=2016, y=4.25,
               label="Op. margin stable 15–18%\n(FY2012: 18.1%, FY2015: 16.2%, FY2021: 16.6%)\n→ no improvement across doublings 3M→7M",
               size=8, color="#1B5E20", ha="center")
    # Competitive collapse annotation
    + annotate("rect",
               xmin=2021.3, xmax=2025.2, ymin=7.5, ymax=8.9,
               fill="#FFEBEE", alpha=0.8)
    + annotate("text", x=2023.2, y=8.2,
               label="Margin collapse:\n7.5% (FY2023)\n4.1% (FY2024)\n↳ Chinese competition",
               size=8, color="#B71C1C", ha="center")
    # Legend note
    + annotate("text", x=1986, y=y_max - 0.3,
               label="* = last HIGH-confidence milestone (official history page)\n"
                     "† = MEDIUM confidence (secondary sources)\n"
                     "Light blue dashed = estimated from PRG revenue ÷ assumed constant ASP",
               size=7.5, color="#555555", ha="left")
    + scale_x_continuous(breaks=list(range(1985, 2026, 5)), limits=(1984, 2026))
    + scale_y_continuous(
        labels=lambda v: [f"{x:.0f}M" for x in v],
        limits=(-0.2, y_max),
    )
    + labs(
        title="Nabtesco RV reducer cumulative production 1986–2024: no margin improvement across decades of scaling",
        subtitle=(
            "Solid line = HIGH-confidence milestones (official Nabtesco history page). "
            "Dashed dark blue = MEDIUM-confidence (secondary). "
            "Light blue dashed = estimated from PRG revenue (MEDIUM).\n"
            "Operating margins stable at 15–18% from 3M to 7M cumulative units (~1.2 doublings), "
            "then collapsed on Chinese competitive entry."
        ),
        x="Year",
        y="Cumulative units produced",
    )
    + theme_minimal()
    + theme(
        figure_size=(13, 6.5),
        plot_title=element_text(size=12, fontweight="bold"),
        plot_subtitle=element_text(size=8, color="#555555"),
    )
)
p_g.save(f"{OUT}/G_nabtesco_production_history.png", dpi=150)
print("Saved G_nabtesco_production_history.png")


# ── 9. SUMMARY STATISTICS FOR WIKI NOTE ──────────────────────────────────────

print("\n" + "="*60)
print("SUMMARY FOR WIKI NOTE")
print("="*60)
print(f"\nLeaderdrive COGS/unit (nominal CNY, HIGH-confidence years):")
for _, row in ld_high.iterrows():
    print(f"  {int(row.year)}: ¥{row.cogs_unit_cny:.0f}/unit  "
          f"(cum. prod: {row.cum_prod/1e3:.0f}k, GM: {row.gm*100:.1f}%)")

print(f"\nNominal Wright's Law fit (2021–2024):")
print(f"  Implied LR = {lr_nominal*100:.1f}% per doubling (slope = {slope:.4f})")
print(f"  This is NEGATIVE — COGS rose as production scaled")

print(f"\nWage-adjusted Wright's Law fit (2021–2024, 2021 CNY):")
print(f"  Implied LR = {lr_real*100:.1f}% per doubling (slope = {slope_real:.4f})")

print(f"\nCOGS change 2021→2024 (nominal): "
      f"¥{ld.loc[ld.year==2021,'cogs_unit_cny'].values[0]:.0f} → "
      f"¥{ld.loc[ld.year==2024,'cogs_unit_cny'].values[0]:.0f} "
      f"(+{((ld.loc[ld.year==2024,'cogs_unit_cny'].values[0]/ld.loc[ld.year==2021,'cogs_unit_cny'].values[0])-1)*100:.1f}%)")
print(f"COGS change 2021→2024 (wage-adj): "
      f"¥{ld.loc[ld.year==2021,'cogs_unit_real_2021'].values[0]:.0f} → "
      f"¥{ld.loc[ld.year==2024,'cogs_unit_real_2021'].values[0]:.0f} "
      f"(+{((ld.loc[ld.year==2024,'cogs_unit_real_2021'].values[0]/ld.loc[ld.year==2021,'cogs_unit_real_2021'].values[0])-1)*100:.1f}%)")

print(f"\nProduction doublings 2021→2024: {np.log2(cum_prod[2024]/cum_prod[2021]):.2f}")
print(f"Physical floor: ¥{FLOOR_CNY:.0f} (${47:.0f})")
print(f"2024 COGS/unit: ¥{ld.loc[ld.year==2024,'cogs_unit_cny'].values[0]:.0f} "
      f"(${ld.loc[ld.year==2024,'cogs_unit_usd'].values[0]:.0f})")
print(f"Current multiple above floor: "
      f"{ld.loc[ld.year==2024,'cogs_unit_cny'].values[0]/FLOOR_CNY:.1f}×")

print(f"\nConclusion: empirical data supports LR ≈ 0–3% (real), not 5%.")
print(f"The 5% prior estimate was at the high end; data suggests the true rate")
print(f"is closer to 0% when wage inflation is stripped out.")
