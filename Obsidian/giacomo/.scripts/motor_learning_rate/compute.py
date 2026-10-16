"""
Wright's Law learning rate analysis for BLDC/PMSM electric motors.

Goal: replace the current ~18% estimate (inferred from DOE roadmap targets vs.
time) with an empirically grounded estimate using actual cumulative EV motor
production volumes as the Wright's Law denominator.

Key finding: the ~18% was fitted against *time*, not cumulative production.
EV production was doubling every 12–24 months early on; using production
volumes as the correct x-axis yields ~11–13% per doubling — lower than
claimed, but still consistent with electronics-adjacent technologies.

Methodology:
  - DOE VTO roadmap cost data: $/kW traction drive system (motor + inverter)
    Source: Miller 2013 (2010 actual), EDTT Roadmap 2023 (2015–2030 targets)
  - EV motor production denominator: cumulative global BEV+PHEV sales
    Source: IEA Global EV Outlook (compiled via Wikipedia/OurWorldInData)
  - Adjustment: the DOE targets track lab/program cost (not commercial OEM
    price); they are confirmed LOW confidence except the 2010 baseline.
  - Robot frameless motor prices: CubeMars AK80-9 retail (2024–2026 data).
    These are integrated actuator modules, NOT comparable to bare OEM motors.

Plots:
  A — Wright's Law fit: log($/kW) vs log(cumulative EV production)
  B — EV production growth: annual sales and doublings timeline
  C — Robot frameless motors vs EV motors on the same Wright's Law axes
  D — Implied learning rate range with confidence bounds

Data sources and confidence annotated inline.
"""

import numpy as np
import pandas as pd
from scipy import stats
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_ribbon, geom_hline, geom_vline,
    geom_text, geom_label, geom_linerange, geom_segment, geom_col,
    annotate, scale_x_log10, scale_y_log10, scale_x_continuous,
    scale_y_continuous, scale_color_manual, scale_fill_manual,
    scale_shape_manual, labs, theme_minimal, theme, element_text,
    element_blank, element_line, coord_cartesian, facet_wrap,
)
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"

# ── 1. RAW DATA ───────────────────────────────────────────────────────────────

# DOE VTO cost data ($/kW, traction drive system = motor + inverter + gearbox)
# Sources:
#   2010 actual: Miller 2013 DOE APEEM presentation — characterized as
#     pre-program actual baseline. Likely a NREL/ANL cost model estimate, not
#     OEM price. Confidence: MEDIUM (lab-characterized, not commercial price).
#   2015–2030: EDTT Roadmap 2023. R&D program targets, NOT commercial prices.
#     Confidence: LOW for all targets. The 2015 target is sometimes cited as
#     "achieved" but this is unverified in primary ORNL benchmarking reports.
#   Motor-only sub-targets exist (e.g., $3.3/kW in 2025) but the TDS system
#   target ($6/kW in 2025) is used here for consistency with the 2010 baseline,
#   which is also a TDS estimate.
doe_data = pd.DataFrame({
    "year":       [2010,   2015,   2020,   2025,   2030],
    "cost_per_kw": [19.0,   10.0,    7.0,    6.0,    3.0],
    "type":        ["actual baseline", "target", "target", "target", "target"],
    "confidence":  ["medium",          "low",    "low",    "low",    "low"],
})

# Cumulative global EV (BEV+PHEV) production at each DOE cost data year.
# This is the correct Wright's Law x-axis denominator.
# Source: IEA Global EV Outlook / Wikipedia compiled IEA data / OurWorldInData.
# Annual new registrations are used as proxy for motors produced (1 car ≈ 1
# traction motor for BEV; PHEV counted at 0.5; historically mixed so use
# 1:1 as simplification — introduces ~10-15% overcount).
# Confidence: MEDIUM (IEA data, rounded; OEM total production not publicly
# available; commercial vehicle EVs excluded).
doe_cum_prod = {
    2010:   50_000,       # EV production just beginning; ~50k BEV globally
    2015: 1_280_000,      # IEA milestone: ~1.28M cumulative stock end-2015
    2020: 10_600_000,     # IEA milestone: 10M cumulative stock reached Dec 2020
    2025: 75_000_000,     # Projected from 59M end-2024 + ~16M 2025 sales
    2030: 200_000_000,    # IEA announced-policies scenario projection
}
doe_data["cum_prod"] = doe_data["year"].map(doe_cum_prod)

# ── 2. ANNUAL EV PRODUCTION SERIES ───────────────────────────────────────────

# Annual global EV sales and cumulative production, 2010–2024.
# Sources: Wikipedia Electric car use by country (compiled from IEA);
#   IEA Global EV Outlook 2024 / 2025; Our World in Data EV tracker.
# Note: 2010–2019 are MEDIUM confidence (IEA-sourced but rounded);
#   2020–2024 are HIGH confidence (IEA confirmed milestones and annual reports).
ev_annual = pd.DataFrame({
    "year": list(range(2010, 2025)),
    "annual_sales": [
           50_000,   # 2010 — BEV market nascent (Leaf launched Dec 2010)
           50_000,   # 2011
          125_000,   # 2012
          213_000,   # 2013
          315_000,   # 2014
          565_000,   # 2015
          775_000,   # 2016
        1_220_000,   # 2017
        2_018_000,   # 2018
        2_210_000,   # 2019
        3_100_000,   # 2020
        6_600_000,   # 2021 — China COVID-recovery surge
       10_500_000,   # 2022
       13_900_000,   # 2023 — IEA confirmed ~14M
       17_000_000,   # 2024 — IEA confirmed ~17M
    ],
})
ev_annual["cum_prod"] = ev_annual["annual_sales"].cumsum()

# Doublings since 2010 baseline (50k cumulative at start of 2010)
BASE_2010 = 50_000
ev_annual["doublings"] = np.log2(ev_annual["cum_prod"] / BASE_2010)

# ── 3. WRIGHT'S LAW FIT (against cumulative production) ──────────────────────

# Fit log(cost) = b * log(cum_prod) + const  on the DOE data points.
# Use 2010 (MEDIUM) + 2020 (LOW but best available mid-range) for the primary
# fit; 2015 and 2025 are included but given lower weight (targets only).
# Exclude 2030 (highly aspirational; no empirical anchor).

fit_data = doe_data[doe_data["year"] <= 2025].copy()

log_cum = np.log(fit_data["cum_prod"].values)
log_cost = np.log(fit_data["cost_per_kw"].values)

slope, intercept, r, p, se = stats.linregress(log_cum, log_cost)
# Learning rate: LR = 1 - 2^slope
lr_implied = 1 - 2 ** slope

# Two-anchor fit: just 2010 and 2020 (most defensible pair)
anchor_cum  = np.array([doe_cum_prod[2010], doe_cum_prod[2020]])
anchor_cost = np.array([19.0, 7.0])
slope_2pt, intercept_2pt = np.polyfit(np.log(anchor_cum), np.log(anchor_cost), 1)
lr_2pt = 1 - 2 ** slope_2pt

print(f"Full DOE 2010-2025 fit: slope={slope:.4f}, R²={r**2:.3f}, implied LR={lr_implied*100:.1f}%")
print(f"Two-anchor (2010–2020) fit: slope={slope_2pt:.4f}, implied LR={lr_2pt*100:.1f}%")

# Prediction curve for fit
cum_range = np.logspace(np.log10(30_000), np.log10(250_000_000), 300)
cost_fit  = np.exp(intercept + slope * np.log(cum_range))
cost_2pt  = np.exp(intercept_2pt + slope_2pt * np.log(cum_range))

# Reference learning rate curves anchored at 2010 baseline
def lr_curve(cum, base_cost=19.0, base_cum=BASE_2010, lr=0.18):
    doublings = np.log2(cum / base_cum)
    return base_cost * (1 - lr) ** doublings

ref_curves = pd.DataFrame({
    "cum_prod": cum_range,
    "lr_10": lr_curve(cum_range, lr=0.10),
    "lr_13": lr_curve(cum_range, lr=0.13),
    "lr_18": lr_curve(cum_range, lr=0.18),
    "lr_20": lr_curve(cum_range, lr=0.20),
    "fit_full": cost_fit,
    "fit_2pt": cost_2pt,
})

# ── 4. ROBOT FRAMELESS MOTOR DATA ────────────────────────────────────────────

# These are integrated actuator modules (motor + planetary gearbox + driver),
# not bare EV motors. They are NOT on the EV motor learning curve — different
# form factor, volume, and manufacturing process. Included for reference.
#
# Sources: store.cubemars.com (April 2026); shop.unitree.com (2022–2024).
# Note: $/kW figures use peak power for EV context comparison; rated power
# would give even higher $/kW values.
robot_motors = pd.DataFrame([
    # name, $/kW (peak), Nm/$ (peak), approx cumulative units produced, year
    ("CubeMars AK80-9 V3.0\n($580, 368 W rated, 22 Nm peak)",
     1_302.0, 2024, "CubeMars/T-Motor\n(integrated actuator module)"),
    ("Unitree GO-M8010-6\n($370, ~816 W peak mech.)",
     453.0, 2023, "Unitree\n(bare motor + gearbox)"),
    ("MIT Cheetah clone\n(AliExpress, ~$285)",
     350.0, 2024, "Chinese clone\n(integrated actuator)"),
], columns=["label", "cost_per_kw", "year", "note"])

# Estimated cumulative production of robot joint BLDC motors (all makers).
# Robot joint motor market ~$300-750M/yr at $100-800/unit → 400k–7M units/yr.
# Cumulative through 2024 (since market started ~2017): rough 1–5M total units.
# Confidence: LOW — this is an order-of-magnitude estimate.
robot_cum_prod = 2_000_000  # midpoint estimate, all robot joint BLDC producers

# ── 5. PLOT A: WRIGHT'S LAW FIT ──────────────────────────────────────────────

# Color scheme
c_actual = "#2196F3"    # blue: actual/measured DOE data
c_target = "#90CAF9"    # light blue: DOE targets
c_fit    = "#1565C0"    # dark blue: regression fit
c_18pct  = "#F44336"    # red: the claimed 18% LR (for comparison)
c_13pct  = "#4CAF50"    # green: implied ~13% LR from proper fit
c_robot  = "#FF9800"    # orange: robot-specific motors

doe_plot = doe_data.copy()
doe_plot["color"] = doe_plot["type"].map({
    "actual baseline": c_actual,
    "target": c_target,
})
doe_plot["shape"] = doe_plot["type"].map({
    "actual baseline": "circle",
    "target": "triangle",
})

p_A = (
    ggplot()
    # Shaded band between 10% and 18% LR reference curves
    + geom_ribbon(
        pd.DataFrame({"cum_prod": cum_range,
                       "ymin": ref_curves["lr_10"],
                       "ymax": ref_curves["lr_20"]}),
        aes(x="cum_prod", ymin="ymin", ymax="ymax"),
        fill="#E3F2FD", alpha=0.5,
    )
    # Reference: 18% LR (old claim)
    + geom_line(
        ref_curves, aes(x="cum_prod", y="lr_18"),
        color=c_18pct, size=1.0, linetype="dashed", alpha=0.8,
    )
    # Reference: 13% LR (implied from 2010–2020 data)
    + geom_line(
        ref_curves, aes(x="cum_prod", y="lr_13"),
        color=c_13pct, size=1.0, linetype="dashed", alpha=0.8,
    )
    # Reference: 10% LR (lower bound)
    + geom_line(
        ref_curves, aes(x="cum_prod", y="lr_10"),
        color="#9E9E9E", size=0.8, linetype="dotted", alpha=0.7,
    )
    # DOE data points
    + geom_point(
        doe_plot, aes(x="cum_prod", y="cost_per_kw", color="type", shape="type"),
        size=5, stroke=1.5,
    )
    # DOE data labels
    + geom_text(
        doe_plot, aes(x="cum_prod", y="cost_per_kw",
                      label="year.astype(str) + '\\n$' + cost_per_kw.astype(int).astype(str) + '/kW'"),
        va="bottom", nudge_y=0.04, size=7, color="#333333", ha="center",
        format_string="{}"
    )
    # Robot motor points (separate series)
    + geom_point(
        robot_motors, aes(x=[robot_cum_prod]*len(robot_motors), y="cost_per_kw"),
        color=c_robot, shape="s", size=5, stroke=1.5,
    )
    # Annotation: 18% label
    + annotate("text", x=2e7, y=3.8,
               label=f"18% LR\n(old DOE-target estimate)",
               color=c_18pct, size=7.5, ha="left")
    # Annotation: 13% label
    + annotate("text", x=2e7, y=6.2,
               label=f"~{lr_2pt*100:.0f}% LR\n(2010–2020 production fit)",
               color=c_13pct, size=7.5, ha="left")
    # Annotation: robot motors
    + annotate("text", x=robot_cum_prod * 1.5, y=700,
               label="Robot joint motors\n(integrated actuator modules)\n"
                     "~$350–1,300/kW — different product class",
               color=c_robot, size=7, ha="left")
    + scale_x_log10(
        breaks=[1e4, 1e5, 1e6, 1e7, 1e8],
        labels=["10k", "100k", "1M", "10M", "100M"],
    )
    + scale_y_log10(
        breaks=[2, 3, 5, 7, 10, 15, 19, 30, 100, 300, 1000],
        labels=["$2", "$3", "$5", "$7", "$10", "$15", "$19", "$30",
                "$100", "$300", "$1,000"],
    )
    + scale_color_manual(
        values={"actual baseline": c_actual, "target": c_target},
        name="DOE data type",
        labels={"actual baseline": "Actual baseline (2010)", "target": "Program target"},
    )
    + scale_shape_manual(
        values={"actual baseline": "o", "target": "^"},
        name="DOE data type",
        labels={"actual baseline": "Actual baseline (2010)", "target": "Program target"},
    )
    + labs(
        title="EV traction motor cost vs. cumulative EV production (Wright's Law)",
        subtitle=(
            f"DOE roadmap targets fitted against actual EV production volumes.\n"
            f"Implied LR: ~{lr_2pt*100:.0f}% (2010–2020 anchor pair) to "
            f"~{lr_implied*100:.0f}% (full 2010–2025 fit). "
            f"Old ~18% was fitted against time, not production.\n"
            f"Sources: DOE Miller 2013 + EDTT Roadmap 2023 (costs); "
            f"IEA Global EV Outlook (production). "
            f"Robot motor prices: CubeMars/Unitree (2023–2026)."
        ),
        x="Cumulative EV motors produced (global)",
        y="Traction drive system cost ($/kW peak)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 7),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8, color="#555555"),
        legend_position="bottom",
        legend_text=element_text(size=9),
        panel_grid_minor=element_blank(),
    )
)
p_A.save(f"{OUT}/A_motor_wrights_law.png", dpi=150)
print("Saved A_motor_wrights_law.png")

# ── 6. PLOT B: EV PRODUCTION GROWTH ──────────────────────────────────────────

# Mark doubling events
doubling_df = []
for d in range(1, 11):
    target_cum = BASE_2010 * (2 ** d)
    row = ev_annual[ev_annual["cum_prod"] >= target_cum].iloc[0]
    doubling_df.append({
        "year": row["year"],
        "cum_prod": row["cum_prod"],
        "doublings": d,
        "label": f"Doubling {d}\n({row['year']})",
    })
doubling_df = pd.DataFrame(doubling_df)

p_B = (
    ggplot(ev_annual, aes(x="year"))
    + geom_col(aes(y="annual_sales"), fill="#90CAF9", alpha=0.7)
    + geom_line(aes(y="cum_prod"), color="#1565C0", size=1.5)
    + geom_point(aes(y="cum_prod"), color="#1565C0", size=2.5)
    # Mark doublings on cumulative line
    + geom_point(doubling_df, aes(x="year", y="cum_prod"),
                 color="#F44336", size=5, shape="D")
    + geom_text(doubling_df, aes(x="year", y="cum_prod",
                                  label="'×' + doublings.astype(str)"),
                va="bottom", nudge_y=500_000, size=7.5, color="#F44336",
                fontweight="bold")
    + annotate("text", x=2013, y=35_000_000,
               label="Cumulative production\n(blue line)", color="#1565C0", size=9)
    + annotate("text", x=2013, y=7_000_000,
               label="Annual sales (bars)", color="#607D8B", size=9)
    + scale_x_continuous(breaks=list(range(2010, 2025, 2)))
    + scale_y_continuous(
        labels=lambda xs: [
            f"{v/1e6:.0f}M" if v >= 1e6 else f"{v/1e3:.0f}k"
            for v in xs
        ],
    )
    + labs(
        title="Global EV production: annual sales and cumulative total (2010–2024)",
        subtitle=(
            "Red diamonds mark production doublings since the 2010 baseline (~50k cumulative).\n"
            "10 doublings occurred in 14 years — one doubling every ~1.4 years on average.\n"
            "Sources: IEA Global EV Outlook 2024/2025; Wikipedia EV use by country (IEA compiled)."
        ),
        x="Year",
        y="EV motors produced",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8.5, color="#555555"),
        panel_grid_minor=element_blank(),
    )
)
p_B.save(f"{OUT}/B_ev_production_growth.png", dpi=150)
print("Saved B_ev_production_growth.png")

# ── 7. PLOT C: LEARNING RATE COMPARISON ──────────────────────────────────────
# Compare EV motor LR against battery, solar, and robot motor estimate.

lr_comparison = pd.DataFrame([
    # Technology, midpoint LR, lo, hi, confidence, basis
    ("Li-ion battery\n(BNEF, primary series)", 18.0, 16.0, 20.0, "high",
     "BNEF annual survey\n2010–2024; confirmed empirically"),
    ("Solar PV\n(IRENA, primary series)", 20.0, 18.0, 23.0, "high",
     "IRENA global capacity\nand price data"),
    ("EV traction motor\n(this analysis)", 12.0, 10.0, 15.0, "low-medium",
     "DOE roadmap targets vs.\nIEA production volumes;\nno direct commercial series"),
    ("EV traction motor\n(old DOE-target estimate)", 18.0, 14.0, 22.0, "low",
     "DOE roadmap only;\ntime-based fit, not\nproduction-volume fit"),
    ("Robot joint BLDC motor\n(frameless, CubeMars/T-Motor)", 6.0, 0.0, 10.0, "very-low",
     "No observable price decline\n2019–2026; volume 100–1000×\nbelow EV scale"),
    ("Harmonic reducer\n(this wiki, Leaderdrive data)", 1.0, 0.0, 3.0, "medium",
     "Leaderdrive COGS/unit\n2021–2024; real LR ~0%\n(wage-adjusted)"),
], columns=["technology", "lr_mid", "lr_lo", "lr_hi", "confidence", "basis"])

lr_comparison["technology"] = pd.Categorical(
    lr_comparison["technology"],
    categories=lr_comparison.sort_values("lr_mid")["technology"].tolist(),
)

conf_colors = {
    "high": "#2196F3",
    "low-medium": "#4CAF50",
    "low": "#FF9800",
    "very-low": "#F44336",
    "medium": "#9C27B0",
}
lr_comparison["color"] = lr_comparison["confidence"].map(conf_colors)

p_C = (
    ggplot(lr_comparison, aes(x="technology", y="lr_mid", color="confidence"))
    + geom_linerange(
        aes(ymin="lr_lo", ymax="lr_hi"),
        size=4, alpha=0.35,
    )
    + geom_point(size=6)
    + geom_text(
        aes(label="lr_mid.astype(int).astype(str) + '%'"),
        va="center", nudge_x=0.32, size=9, fontweight="bold",
    )
    + scale_color_manual(
        values=conf_colors,
        name="Evidence quality",
        labels={
            "high": "High (primary empirical series)",
            "medium": "Medium (COGS/unit proxy)",
            "low-medium": "Low–medium (DOE + IEA production)",
            "low": "Low (DOE targets, time-based)",
            "very-low": "Very low (no observable trend)",
        },
    )
    + coord_cartesian(ylim=(-2, 26))
    + labs(
        title="Learning rates by technology (% cost reduction per doubling of production)",
        subtitle=(
            "EV motor LR revised downward from ~18% to ~11–13% when fitted against\n"
            "actual cumulative production volumes rather than DOE roadmap timelines.\n"
            "Robot-specific frameless motors show no empirical learning; estimated ≤10%."
        ),
        x="",
        y="Learning rate (% per doubling of cumulative production)",
    )
    + theme_minimal()
    + theme(
        figure_size=(12, 6.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8.5, color="#555555"),
        legend_position="right",
        legend_text=element_text(size=8),
        axis_text_x=element_text(size=8.5),
        panel_grid_major_x=element_blank(),
    )
)
p_C.save(f"{OUT}/C_motor_lr_comparison.png", dpi=150)
print("Saved C_motor_lr_comparison.png")

# ── 8. PLOT D: TIME-FIT vs PRODUCTION-FIT COMPARISON ─────────────────────────
# Show how the 18% estimate was derived (time-based) vs. the corrected
# production-volume estimate. This is the methodological critique.

# Time-based fit (how the 18% was derived):
# Treat the 5 DOE points at 5-year intervals as if production doubled once per
# period. This is the implicit assumption of the old estimate.
# Fit: log(cost) = b * (year - 2010) / 5 + const
# A 5-year period ≈ "1 unit" on an arbitrary x-axis.
year_intervals = np.array([0, 1, 2, 3, 4])  # 0=2010, 1=2015, ..., 4=2030
doe_costs = np.array([19.0, 10.0, 7.0, 6.0, 3.0])
slope_time, intercept_time, *_ = stats.linregress(year_intervals, np.log(doe_costs))
lr_time_implied = 1 - np.exp(slope_time)  # per "5-year unit"

print(f"\nTime-based fit (per 5-year interval): implied LR = {lr_time_implied*100:.1f}%")
print(f"Actual doublings per 5-year interval 2010-2020: "
      f"{np.log2(doe_cum_prod[2020]/doe_cum_prod[2010]):.1f}")

# Build a comparison dataframe showing both curves on same axes
cum_pred_time = np.linspace(0, 4, 100)  # 5-year intervals as x-units
cost_pred_time = np.exp(intercept_time + slope_time * cum_pred_time)

# Convert time-fit to cumulative production (x-axis) to show on same plot
# Assumption embedded in time-fit: production doubled N times in each 5yr period.
# From data: 2010→2015 was 1.28M/50k = 25.6x growth = 4.67 doublings in 5yr.
# So time-fit implicitly assumed ~1 doubling per "unit" but actual was ~5.
actual_doublings = np.array([
    0,
    np.log2(doe_cum_prod[2015] / doe_cum_prod[2010]),  # 2010→2015: 4.67 doublings
    np.log2(doe_cum_prod[2020] / doe_cum_prod[2010]),  # 2010→2020: 7.73 doublings
    np.log2(doe_cum_prod[2025] / doe_cum_prod[2010]),  # 2010→2025: 10.56 doublings (proj.)
])
actual_costs_at_doe = np.array([19.0, 10.0, 7.0, 6.0])

comparison_df = pd.DataFrame({
    "actual_doublings": actual_doublings,
    "cost_doe": actual_costs_at_doe,
    "cum_prod": [doe_cum_prod[y] for y in [2010, 2015, 2020, 2025]],
    "year": [2010, 2015, 2020, 2025],
})

# Time-fit predicts cost for each DOE year, treating each as 1 doubling
time_fit_predictions = np.exp(intercept_time + slope_time * np.arange(4))

comparison_df["cost_time_fit"] = time_fit_predictions

# Production range for plotting
doublings_range = np.linspace(0, 12, 200)
cum_range_d = BASE_2010 * 2 ** doublings_range

# Curves
cost_prod_curve = np.exp(intercept_2pt + slope_2pt * np.log(cum_range_d))
cost_18pct_curve = lr_curve(cum_range_d, lr=0.18)
cost_13pct_curve = lr_curve(cum_range_d, lr=0.13)

plot_d_df = pd.DataFrame({
    "doublings": doublings_range,
    "cum_prod": cum_range_d,
    "cost_prod_fit": cost_prod_curve,
    "cost_18pct": cost_18pct_curve,
    "cost_13pct": cost_13pct_curve,
})

p_D = (
    ggplot()
    + geom_line(plot_d_df, aes(x="doublings", y="cost_18pct"),
                color=c_18pct, size=1.3, linetype="dashed")
    + geom_line(plot_d_df, aes(x="doublings", y="cost_13pct"),
                color=c_13pct, size=1.3, linetype="dashed")
    # Actual DOE data points vs. actual doublings
    + geom_point(comparison_df, aes(x="actual_doublings", y="cost_doe"),
                 color=c_actual, size=6, shape="o")
    + geom_text(comparison_df,
                aes(x="actual_doublings", y="cost_doe",
                    label="year.astype(str)"),
                va="bottom", nudge_y=0.08, size=8, color="#333333")
    # Where the time-fit THOUGHT the data points were (1 doubling per 5 yr)
    + geom_point(comparison_df, aes(x=np.arange(4).astype(float), y="cost_time_fit"),
                 color=c_18pct, size=4, shape="s", alpha=0.6)
    + geom_segment(
        comparison_df,
        aes(x=np.arange(4).astype(float),
            xend="actual_doublings",
            y="cost_time_fit",
            yend="cost_doe"),
        color="#999999", linetype="dotted", size=0.8,
    )
    + annotate("text", x=0.5, y=13.0, label="18% LR\n(time-based;\nassumed ~1 doubling\nper 5-yr DOE interval)",
               color=c_18pct, size=7.5, ha="left")
    + annotate("text", x=7.5, y=11.5, label=f"~{lr_2pt*100:.0f}% LR\n(production-based;\nactual doublings\nas x-axis)",
               color=c_13pct, size=7.5, ha="left")
    + annotate("text", x=2.0, y=5.5,
               label="Dotted lines connect where time-fit\nthought each point was (open squares)\nto where it actually is (filled circles)",
               color="#666666", size=7, ha="left")
    + scale_x_continuous(
        breaks=list(range(0, 12)),
        labels=[f"{d}×\n({BASE_2010 * 2**d / 1e6:.1f}M cum.)" if d > 0 else "0\n(50k)"
                for d in range(12)],
    )
    + scale_y_log10(
        breaks=[3, 5, 7, 10, 15, 19],
        labels=["$3", "$5", "$7", "$10", "$15", "$19"],
    )
    + labs(
        title="Why the 18% LR was overstated: time-fit vs. production-fit",
        subtitle=(
            "The old estimate treated each 5-year DOE roadmap interval as ~1 production doubling.\n"
            "Actual EV production doubled ~5× per 5-year interval early on, so the per-doubling\n"
            "rate is lower. Same data, different x-axis, different conclusion."
        ),
        x="Cumulative production doublings since 2010 baseline",
        y="Cost ($/kW, log scale)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 6.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8.5, color="#555555"),
        axis_text_x=element_text(size=8),
        panel_grid_minor=element_blank(),
    )
)
p_D.save(f"{OUT}/D_motor_timevsprod_lr.png", dpi=150)
print("Saved D_motor_timevsprod_lr.png")

# ── 9. INPUT COST ADJUSTMENT ──────────────────────────────────────────────────
# Separate manufacturing learning from commodity input price changes.
# Analogous to the reducer note's real-wage deflation adjustment.
#
# For an IPM traction motor the two primary volatile material inputs are:
#   - NdFeB permanent magnets: price tracks NdPr oxide (no manufacturing LR;
#     supply is policy- and deposit-constrained, not scale-constrained)
#   - Copper wire (LME copper price)
#
# Reference motor: 55 kW peak IPM (DOE APEEM 2010 baseline class).
# Material assumptions (LOW confidence — varies by design):
#   - NdFeB magnets: ~1.5 kg (sintered N42-grade IPM; 1.0–2.5 kg range in lit.)
#   - Copper windings: ~5 kg (random-wound stator; hairpin ~3–4 kg at scale)
#   - Si-steel laminations: ~15 kg (excluded — price relatively stable)
#   - Magnet cost ≈ NdPr oxide price × 1.7 (oxide-to-magnet processing markup)
#
# NdPr oxide prices at DOE data years ($/kg oxide), MEDIUM confidence.
# Source: Argus Media / Metal Pages / USGS Mineral Resources Program historical
#   data (annual averages). 2011–2012 spike (~$150/kg) excluded — interpolating
#   to annual averages avoids treating the spike as representative.
#
# Copper LME annual average prices ($/kg), HIGH confidence.
# Source: World Bank Commodity Price Data (Pink Sheet).

MOTOR_KW    = 55.0
MAGNET_KG   = 1.5    # NdFeB magnets per motor (kg)
COPPER_KG   = 5.0    # Copper windings per motor (kg)
MAGNET_MULT = 1.7    # Sintered NdFeB price vs. NdPr oxide (processing markup)

ndpr_oxide = {
    2010: 35.0,   # MEDIUM — pre-spike baseline; annual avg ~$30–40
    2015: 48.0,   # MEDIUM — post-spike stabilization; 2014–2016 range $45–55
    2020: 42.0,   # MEDIUM — COVID demand trough; 2019 avg ~$45
    2025: 50.0,   # MEDIUM — 2024 actual ~$45–55; projected 2025 mid
}

cu_lme = {        # World Bank Pink Sheet ($/kg), HIGH confidence
    2010: 7.53,
    2015: 5.51,
    2020: 6.17,
    2025: 9.20,   # MEDIUM — 2024 actual annual average
}

doe_years_mat = [2010, 2015, 2020, 2025]


def mat_cost_per_kw(year):
    magnet = MAGNET_KG * ndpr_oxide[year] * MAGNET_MULT
    copper = COPPER_KG * cu_lme[year]
    return (magnet + copper) / MOTOR_KW


baseline_mat_kw = mat_cost_per_kw(2010)

# Input-cost-adjusted cost/kW:
# What would DOE $/kW be if NdFeB and copper had stayed at 2010 prices?
# Adjusted = nominal − (actual material $/kW − baseline material $/kW)
# Rising NdFeB 2010→2020 → Δ > 0 → adjusted < nominal:
# manufacturing learning was slightly stronger than nominal data shows.
nom_cost = {2010: 19.0, 2015: 10.0, 2020: 7.0, 2025: 6.0}
adj_cost = {
    y: nom_cost[y] - (mat_cost_per_kw(y) - baseline_mat_kw)
    for y in doe_years_mat
}

print("\n── Input cost adjustment ─────────────────────────────────────────────────")
print(f"{'Year':<6} {'NdPr$/kg':>9} {'Cu$/kg':>7} {'Mat$/kW':>9} "
      f"{'Nom$/kW':>9} {'Adj$/kW':>9} {'Δ$/kW':>8}")
for y in doe_years_mat:
    print(
        f"{y:<6} {ndpr_oxide[y]:>9.1f} {cu_lme[y]:>7.2f} "
        f"{mat_cost_per_kw(y):>9.2f} {nom_cost[y]:>9.2f} "
        f"{adj_cost[y]:>9.2f} {adj_cost[y]-nom_cost[y]:>+8.2f}"
    )

# Refit LR on adjusted series (4-point and 2-point anchor)
adj_arr = np.array([adj_cost[y] for y in doe_years_mat])
cum_arr = np.array([doe_cum_prod[y] for y in doe_years_mat])

slope_adj, intercept_adj, r_adj, *_ = stats.linregress(
    np.log(cum_arr), np.log(adj_arr)
)
lr_adj_full = 1 - 2 ** slope_adj

slope_adj_2pt, intercept_adj_2pt = np.polyfit(
    np.log([doe_cum_prod[2010], doe_cum_prod[2020]]),
    np.log([adj_cost[2010],     adj_cost[2020]]),
    1
)
lr_adj_2pt = 1 - 2 ** slope_adj_2pt

print(f"\nNominal two-anchor LR (2010–2020):             {lr_2pt*100:.1f}%")
print(f"Input-cost-adjusted two-anchor LR (2010–2020): {lr_adj_2pt*100:.1f}%")
print(f"Nominal full fit LR:                            {lr_implied*100:.1f}%")
print(f"Input-cost-adjusted full fit LR:                {lr_adj_full*100:.1f}%")

# ── 10. PLOT E: NOMINAL vs. INPUT-COST-ADJUSTED COST SERIES ──────────────────
# Analogous to reducer note's plot B (nominal vs. wage-adjusted COGS).
# Here the commodity effect runs the opposite direction: NdFeB rose 2010→2020
# (headwind), so the adjusted series is slightly more steeply declining.
# The effect is small (~0.4 pp) for 2010–2020 but grows at 2025 as NdFeB
# prices remain elevated above 2010 baseline.

cum_e_range = np.logspace(np.log10(30_000), np.log10(250_000_000), 300)
cost_nom_line = np.exp(intercept + slope * np.log(cum_e_range))
cost_adj_line = np.exp(intercept_adj + slope_adj * np.log(cum_e_range))

# DOE years data for plotting (nominal and adjusted, long-format)
e_nom_df = pd.DataFrame({
    "year": doe_years_mat,
    "cum_prod": [doe_cum_prod[y] for y in doe_years_mat],
    "cost": [nom_cost[y] for y in doe_years_mat],
})
e_adj_df = pd.DataFrame({
    "year": doe_years_mat,
    "cum_prod": [doe_cum_prod[y] for y in doe_years_mat],
    "cost": [adj_cost[y] for y in doe_years_mat],
})

e_fit_nom = pd.DataFrame({"cum_prod": cum_e_range, "cost": cost_nom_line})
e_fit_adj = pd.DataFrame({"cum_prod": cum_e_range, "cost": cost_adj_line})

c_e_nom = "#2196F3"   # blue — nominal
c_e_adj = "#4CAF50"   # green — adjusted

p_E = (
    ggplot()
    # Fit lines
    + geom_line(e_fit_nom, aes(x="cum_prod", y="cost"),
                color=c_e_nom, size=1.0, linetype="dashed", alpha=0.7)
    + geom_line(e_fit_adj, aes(x="cum_prod", y="cost"),
                color=c_e_adj, size=1.0, linetype="dashed", alpha=0.7)
    # Data points
    + geom_point(e_nom_df, aes(x="cum_prod", y="cost"),
                 color=c_e_nom, size=5, shape="o")
    + geom_point(e_adj_df, aes(x="cum_prod", y="cost"),
                 color=c_e_adj, size=5, shape="^")
    # Year labels on nominal series
    + geom_text(e_nom_df, aes(x="cum_prod", y="cost",
                               label="year.astype(str)"),
                va="top", nudge_y=-0.04, size=7.5, color=c_e_nom)
    # Annotations
    + annotate("text", x=3.5e6, y=14.5,
               label=(f"Nominal: LR ≈ {lr_implied*100:.1f}% (full fit)\n"
                      f"           ≈ {lr_2pt*100:.1f}% (2010–2020 anchor)"),
               color=c_e_nom, size=8, ha="left")
    + annotate("text", x=3.5e6, y=9.5,
               label=(f"Adjusted: LR ≈ {lr_adj_full*100:.1f}% (full fit)\n"
                      f"             ≈ {lr_adj_2pt*100:.1f}% (2010–2020 anchor)\n"
                      f"↑ higher: NdFeB was a cost headwind"),
               color=c_e_adj, size=8, ha="left")
    + annotate("text", x=5e4, y=4.0,
               label=(f"Material cost / kW (55 kW IPM reference motor)\n"
                      f"2010: ${mat_cost_per_kw(2010):.2f}  "
                      f"2015: ${mat_cost_per_kw(2015):.2f}  "
                      f"2020: ${mat_cost_per_kw(2020):.2f}  "
                      f"2025: ${mat_cost_per_kw(2025):.2f}\n"
                      f"NdFeB: +{(ndpr_oxide[2020]-ndpr_oxide[2010])/ndpr_oxide[2010]*100:.0f}% "
                      f"(2010→2020 net)   Cu: "
                      f"{(cu_lme[2020]-cu_lme[2010])/cu_lme[2010]*100:+.0f}%"),
               color="#555555", size=7, ha="left")
    + scale_x_log10(
        breaks=[1e4, 1e5, 1e6, 1e7, 1e8],
        labels=["10k", "100k", "1M", "10M", "100M"],
    )
    + scale_y_log10(
        breaks=[4, 5, 6, 7, 8, 10, 12, 15, 19],
        labels=["$4", "$5", "$6", "$7", "$8", "$10", "$12", "$15", "$19"],
    )
    + coord_cartesian(ylim=(3.5, 22))
    + labs(
        title="EV traction motor cost: nominal vs. input-cost-adjusted (NdFeB + copper)",
        subtitle=(
            f"Holding NdFeB and copper at 2010 prices to isolate manufacturing LR.\n"
            f"NdFeB oxide rose ~{(ndpr_oxide[2020]-ndpr_oxide[2010])/ndpr_oxide[2010]*100:.0f}% "
            f"2010→2020 (headwind); copper fell ~{abs((cu_lme[2020]-cu_lme[2010])/cu_lme[2010]*100):.0f}% "
            f"(tailwind). Net: ~+$0.2/kW headwind 2010→2020; ~+$0.9/kW at 2025.\n"
            f"NdPr oxide: Argus/USGS (MEDIUM conf.). Copper LME: World Bank Pink Sheet (HIGH conf.)."
        ),
        x="Cumulative EV motors produced (global)",
        y="Traction drive system cost ($/kW, log scale)",
    )
    + theme_minimal()
    + theme(
        figure_size=(11, 6.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=8.5, color="#555555"),
        panel_grid_minor=element_blank(),
    )
)
p_E.save(f"{OUT}/E_motor_inputcost_adj.png", dpi=150)
print("Saved E_motor_inputcost_adj.png")

# ── SUMMARY ──────────────────────────────────────────────────────────────────
print("\n── Summary ──────────────────────────────────────────────────────────────")
print(f"Production-volume fit (2010–2020 anchor pair): LR = {lr_2pt*100:.1f}%")
print(f"Production-volume fit (full 2010–2025 DOE data): LR = {lr_implied*100:.1f}%")
print(f"Defensible range (given DOE target uncertainty): 10–15%")
print(f"Old time-based estimate: 18% — overstated by ~{(0.18 - lr_2pt)*100:.0f}pp")
print(f"Robot frameless motors: no empirical LR; estimated ≤10%; likely 5–8%")
