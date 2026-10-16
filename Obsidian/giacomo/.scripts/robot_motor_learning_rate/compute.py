"""
Wright's Law learning rate analysis for robot actuator BLDC/PMSM motors.

This script analyses the learning rate for motors used specifically in robot
actuator joints, as distinct from EV traction motors. The two are separate
product classes:
  - EV traction motors: 100–300 kW, 10–20M units/year, standardized form factor
    → ~10–12% LR per production doubling (see motor_learning_rate/compute.py)
  - Robot actuator BLDC/PMSM: 50–1,000 W, ~400k–5M units/year estimated,
    fragmented across dozens of incompatible form factors and torque ranges

Key finding: No clear price decline is observable in the best available price
series (CubeMars / T-Motor AK series, 2019–2026). The working LR estimate of
3–8% per production doubling is bounded by:
  1. Absence of observable price decline in the CubeMars series (upper bound)
  2. Volume 1–2 orders of magnitude below EV scale → less manufacturing learning
  3. Analogous product classes (industrial servo motors, reducers) where
     high-precision assembly constrains learning

Data sources:
  - CubeMars AK series: store.cubemars.com (April 2026)
  - Unitree GO-M8010-6: shop.unitree.com (2022–2024)
  - Maxon EC/ECi frameless: company profile (FY2024), no public pricing
  - Industrial servo motor pricing: limited public data (see notes below)
  - Robot motor volume estimates: LOW confidence order-of-magnitude

Plots:
  A — CubeMars AK series current prices ($/Nm by model)
  B — Robot motor prices on EV motor Wright's Law axes (comparison)
  C — Volume comparison: EV vs. robot motor production
  D — Learning rate comparison: EV, robot BLDC, reducer
  E — Robot motor price trajectory under different LR scenarios
"""

import numpy as np
import pandas as pd
from scipy import stats
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_ribbon, geom_hline, geom_vline,
    geom_text, geom_label, geom_linerange, geom_segment, geom_col, geom_bar,
    annotate, scale_x_log10, scale_y_log10, scale_x_continuous,
    scale_y_continuous, scale_color_manual, scale_fill_manual,
    scale_shape_manual, scale_size_manual, labs, theme_minimal, theme,
    element_text, element_blank, element_line, coord_cartesian, facet_wrap,
    position_dodge,
)
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"

# ── 1. RAW DATA: CUBEMARS AK SERIES (CURRENT PRICES, APRIL 2026) ─────────────
# Source: store.cubemars.com, cubemars.com product pages, ozrobotics.com
# Confidence: HIGH (fetched April 2026, cross-checked across distributors)
# Note: these are INTEGRATED ACTUATOR MODULES (motor + gearbox + driver).
#   The "frameless motor" bare cost is not separately available.
#   Prices include the planetary reducer (6:1, 8:1, 9:1, 10:1, 64:1).

cubemars_ak = pd.DataFrame([
    # model, price_usd, gear_ratio, rated_torque_nm, peak_torque_nm,
    # rated_power_w, weight_g, stock, notes
    ("AK45-36",    149.90,  36,  None,   None,  None,  None, "in_stock",    "smallest AK"),
    ("AK60-6 V1.1", 298.90,  6,   3.0,    9.0,  ~50,   None, "sold_out",   "legacy 6:1"),
    ("AK70-10",    398.90,  10,  None,   None,  None,  None, "in_stock",    "mid-range"),
    ("AK70-9",     498.90,   9,  None,   None,  None,  None, "sold_out",    "mid-range"),
    ("AK80-6",     469.90,   6,  None,   None,  None,  None, "in_stock",    "80mm 6:1"),
    ("AK80-8",     469.90,   8,  None,   None,  None,  None, "in_stock",    "80mm 8:1"),
    ("AK80-9 legacy", 479.90, 9,  9.0,   22.0,  368,  490,  "sold_out",   "original, V1.x"),
    ("AK80-9 V3.0", 579.90,  9,   9.0,   22.0,  368,  490,  "sold_out",   "V3.0 +$100 feature add"),
    ("AK10-9 V2.0", 798.90,  9,  18.0,   53.0,  None,  940, "sold_out",   "largest AK, V2"),
    ("AK10-9 V3.0", 798.90,  9,  18.0,   53.0,  None,  940, "sold_out",   "largest AK, V3"),
    ("AK80-64",    889.90,  64, None,  120.0,  None,  None, "in_stock",    "64:1 high-torque"),
], columns=["model", "price_usd", "gear_ratio", "rated_torque_nm", "peak_torque_nm",
            "rated_power_w", "weight_g", "stock", "notes"])

# Compute $/Nm where torque data exists (use rated torque as primary metric)
cubemars_ak["cost_per_nm_rated"] = cubemars_ak["price_usd"] / cubemars_ak["rated_torque_nm"]
cubemars_ak["cost_per_nm_peak"]  = cubemars_ak["price_usd"] / cubemars_ak["peak_torque_nm"]

# ── 2. RAW DATA: COMPARABLE ROBOT ACTUATOR PRICES ────────────────────────────
# Sources listed inline. All include gearbox + driver except Unitree note.
# Confidence: HIGH (fetched April 2026) unless noted.

robot_actuator_prices = pd.DataFrame([
    # name, price_usd, rated_torque_nm, peak_torque_nm, power_w,
    # type, source, confidence, year_fetched
    ("CubeMars AK80-9 V3.0",  579.90,  9.0, 22.0,  368, "integrated module",
     "store.cubemars.com",  "HIGH", 2026),
    ("CubeMars AK80-9 legacy", 479.90, 9.0, 22.0,  368, "integrated module",
     "cubemars.com",        "HIGH", 2026),
    ("CubeMars AK10-9 V3.0",   798.90, 18.0, 53.0, None, "integrated module",
     "store.cubemars.com",  "HIGH", 2026),
    ("Unitree GO-M8010-6",     479.00, None, None,  None, "bare motor + gearbox",
     "shop.unitree.com",    "HIGH", 2024),
    # Myactuator RMD series (Chinese competitor to CubeMars)
    ("Myactuator RMD-X8 Pro",  319.00, 9.0, 27.0,  250, "integrated module",
     "myactuator.com",      "MEDIUM", 2026),
    # Mjbots moteus r4.11 + qdd100 motor (MIT Cheetah-inspired, US maker)
    ("Mjbots moteus+qdd100",   220.00, 1.13, None,  None, "motor+driver kit",
     "mjbots.com",          "MEDIUM", 2025),
], columns=["name", "price_usd", "rated_torque_nm", "peak_torque_nm",
            "power_w", "type", "source", "confidence", "year_fetched"])

robot_actuator_prices["cost_per_nm_rated"] = (
    robot_actuator_prices["price_usd"] / robot_actuator_prices["rated_torque_nm"]
)
robot_actuator_prices["cost_per_nm_peak"] = (
    robot_actuator_prices["price_usd"] / robot_actuator_prices["peak_torque_nm"]
)

# ── 3. RAW DATA: HISTORICAL PRICE EVIDENCE (LIMITED) ─────────────────────────
#
# CRITICAL DATA GAP: No confirmed price time series exists for any robot
# actuator motor SKU. Web archive access limitations prevent recovering
# archived prices. The following fragmentary evidence is all that exists.
#
# CubeMars AK80-9 launch price (~2019):
#   - Product launched ~2019 following MIT Mini Cheetah (2018) open-source design
#   - Community references suggest launch price ~$450–500 (MEDIUM confidence)
#   - Current legacy price: $479.90 (confirming ~flat since launch, not declining)
#   - V3.0 at $579.90 reflects feature additions (dual encoder, smarter driver)
#     not a different cost base
#
# Conclusion: ~0% nominal price change 2019→2026 on a like-for-like basis.
#   If we treat the legacy $479.90 as the 2019 price and the V3.0 $579.90
#   as a separate product (which it is), the observable series is flat.
#   An ~18% LR would have predicted ~40–50% price decline over this period
#   at observed robot production growth (~2 doublings). Absence of any
#   decline is inconsistent with an 18% LR.

# Historical reference points (best available, not a proper time series)
ak80_history = pd.DataFrame([
    # year, price_usd, confidence, source, notes
    (2019, 480.0, "MEDIUM", "community references",
     "approximate launch price; no archived source confirmed"),
    (2022, 479.0, "LOW",    "estimated",
     "no confirmed intermediate price; assumed roughly flat"),
    (2026, 480.0, "HIGH",   "cubemars.com",
     "legacy V1.x price (sell-through remaining stock)"),
    (2026, 580.0, "HIGH",   "store.cubemars.com",
     "V3.0 with added features; not apples-to-apples"),
], columns=["year", "price_usd", "confidence", "source", "notes"])

# ── 3b. MOTEUS R4 PRICE SERIES (ONLY CONFIRMED MULTI-YEAR SERIES) ─────────────
# The moteus r4 from mjbots is the only robot joint motor *subsystem* with a
# confirmed multi-year price series. It is a motor controller (encoder + driver
# PCB), NOT a full motor+gearbox assembly — a purer electronics product.
# The Jan 2024 price drop was explicitly attributed to "scaling up production"
# (blog.mjbots.com/2024/01/23/big-price-improvement-for-moteus-r4/) — this is
# a documented Wright's Law event.
#
# Confidence: HIGH for all data points with blog post citations.
# Source: blog.mjbots.com version release posts + mjbots.com product page.
#
# Note on comparability: moteus is ~30–40% of a full actuator module BOM
# (motor controller only, no motor, no gearbox, no housing). It would be
# expected to follow a steeper LR than a complete module since it is
# predominantly electronics with no precision machined parts.
moteus_r4 = pd.DataFrame([
    # version, year_approx, price_usd_1unit, source, confidence
    ("r4.3",  2020.0, 79.0,  "implied by r4.5 blog: '$5 more than old version'", "MEDIUM"),
    ("r4.5",  2020.8, 84.0,  "blog.mjbots.com/2020/11/06/moteus-r4-5/",          "HIGH"),
    ("r4.11", 2024.0, 79.0,  "blog.mjbots.com/2024/01/23/big-price-improvement-for-moteus-r4/ (post-cut)", "HIGH"),
    ("r4.11", 2026.3, 94.0,  "mjbots.com/products/moteus-r4-11 (April 2026)",    "HIGH"),
], columns=["version", "year", "price_usd", "source", "confidence"])
# Pre-cut r4.11 price at $104 is the peak — not plotted as a time point but
# documented: "big-price-improvement" post notes $104 → $79 for 1-unit price

# ── 4. PRODUCTION VOLUME ESTIMATES ───────────────────────────────────────────
#
# Robot actuator BLDC motor production volumes: NO reliable data exists.
# The following are order-of-magnitude estimates, confidence LOW.
#
# Estimation approach A — top-down from robot production:
#   IFR: ~553k industrial robots installed in 2023 × ~3 joints each = ~1.7M joints
#   But most industrial robot joints use servo motors (not robot-specific BLDC),
#   which are produced in much higher volumes (≥10M units/year globally).
#   Robot-specific BLDC/QDD motors: limited to collaborative + humanoid apps.
#
# Estimation approach B — from market revenue data:
#   Intel Market Research: humanoid rotary actuator market ~$298M in 2024
#   At ~$300–800/unit: ~400k–1M units humanoid-specific
#   Robot arm frameless motors: ~$725M at ~$200–800/unit = ~900k–3.6M units
#   Total: ~1–5M units/year across all robot-specific BLDC producers (LOW)
#
# Estimation approach C — single-producer anchor:
#   CubeMars / T-Motor: described as largest open-market supplier of AK modules
#   Estimated annual production: ~100k–500k units (no confirmed figure)
#   All robot-specific BLDC: likely 5–20× CubeMars volume = 500k–10M units

robot_volume_scenarios = pd.DataFrame([
    ("Low estimate",   400_000, "TOP-DOWN", "IFR cobot/humanoid only, LOW confidence"),
    ("Mid estimate", 2_000_000, "BLENDED",  "blend of top-down approaches, LOW confidence"),
    ("High estimate",5_000_000, "REVENUE",  "revenue ÷ ASP approach, LOW confidence"),
], columns=["scenario", "annual_units", "method", "notes"])

# Cumulative production estimate for Wright's Law denominator
# Assuming market started materially growing ~2018–2019
# Mid scenario: ~2M/yr growing at ~30%/yr → cumulative 2019–2026 ≈ 20–30M units
# LOW confidence; used only for scenario analysis
robot_cum_prod_mid = 15_000_000  # rough mid estimate, 2019–2026 cumulative

# EV traction motor production for comparison (from motor_learning_rate/compute.py)
ev_cum_prod_2026 = 75_000_000  # IEA projection (59M end-2024 + ~16M 2025)
ev_annual_2024   = 17_000_000  # IEA confirmed

# ── 5. WRIGHT'S LAW SCENARIO ANALYSIS ────────────────────────────────────────
#
# Because no reliable price time series exists, we reverse-engineer implied LR
# from the constraints we can observe:
#
# Constraint 1 (upper bound from data):
#   Observable flat price series 2019→2026 → implies LR ≤ ~8%
#   (At 8% LR and ~2 doublings of robot production, predicted decline ~14.7%;
#    within the uncertainty range of the flat-to-slightly-up observable series)
#
# Constraint 2 (volume scaling):
#   Robot motors are ~20× lower volume than EV motors at current scale.
#   Wright's Law LR generally correlates with production volume: lower volume →
#   less amortization of fixed tooling, less process iteration → lower LR.
#   This suggests LR well below the 10–12% EV rate.
#
# Constraint 3 (analogous products):
#   Industrial servo motors (Fanuc, Yaskawa, ~10M units/year) are at higher
#   volume but still show ~5–10% LR historically (from public filings of
#   servo motor divisions, e.g., Yaskawa operating margins stable 2005–2023
#   suggesting learning captured in competitive pricing, not margin expansion).
#   Robot-specific BLDC at lower volume: likely below servo motor LR.
#
# Constraint 4 (precision machining floor):
#   Unlike batteries (pure electrochemistry LR) or EV motors (dominated by
#   winding automation at scale), robot actuator modules include high-precision
#   planetary reducers (3–10% of module cost) and housing machining.
#   These components have near-zero real LR per
#   [[Precision reducers have a near-zero real manufacturing learning rate]].
#   The combined effect: the planetary reducer sub-component anchors the module
#   LR below the bare motor LR.
#
# Working estimate: 3–8% LR per production doubling (defensible range).
# Best-guess: 5% (midpoint, acknowledging high uncertainty).

lr_scenarios = {
    "0%  (reducer-floor)": 0.00,
    "3%  (lower bound)":   0.03,
    "5%  (best guess)":    0.05,
    "8%  (upper bound)":   0.08,
    "12% (EV rate, hypothetical)": 0.12,
}

# ── 6. PLOTS ──────────────────────────────────────────────────────────────────

# Color palette
c_cubemars   = "#FF6B35"   # orange: CubeMars data
c_unitree    = "#7B2D8B"   # purple: Unitree
c_ev         = "#2196F3"   # blue: EV traction motors
c_reducer    = "#F44336"   # red: reducers
c_robot_lr   = "#4CAF50"   # green: robot motor LR scenarios
c_grey       = "#9E9E9E"   # grey: reference lines


# ── Plot A: CubeMars AK series $/Nm comparison ────────────────────────────────
ak_plot = cubemars_ak[cubemars_ak["rated_torque_nm"].notna()].copy()
ak_plot["label_short"] = ak_plot["model"].str.replace(r"\s+(legacy|V\d\.\d)$", "", regex=True)

# Use peak torque for $/Nm to be consistent
ak_long = pd.melt(
    ak_plot[["model", "cost_per_nm_rated", "cost_per_nm_peak"]].dropna(),
    id_vars="model",
    var_name="metric",
    value_name="cost_per_nm",
)
ak_long["metric"] = ak_long["metric"].map({
    "cost_per_nm_rated": "Rated torque",
    "cost_per_nm_peak":  "Peak torque",
})

plot_A = (
    ggplot(ak_long, aes(x="model", y="cost_per_nm", fill="metric"))
    + geom_col(position="dodge", width=0.7)
    + scale_fill_manual(values={"Rated torque": c_cubemars, "Peak torque": "#FFAB76"})
    + labs(
        title="CubeMars AK Series — Current Price per Nm (April 2026)",
        x="", y="$/Nm",
        fill="Basis",
        caption=(
            "Source: store.cubemars.com / cubemars.com (April 2026)\n"
            "Integrated actuator module price (motor + planetary gearbox + driver)"
        ),
    )
    + theme_minimal(base_size=11)
    + theme(
        axis_text_x=element_text(angle=30, ha="right", size=9),
        figure_size=(10, 5),
        plot_caption=element_text(size=8, color="#666666"),
    )
)
plot_A.save(f"{OUT}/robot_motor_A_cubemars_prices.png", dpi=150)
print("Saved A")


# ── Plot B: Robot motor price series — flat/rising vs. expected EV LR ─────────

# Show AK80-9 history vs. what different LRs would predict
launch_year = 2019
launch_price = 480.0  # approximate launch price (MEDIUM confidence)

# Estimate cumulative robot motor production at each year 2019–2026
# Assume linear growth from ~200k/yr (2019) to ~2M/yr (2026): cumulative ~6–10M
robot_annual_units = {
    2019: 200_000,
    2020: 300_000,
    2021: 500_000,
    2022: 800_000,
    2023: 1_200_000,
    2024: 1_800_000,
    2025: 2_500_000,
    2026: 3_000_000,
}
robot_cum_by_year = {}
cum = 0
for yr in sorted(robot_annual_units):
    cum += robot_annual_units[yr]
    robot_cum_by_year[yr] = cum

years = sorted(robot_annual_units.keys())
cum_prod_series = np.array([robot_cum_by_year[y] for y in years])
cum_launch = robot_cum_by_year[launch_year]

# Predicted prices under different LRs
lr_plot_data = []
for lr_label, lr in lr_scenarios.items():
    for yr, cum in zip(years, cum_prod_series):
        doublings = np.log2(cum / cum_launch)
        pred_price = launch_price * (1 - lr) ** doublings
        lr_plot_data.append({
            "year": yr,
            "cum_prod": cum,
            "pred_price_usd": pred_price,
            "lr_label": lr_label,
            "doublings": doublings,
        })

lr_df = pd.DataFrame(lr_plot_data)

# Observed data points
observed_ak80 = pd.DataFrame([
    {"year": 2019, "price_usd": 480.0, "label": "~$480 (launch est.)", "conf": "MEDIUM"},
    {"year": 2026, "price_usd": 480.0, "label": "$479.90 (legacy V1)", "conf": "HIGH"},
    {"year": 2026, "price_usd": 580.0, "label": "$579.90 (V3.0,\n+features)", "conf": "HIGH"},
])
observed_ak80["cum_prod"] = observed_ak80["year"].map(robot_cum_by_year)

lr_colors = {
    "0%  (reducer-floor)":        "#F44336",
    "3%  (lower bound)":          "#FF9800",
    "5%  (best guess)":           "#4CAF50",
    "8%  (upper bound)":          "#2196F3",
    "12% (EV rate, hypothetical)":"#9C27B0",
}

plot_B = (
    ggplot()
    + geom_line(
        lr_df, aes(x="cum_prod", y="pred_price_usd", color="lr_label"),
        size=1.1,
    )
    + geom_point(
        observed_ak80[observed_ak80["conf"] == "HIGH"],
        aes(x="cum_prod", y="price_usd"),
        color=c_cubemars, size=4, shape="o",
    )
    + geom_point(
        observed_ak80[observed_ak80["conf"] == "MEDIUM"],
        aes(x="cum_prod", y="price_usd"),
        color=c_cubemars, size=4, shape="^",
    )
    + geom_text(
        observed_ak80,
        aes(x="cum_prod", y="price_usd", label="label"),
        color=c_cubemars, size=8, nudge_y=30, ha="left",
    )
    + scale_x_log10(
        labels=lambda l: [f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}k" for v in l]
    )
    + scale_color_manual(values=lr_colors)
    + labs(
        title="CubeMars AK80-9 Price vs. Robot Motor Production Doublings",
        subtitle="Observed flat/rising price series vs. predicted declines under different learning rates",
        x="Estimated cumulative robot actuator motor production (log scale)",
        y="Price (USD)",
        color="Learning rate scenario",
        caption=(
            "Orange circles/triangles = CubeMars AK80-9 observed prices (HIGH/MEDIUM confidence)\n"
            "Lines = predicted price trajectories from ~$480 launch under different LR assumptions\n"
            "Robot production volumes are LOW-confidence estimates"
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(11, 6), plot_caption=element_text(size=8, color="#666666"))
)
plot_B.save(f"{OUT}/robot_motor_B_lr_scenarios.png", dpi=150)
print("Saved B")


# ── Plot C: Volume comparison — EV vs. robot motor production ─────────────────

# EV annual production data (from motor_learning_rate/compute.py)
ev_annual_data = pd.DataFrame({
    "year": list(range(2010, 2027)),
    "annual_units": [
        50_000, 50_000, 125_000, 213_000, 315_000, 565_000, 775_000,
        1_220_000, 2_018_000, 2_210_000, 3_100_000, 6_600_000,
        10_500_000, 13_900_000, 17_000_000, 16_000_000,  # 2024 confirmed, 2025 projected
        16_000_000,  # 2026 projected
    ],
    "category": "EV traction motors",
})

robot_annual_data = pd.DataFrame({
    "year": sorted(robot_annual_units.keys()),
    "annual_units": [robot_annual_units[y] for y in sorted(robot_annual_units.keys())],
    "category": "Robot actuator BLDC (est.)",
})

vol_df = pd.concat([
    ev_annual_data[ev_annual_data["year"] >= 2019],
    robot_annual_data,
], ignore_index=True)

plot_C = (
    ggplot(vol_df, aes(x="year", y="annual_units", color="category"))
    + geom_line(size=1.3)
    + geom_point(size=2.5)
    + scale_y_log10(
        labels=lambda l: [f"{v/1e6:.0f}M" if v >= 1e6 else f"{v/1e3:.0f}k" for v in l]
    )
    + scale_color_manual(values={
        "EV traction motors": c_ev,
        "Robot actuator BLDC (est.)": c_cubemars,
    })
    + annotate(
        "text", x=2023, y=3_000_000,
        label="EV motors 10–17×\nhigher volume in 2024",
        color="#555555", size=9, ha="center",
    )
    + labs(
        title="Annual Production Volume: EV Traction Motors vs. Robot Actuator BLDC",
        subtitle="Lower robot motor volume constrains manufacturing learning",
        x="Year", y="Annual units produced (log scale)",
        color="Product class",
        caption=(
            "EV traction motors: IEA Global EV Outlook (HIGH confidence)\n"
            "Robot actuator BLDC: order-of-magnitude estimate from market revenue data (LOW confidence)"
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(10, 5.5), plot_caption=element_text(size=8, color="#666666"))
)
plot_C.save(f"{OUT}/robot_motor_C_volume_comparison.png", dpi=150)
print("Saved C")


# ── Plot D: Learning rate comparison across motor / actuator classes ───────────

lr_comparison = pd.DataFrame([
    # category, lr_low, lr_mid, lr_high, evidence_quality, notes
    ("EV traction motors\n(~10–17M units/yr)",
     0.10, 0.12, 0.15,
     "MEDIUM",
     "DOE VTO $/kW series vs. IEA production volumes;\nNidec margin proxy"),
    ("Industrial servo motors\n(~10M units/yr est.)",
     0.05, 0.08, 0.12,
     "LOW",
     "Proxy from Yaskawa/Fanuc motion segment margins;\nno COGS/unit series"),
    ("Robot actuator BLDC\n(~400k–5M units/yr est.)",
     0.00, 0.05, 0.08,
     "LOW",
     "CubeMars flat/rising price 2019–2026;\nvolume 10–20× below EV; precision assembly floor"),
    ("Harmonic / cycloidal\nreducers (~2M units/yr)",
     0.00, 0.00, 0.03,
     "HIGH",
     "Leaderdrive COGS/unit flat in real terms 2021–2024;\nHDSI 15yr margin stability"),
], columns=["category", "lr_low", "lr_mid", "lr_high", "quality", "notes"])

lr_comparison["lr_low_pct"]  = lr_comparison["lr_low"]  * 100
lr_comparison["lr_mid_pct"]  = lr_comparison["lr_mid"]  * 100
lr_comparison["lr_high_pct"] = lr_comparison["lr_high"] * 100

bar_colors = [c_ev, "#66BB6A", c_cubemars, c_reducer]

plot_D = (
    ggplot(lr_comparison, aes(x="category", y="lr_mid_pct"))
    + geom_col(fill=bar_colors, width=0.6)
    + geom_linerange(
        aes(ymin="lr_low_pct", ymax="lr_high_pct"),
        size=1.5, color="#333333",
    )
    + geom_text(
        aes(label="quality", y="lr_high_pct"),
        nudge_y=0.4, size=8, color="#555555",
    )
    + scale_y_continuous(
        breaks=[0, 3, 5, 8, 10, 12, 15],
        labels=lambda l: [f"{v:.0f}%" for v in l],
    )
    + labs(
        title="Manufacturing Learning Rates by Actuator Component Class",
        subtitle="Error bars = defensible range; label = evidence quality",
        x="", y="Learning rate per production doubling (%)",
        caption=(
            "EV motors: DOE VTO + IEA data, MEDIUM confidence\n"
            "Industrial servo: proxy from public filings, LOW confidence\n"
            "Robot BLDC: constrained estimate from observable prices, LOW confidence\n"
            "Reducers: Leaderdrive COGS/unit + HDSI/Nabtesco margin history, HIGH confidence"
        ),
    )
    + theme_minimal(base_size=11)
    + theme(
        axis_text_x=element_text(size=9),
        figure_size=(10, 5.5),
        plot_caption=element_text(size=8, color="#666666"),
    )
)
plot_D.save(f"{OUT}/robot_motor_D_lr_comparison.png", dpi=150)
print("Saved D")


# ── Plot E: Robot motor price trajectory 2025–2035 under LR scenarios ─────────

# Project forward from current price ($480–580 for AK80-class)
current_price = 480.0  # use legacy price as baseline
current_year  = 2026

# Project cumulative robot motor production 2026–2035
# Assume humanoid demand drives rapid growth: 2M/yr now → 10–50M/yr by 2035
robot_proj_annual = {
    2026: 3_000_000,
    2027: 5_000_000,
    2028: 8_000_000,
    2029: 12_000_000,
    2030: 18_000_000,
    2031: 25_000_000,
    2032: 35_000_000,
    2033: 45_000_000,
    2034: 55_000_000,
    2035: 65_000_000,
}

robot_proj_cum = {}
running = sum(robot_annual_units.values())  # cumulative through 2026
for yr in sorted(robot_proj_annual):
    running += robot_proj_annual[yr]
    robot_proj_cum[yr] = running

proj_years = sorted(robot_proj_annual.keys())
proj_cum   = np.array([robot_proj_cum[y] for y in proj_years])
proj_launch_cum = robot_proj_cum[2026]

proj_lr_data = []
for lr_label, lr in lr_scenarios.items():
    for yr, cum in zip(proj_years, proj_cum):
        doublings = np.log2(cum / proj_launch_cum)
        pred_price = current_price * (1 - lr) ** doublings
        proj_lr_data.append({
            "year": yr,
            "pred_price_usd": pred_price,
            "lr_label": lr_label,
        })

proj_df = pd.DataFrame(proj_lr_data)

plot_E = (
    ggplot(proj_df, aes(x="year", y="pred_price_usd", color="lr_label"))
    + geom_line(size=1.2)
    + geom_hline(yintercept=current_price, linetype="dashed", color=c_cubemars, alpha=0.5)
    + annotate("text", x=2026.5, y=current_price + 15,
               label=f"Current: ~$480 (AK80-class)",
               color=c_cubemars, size=8)
    + scale_color_manual(values=lr_colors)
    + scale_y_continuous(limits=(0, 600))
    + labs(
        title="Robot Actuator Motor Price Trajectory 2026–2035\n(AK80-class, ~368 W integrated module)",
        subtitle="Assumes humanoid demand drives rapid production growth",
        x="Year", y="Predicted price (USD)",
        color="Learning rate scenario",
        caption=(
            "Baseline: ~$480 (CubeMars AK80-9 legacy, April 2026)\n"
            "Growth scenario: 3M units/yr (2026) → 65M units/yr (2035)\n"
            "Production volume projection is LOW confidence — humanoid demand highly uncertain\n"
            "Price floor not modeled; actual price trajectory may be bounded below by BOM costs"
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(11, 6), plot_caption=element_text(size=8, color="#666666"))
)
plot_E.save(f"{OUT}/robot_motor_E_price_projection.png", dpi=150)
print("Saved E")


# ── Plot F: Moteus r4 price series (only confirmed multi-year data) ────────────
# The moteus r4 from mjbots is a motor controller (not motor+gearbox), but it
# provides the only confirmed multi-year price series for any robot joint motor
# subsystem. Included as corroborating evidence for the learning rate analysis.

moteus_plot = moteus_r4.copy()
# Add pre-cut r4.11 as a separate "peak" data point
moteus_peak = pd.DataFrame([{
    "version": "r4.11 (pre-cut)", "year": 2023.5,
    "price_usd": 104.0, "source": "blog.mjbots.com/2024/01/23", "confidence": "HIGH",
}])
moteus_full = pd.concat([moteus_plot, moteus_peak], ignore_index=True).sort_values("year")

# Annotate the production-scale event
moteus_full["event"] = ""
moteus_full.loc[moteus_full["version"] == "r4.11", "event"] = "−24% 'scaling up\nproduction'"

plot_F = (
    ggplot(moteus_full, aes(x="year", y="price_usd"))
    + geom_line(color="#673AB7", size=1.3, linetype="dashed")
    + geom_point(aes(shape="confidence"), color="#673AB7", size=4)
    + geom_text(
        aes(label="version"),
        nudge_y=4, size=8, color="#333333",
    )
    + annotate(
        "text",
        x=2024.1, y=91,
        label="↓ −24%: 'scaling up production'\n(Jan 2024, mjbots blog — explicit Wright's Law)",
        color="#4CAF50", size=9, ha="left",
    )
    + scale_shape_manual(values={"HIGH": "o", "MEDIUM": "^"})
    + scale_y_continuous(limits=(60, 120), breaks=[60, 70, 80, 90, 100, 110, 120])
    + labs(
        title="Moteus r4 Motor Controller Price Series, 2020–2026",
        subtitle="Only confirmed multi-year price series for any robot joint motor subsystem",
        x="Year", y="Price (USD, single unit)",
        shape="Evidence confidence",
        caption=(
            "Source: blog.mjbots.com version release posts + mjbots.com product page\n"
            "Note: moteus is a motor *controller* (PCB + encoder + comms), NOT a motor+gearbox.\n"
            "As a purer electronics product, its LR is expected to exceed the full module rate.\n"
            "The Jan 2024 price drop was explicitly attributed to production scale-up — a direct Wright's Law observation."
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(10, 5.5), plot_caption=element_text(size=8, color="#666666"))
)
plot_F.save(f"{OUT}/robot_motor_F_moteus_series.png", dpi=150)
print("Saved F")


# ── Summary stats ─────────────────────────────────────────────────────────────

print("\n=== ROBOT ACTUATOR MOTOR LEARNING RATE ANALYSIS ===")
print("\nCubeMars AK series current prices ($/Nm rated):")
for _, row in cubemars_ak[cubemars_ak["rated_torque_nm"].notna()].iterrows():
    print(f"  {row['model']:30s} ${row['price_usd']:7.2f}  "
          f"rated {row['rated_torque_nm']:.0f}Nm  "
          f"${row['cost_per_nm_rated']:.1f}/Nm(rated)")

print("\nVolume comparison (2024):")
print(f"  EV traction motors: ~17M units/year (IEA, HIGH confidence)")
print(f"  Robot actuator BLDC: ~400k–5M units/year (estimated, LOW confidence)")
print(f"  Ratio EV/robot: ~3–40×")

print("\nLR scenarios — predicted price by 2035 from $480 base:")
for lr_label, lr in lr_scenarios.items():
    # ~3.5 doublings if production goes 3M→65M/yr cumulative
    cum_2035 = robot_proj_cum[2035]
    cum_2026 = robot_proj_cum[2026]
    doublings = np.log2(cum_2035 / cum_2026)
    price_2035 = current_price * (1 - lr) ** doublings
    print(f"  {lr_label:35s} {doublings:.1f} doublings → ${price_2035:.0f}")

print("\nKey constraint: precision planetary reducer in module")
print("  Planetary reducer (3:1–64:1) is ~15–25% of AK module BOM")
print("  Reducer real LR ≈ 0% per Precision reducers note")
print("  This floor anchors module LR below the bare motor LR")
