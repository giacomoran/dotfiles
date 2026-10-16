"""
Learning curve analysis: motors vs reducers in robot actuators.

Data sources:
- DOE VTO traction motor cost: energy.gov/sites/prod/files/2014/03/f13/ape051_miller_2013_o.pdf
  and energy.gov/sites/default/files/2024-06/EDTT_Roadmap_2023_JOG_Consensus_compliant.pdf
- Industrial robot average price: IFR / ARK Invest / Inbolt
  arkivest.com/articles/analyst-research/industrial-robot-cost-declines
  inbolt.com/resources/industrial-robot-cost-decline
- Battery (Li-ion): BNEF / OurWorldInData
- Solar PV: OurWorldInData / IRENA
- ARK Invest 50% learning rate for industrial robots:
  ark-invest.com/articles/analyst-research/industrial-robot-cost-declines
- Harmonic/cycloidal reducer: no published learning curve; structural ceiling per
  RoboStrategy 2026 (2-3x max compression regardless of volume)
"""

import numpy as np
import pandas as pd
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_col, geom_hline,
    geom_ribbon, geom_text, geom_label, geom_linerange, geom_errorbar,
    scale_x_continuous, scale_y_continuous, scale_y_log10, scale_x_log10,
    scale_color_manual, scale_fill_manual,
    labs, theme_minimal, theme, element_text, element_blank, element_line,
    coord_cartesian, facet_wrap, annotate,
)
from plotnine.themes import theme_538
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/.scripts/robot_learning_curves"

PALETTE = {
    "battery":  "#2196F3",
    "solar":    "#FF9800",
    "motor":    "#4CAF50",
    "robot":    "#9C27B0",
    "reducer":  "#F44336",
}


# ── 1. TECHNOLOGY LEARNING RATES ─────────────────────────────────────────────
# Learning rate = % cost reduction per doubling of cumulative production.
# Sources annotated inline.

learning_rates = pd.DataFrame([
    # Technology, learning_rate (%), confidence, note
    ("Li-ion battery",      18.0, "high",   "BNEF; OurWorldInData"),
    ("Solar PV",            20.0, "high",   "IRENA; OurWorldInData"),
    ("EV traction motor",   11.0, "medium", "DOE VTO: ~$19/kW (2010) → ~$7/kW (2020 target);\n~10–12% per doubling; see wiki note"),
    ("Robot actuator\nBLDC/PMSM",
                             5.5, "low",    "Estimated 3–8% range; lower volumes, SKU fragmentation,\nintegrated planetary reducer anchors module LR;\nCubeMars AK80-9 ~0% nominal change 2019–2026"),
    ("Industrial robot\n(total unit)",
                            15.0, "medium", "ARK Invest: 50% cost per doubling cumulative units;\n$46k (2010) → $21k (2024), IFR data"),
    ("Precision reducer\n(harmonic/cycloidal)",
                             5.0, "low",    "No published curve; estimated from:\n- RoboStrategy 2-3x compression ceiling total actuator\n- Reducer is largest actuator subcomponent\n- Mechanical precision limits yield gains"),
], columns=["technology", "learning_rate", "confidence", "source"])

# Colors by confidence
conf_colors = {"high": "#2196F3", "medium": "#4CAF50", "low": "#F44336"}
learning_rates["color"] = learning_rates["confidence"].map(conf_colors)
learning_rates["technology"] = pd.Categorical(
    learning_rates["technology"],
    categories=learning_rates.sort_values("learning_rate")["technology"].tolist(),
)

p1 = (
    ggplot(learning_rates, aes(x="technology", y="learning_rate", fill="confidence"))
    + geom_col(width=0.6)
    + geom_text(aes(label="learning_rate.astype(str) + '%'"), va="bottom", nudge_y=0.3, size=11, fontweight="bold")
    + scale_fill_manual(
        values={"high": "#2196F3", "medium": "#4CAF50", "low": "#F44336"},
        name="Confidence",
    )
    + labs(
        title="Learning rates by technology component",
        subtitle="% cost reduction per doubling of cumulative production\nReducer rate is estimated — no published empirical curve exists",
        x="",
        y="Learning rate (% per doubling)",
    )
    + scale_y_continuous(limits=(0, 25))
    + coord_cartesian(expand=False, ylim=(0, 25))
    + theme_minimal()
    + theme(
        figure_size=(9, 5),
        axis_text_x=element_text(size=9),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="right",
        panel_grid_major_x=element_blank(),
    )
)
p1.save(f"{OUT}/01_learning_rates.png", dpi=150)
print("Saved 01_learning_rates.png")


# ── 2. EV / ROBOT MOTOR COST TRAJECTORY (DOE VTO data) ──────────────────────
# DOE APEEM / US DRIVE targets and actuals.
# ~$19/kW baseline 2010 (pre-program actual, Miller 2013)
# $10/kW 2015 target (broadly achieved per 2017 roadmap)
# $7/kW 2020 target (Electric Drive Roadmap 2024 confirms near-achieved)
# $6/kW 2025 target (EDTT Roadmap 2023)
# $3/kW 2030 aspirational (EDTT Roadmap 2023)

motor_cost = pd.DataFrame({
    "year":  [2010, 2015, 2020, 2025, 2030],
    "cost":  [19.0, 10.0,  7.0,  6.0,  3.0],
    "type":  ["actual", "target", "target", "target", "target"],
})

p2 = (
    ggplot(motor_cost, aes(x="year", y="cost"))
    + geom_line(color="#4CAF50", size=1.2)
    + geom_point(aes(shape="type"), color="#4CAF50", size=4)
    + scale_y_continuous(limits=(0, 22))
    + scale_x_continuous(breaks=[2010, 2015, 2020, 2025, 2030])
    + annotate("text", x=2010, y=20.5, label="$19/kW\n(2010 actual)", size=8, color="#333333", ha="center")
    + annotate("text", x=2025, y=7.5,  label="$6/kW\n(2025 target)", size=8, color="#333333", ha="center")
    + annotate("text", x=2030, y=4.5,  label="$3/kW\n(2030 goal)",   size=8, color="#333333", ha="center")
    + labs(
        title="EV traction motor cost trajectory (DOE VTO)",
        subtitle="EV traction motor LR (~10–12%) is higher than robot actuator BLDC LR (~3–8%) due to 7–45× volume advantage\nSource: DOE APEEM / US DRIVE roadmaps (energy.gov)",
        x="Year",
        y="Cost ($/kW peak)",
        shape="Data type",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        legend_position="bottom",
    )
)
p2.save(f"{OUT}/02_motor_cost_trajectory.png", dpi=150)
print("Saved 02_motor_cost_trajectory.png")


# ── 3. INDUSTRIAL ROBOT AVERAGE PRICE (IFR / ARK) ────────────────────────────
# IFR: $46k (2010), $27k (2017), ~$21k (2024)
# Statista / Inbolt corroborate these figures.
# Wright's Law fit: 50% learning rate (ARK Invest), ~15% per doubling.
# Interpolated intermediate years using reported CAGR of ~-5%/yr 2010-2017,
# then flatter through 2024.

robot_price = pd.DataFrame({
    "year":  [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "price": [46000, 42500, 39200, 36200, 33400, 31000, 28800, 27000, 25500, 24200, 23200, 22500, 22000, 21700, 21350],
    "source": (["IFR/Inbolt"] * 8) + (["Inbolt/Statista"] * 7),
})

# Wright's Law trendline: P = P0 * (Q/Q0)^(-lr/log2)
# Fit line to data
from scipy.optimize import curve_fit

def wrights_law(year, p0, rate):
    """Simple time-series proxy; treat year as log-linear."""
    return p0 * np.exp(rate * (year - 2010))

popt, _ = curve_fit(wrights_law, robot_price["year"], robot_price["price"], p0=[46000, -0.05])
robot_price["fitted"] = wrights_law(robot_price["year"], *popt)

p3 = (
    ggplot(robot_price, aes(x="year", y="price"))
    + geom_line(aes(y="fitted"), color="#9C27B0", linetype="dashed", size=1, alpha=0.6)
    + geom_line(color="#9C27B0", size=1.2)
    + geom_point(color="#9C27B0", size=3)
    + annotate("text", x=2014, y=39000, label=f"~{abs(popt[1])*100:.1f}%/yr decline\n(fitted trend)", size=8, color="#9C27B0")
    + scale_y_continuous(labels=lambda x: [f"${v/1000:.0f}k" for v in x])
    + scale_x_continuous(breaks=list(range(2010, 2025, 2)))
    + labs(
        title="Industrial robot average unit price (2010–2024)",
        subtitle="ARK Invest estimates 50% cost reduction per doubling of cumulative production (~15% learning rate)\nSource: IFR, Inbolt, Statista; ARK Invest (ark-invest.com/articles/analyst-research/industrial-robot-cost-declines)",
        x="Year",
        y="Average unit price (USD)",
    )
    + theme_minimal()
    + theme(
        figure_size=(9, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
    )
)
p3.save(f"{OUT}/03_robot_price_trend.png", dpi=150)
print("Saved 03_robot_price_trend.png")


# ── 4. ACTUATOR COST DECOMPOSITION UNDER CORRECTED LEARNING RATES ────────────
# Corrected April 2026:
# - Motor LR: 3–8% (robot actuator BLDC/PMSM; NOT the EV traction 18% figure).
#   Midpoint 5.5% used for central line; range shown in subtitle.
# - Reducer LR: ~0% empirical (gear-grinding time does not compress with volume;
#   wage inflation absorbs efficiency gains — Leaderdrive data, April 2026).
# - Other: 10% (encoder, housing, braking — unchanged estimate).
#
# Baseline (today): actuator ~$300; reducer 47.5%, motor 22.5%, other 30%.

BASE_TOTAL    = 300.0
BASE_REDUCER  = BASE_TOTAL * 0.475
BASE_MOTOR    = BASE_TOTAL * 0.225
BASE_OTHER    = BASE_TOTAL * 0.30

def learning_curve(base, rate, doublings):
    """Cost after n doublings at learning_rate `rate` (0-1)."""
    return base * ((1 - rate) ** doublings)

doublings = np.arange(0, 7)  # 0 to 6 doublings (~64x production growth)

rows = []
for d in doublings:
    reducer = learning_curve(BASE_REDUCER, 0.00, d)   # ~0% empirical LR
    motor   = learning_curve(BASE_MOTOR,   0.055, d)  # 5.5% midpoint of 3–8% range
    other   = learning_curve(BASE_OTHER,   0.10, d)
    total   = reducer + motor + other
    rows.append({"doublings": d, "component": "Reducer (harmonic/cycloidal)",
                 "cost": reducer, "share": reducer / total * 100})
    rows.append({"doublings": d, "component": "Motor (BLDC/PMSM, NdFeB)",
                 "cost": motor,   "share": motor / total * 100})
    rows.append({"doublings": d, "component": "Other (encoder, housing, braking)",
                 "cost": other,   "share": other / total * 100})

decomp = pd.DataFrame(rows)
decomp["component"] = pd.Categorical(
    decomp["component"],
    categories=["Reducer (harmonic/cycloidal)", "Motor (BLDC/PMSM, NdFeB)",
                "Other (encoder, housing, braking)"],
)

comp_colors = {
    "Reducer (harmonic/cycloidal)":      "#F44336",
    "Motor (BLDC/PMSM, NdFeB)":         "#4CAF50",
    "Other (encoder, housing, braking)": "#9E9E9E",
}

p4a = (
    ggplot(decomp, aes(x="doublings", y="cost", color="component"))
    + geom_line(size=1.3)
    + geom_point(size=2.5)
    + scale_color_manual(values=comp_colors, name="")
    + scale_y_continuous(labels=lambda x: [f"${v:.0f}" for v in x])
    + scale_x_continuous(breaks=list(range(7)),
                         labels=[f"{d}×\n({2**d}x prod.)" for d in range(7)])
    + labs(
        title="Actuator cost decomposition across production doublings",
        subtitle="Corrected LRs: motor 3–8% (robot actuator BLDC, midpoint 5.5%); reducer ~0% (empirical, April 2026)\nBaseline: USD300/actuator; reducer 47.5%, motor 22.5%, other 30% — total floor ~USD234 at 6 doublings",
        x="Cumulative production doublings",
        y="Component cost (USD)",
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
p4a.save(f"{OUT}/04a_actuator_decomposition_cost.png", dpi=150)
print("Saved 04a_actuator_decomposition_cost.png")

p4b = (
    ggplot(decomp, aes(x="doublings", y="share", color="component"))
    + geom_line(size=1.3)
    + geom_point(size=2.5)
    + scale_color_manual(values=comp_colors, name="")
    + scale_x_continuous(breaks=list(range(7)),
                         labels=[f"{d}×\n({2**d}x prod.)" for d in range(7)])
    + labs(
        title="Reducer share of actuator cost grows as motor compresses",
        subtitle="Corrected LRs: motor 3–8% (robot actuator BLDC); reducer ~0% (empirical) — reducer share rises faster than prior model\nTotal cost floor ~USD234 at 6 doublings (vs. ~USD120 under the incorrect 18% motor / 5% reducer assumption)",
        x="Cumulative production doublings",
        y="Share of actuator BOM (%)",
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
p4b.save(f"{OUT}/04b_actuator_decomposition_share.png", dpi=150)
print("Saved 04b_actuator_decomposition_share.png")


# ── 5. NEODYMIUM PRICE HISTORY ────────────────────────────────────────────────
# Neodymium metal price (USD/kg), approximate annual averages.
# Sources:
# - strategicmetalsinvest.com/neodymium-prices/
# - dailymetalprice.com/neodymium.html
# - businessanalytiq.com/procurementanalytics/index/neodymium-oxide-price-index/
# - tradingeconomics.com/commodity/neodymium
# Note: Nd metal price ≈ ~1.3–1.5× Nd oxide price (oxide is ~85% of metal weight + processing).
# 2022 peak sourced from multiple reports of ~$200+/kg metal.

nd_price = pd.DataFrame({
    "year": [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "price_usd_kg": [45, 65, 55, 50, 65, 120, 210, 135, 110, 120],
    "note": ["", "", "", "", "pre-boom floor",
             "EV/wind surge", "peak (+3× vs 2020)",
             "destocking correction", "floor finding", "recovery"],
})

# Annotate key events
annotations = nd_price[nd_price["note"] != ""].copy()

p5 = (
    ggplot(nd_price, aes(x="year", y="price_usd_kg"))
    + geom_ribbon(aes(ymin=0, ymax="price_usd_kg"), fill="#F44336", alpha=0.15)
    + geom_line(color="#F44336", size=1.3)
    + geom_point(color="#F44336", size=3)
    + geom_hline(yintercept=65, linetype="dashed", color="#9E9E9E", size=0.8)
    + annotate("text", x=2016.2, y=72, label="2020 baseline (~$65/kg)", size=8, color="#9E9E9E", ha="left")
    + annotate("text", x=2022, y=220, label="~$210/kg\n(3× spike)", size=8, color="#F44336", ha="center")
    + annotate("text", x=2024.5, y=95,  label="~$110/kg\n(2024 floor)", size=8, color="#333333", ha="center")
    + scale_x_continuous(breaks=list(range(2016, 2026)))
    + scale_y_continuous(limits=(0, 240), labels=lambda x: [f"${v:.0f}" for v in x])
    + labs(
        title="Neodymium metal price (USD/kg), 2016–2025",
        subtitle="3× spike in 2021–22 driven by EV/wind demand surge; corrected in 2023 but remains well above 2020 baseline\n"
                 "Sources: Strategic Metals Invest · Daily Metal Price · Trading Economics · Adamas Intelligence",
        x="Year",
        y="Price (USD/kg)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_x=element_text(angle=45, ha="right"),
    )
)
p5.save(f"{OUT}/05_neodymium_price_history.png", dpi=150)
print("Saved 05_neodymium_price_history.png")


# ── 6. NdFeB COST SHARE vs REDUCER: WHAT MATTERS ─────────────────────────────
# Context: how much of a $300 actuator is actually NdFeB magnets?
# Unitree motor ~$60–70. Motor uses ~20–50g NdFeB (compact high-torque motor estimate).
# At $65/kg (2020): 35g × $65/kg = $2.28 NdFeB per motor
# At $210/kg (2022 peak): 35g × $210 = $7.35 NdFeB per motor
# Even at peak: NdFeB is ~$7 of a $65 motor = ~11% of motor cost, ~1.6% of $300 actuator
# Reducer: ~$142.50 (47.5% of $300)
# Ratio: reducer is ~20–60× more expensive than the NdFeB content in the motor

nd_scenarios = pd.DataFrame([
    ("NdFeB in motor\n(2020 baseline, $65/kg)", 2.28,  "#F44336"),
    ("NdFeB in motor\n(2022 peak, $210/kg)",    7.35,  "#FF5722"),
    ("Motor total\n(excl. NdFeB)",              57.72, "#4CAF50"),
    ("Reducer",                                142.50, "#B71C1C"),
    ("Other (encoder,\nhousing, braking)",      90.00, "#9E9E9E"),
], columns=["component", "cost", "color"])

nd_scenarios["component"] = pd.Categorical(
    nd_scenarios["component"],
    categories=nd_scenarios["component"].tolist()[::-1],
)

p6 = (
    ggplot(nd_scenarios, aes(x="component", y="cost", fill="component"))
    + geom_col(width=0.6, show_legend=False)
    + geom_text(aes(label="'$' + cost.round(0).astype(int).astype(str)"),
                va="bottom", nudge_y=1.5, size=9, fontweight="bold")
    + scale_fill_manual(values=dict(zip(nd_scenarios["component"], nd_scenarios["color"])))
    + coord_cartesian(ylim=(0, 165))
    + labs(
        title="NdFeB magnet cost vs reducer in a $300 actuator",
        subtitle="Even at the 2022 price spike, NdFeB is ~$7 per actuator vs ~$143 for the reducer (~20× cheaper)\n"
                 "Adamas Intelligence: 'magnet value tends to be small relative to cost of end product'\n"
                 "Motor NdFeB content estimated at ~35g per motor (compact high-torque, sintered NdFeB)",
        x="",
        y="Cost per actuator (USD)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_x=element_text(size=8),
        panel_grid_major_x=element_blank(),
    )
)
p6.save(f"{OUT}/06_ndfeb_vs_reducer_cost.png", dpi=150)
print("Saved 06_ndfeb_vs_reducer_cost.png")


# ── 7. CHINESE vs. JAPANESE REDUCER PRICE WEDGE ──────────────────────────────
# Shows the compression already achieved via competitive entry vs. what remains
# to reach the physical manufacturing floor.
#
# Data sources:
# - Japanese (HDSI) Size 17–25 China-market price: ¥3,000–4,000 (~$415–555)
#   Source: Sina Finance Jan 2025 comparison article
# - Leaderdrive retail (small-batch): ~¥2,000 (~$280)
#   Source: Sina Finance Jan 2025 / Leaderdrive pricing
# - Leaderdrive OEM volume (current): ~¥1,300–1,400 (~$180–200)
#   Source: Leaderdrive 2024 ASP implied from revenue/unit data
# - Physical cost floor (first-principles, 40Cr steel): $40–59
#   Source: wiki derivation (materials + machining + inspection + assembly + yield)
# - Leaderdrive ASP time series (2017–2024):
#   Source: Leaderdrive annual reports / analyst commentary

# -- 7a. Price level waterfall (Size 17–25 harmonic reducer) ------------------
price_levels = pd.DataFrame([
    ("Japanese (HDSI)\nChina list price\n(Size 17–25)", 485, 140, "#B71C1C", "today"),
    ("Chinese retail\n(Leaderdrive\nsmall-batch)", 280, 100, "#F44336", "today"),
    ("Chinese OEM\n(Leaderdrive\nvolume)", 190, 50,  "#FF7043", "today"),
    ("Physical\nmanufacturing\nfloor (40Cr)", 50,  18,  "#9E9E9E", "floor"),
], columns=["label", "mid", "half_range", "color", "type"])

price_levels["lo"] = price_levels["mid"] - price_levels["half_range"]
price_levels["hi"] = price_levels["mid"] + price_levels["half_range"]
price_levels["label"] = pd.Categorical(
    price_levels["label"],
    categories=price_levels["label"].tolist(),
)

p7a = (
    ggplot(price_levels, aes(x="label", y="mid", color="label"))
    + geom_point(size=5, show_legend=False)
    + geom_linerange(aes(ymin="lo", ymax="hi"), size=3, alpha=0.4, show_legend=False)
    + geom_hline(yintercept=50, linetype="dashed", color="#9E9E9E", size=0.8)
    + annotate("text", x=3.7, y=57, label="Physical floor\n~$40–59", size=8, color="#666666", ha="left")
    + annotate("text", x=0.7, y=540, label="~2× already compressed\nby competitive entry", size=8, color="#B71C1C", ha="left")
    + annotate("text", x=2.7, y=280,  label="~3–5× still above\nphysical floor", size=8, color="#FF7043", ha="left")
    + scale_color_manual(values=dict(zip(price_levels["label"], price_levels["color"])))
    + scale_y_continuous(labels=lambda x: [f"${v:.0f}" for v in x], limits=(0, 640))
    + labs(
        title="Harmonic reducer price levels: Japanese → Chinese → physical floor",
        subtitle="Size 17–25 (cobot/humanoid range). Competitive entry delivered ~2× compression; another ~3–5× remains to physical floor.\n"
                 "Sources: Sina Finance (Jan 2025) · Leaderdrive 2024 annual report · wiki first-principles floor derivation",
        x="",
        y="Price per unit (USD, approx.)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 6),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_x=element_text(size=9),
        panel_grid_major_x=element_blank(),
    )
)
p7a.save(f"{OUT}/07a_reducer_price_wedge.png", dpi=150)
print("Saved 07a_reducer_price_wedge.png")

# -- 7b. Leaderdrive ASP time series vs. 5% LR prediction ---------------------
# Leaderdrive ASP in USD (at ~7.2 RMB/USD)
leaderdrive_asp = pd.DataFrame({
    "year":  [2017,  2018,  2019,  2020,  2021,  2022,  2023,  2024],
    "asp_usd": [267,  262,  227,  219,  212,  206,  214,  183],
    "source": (["annual report"] * 6) + ["implied"] + ["estimated"],
})

# 5% learning rate prediction anchored to 2017 (as starting point)
# Production doublings: approximate from robot install growth
# 2005-08: ~115k/yr; 2017: ~380k/yr → ~1.7 doublings in ~9 years → 0.19 doublings/yr
# 2017→2024: ~7 years × 0.19 = ~1.3 doublings → 5% LR: 267 × (0.95^1.3) ≈ 250
years_pred = np.array([2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024])
doublings_per_year = 1.0 / 7.5  # one doubling every 7.5 years (empirical IFR rate)
lr_prediction = 267 * ((1 - 0.05) ** ((years_pred - 2017) * doublings_per_year))

pred_df = pd.DataFrame({
    "year": years_pred,
    "asp_usd": lr_prediction,
})

p7b = (
    ggplot()
    + geom_line(leaderdrive_asp, aes(x="year", y="asp_usd"), color="#F44336", size=1.3)
    + geom_point(leaderdrive_asp, aes(x="year", y="asp_usd"), color="#F44336", size=3)
    + geom_line(pred_df, aes(x="year", y="asp_usd"), color="#9E9E9E", linetype="dashed", size=1.2)
    + annotate("text", x=2022.3, y=175, label="Actual ASP\n(Leaderdrive)", size=9, color="#F44336", ha="left")
    + annotate("text", x=2022.3, y=255, label="~5% LR prediction\n(1 doubling / 7.5yr)", size=9, color="#777777", ha="left")
    + annotate("text", x=2023.5, y=130, label="Competitive\nrepricing", size=8, color="#333333",
               ha="left")
    + geom_hline(yintercept=50, linetype="dotted", color="#9E9E9E", size=0.8)
    + annotate("text", x=2017.1, y=57, label="Physical floor ~$40–59", size=8, color="#666666", ha="left")
    + scale_y_continuous(labels=lambda x: [f"${v:.0f}" for v in x], limits=(0, 310))
    + scale_x_continuous(breaks=list(range(2017, 2025)))
    + labs(
        title="Leaderdrive ASP vs. 5% learning rate prediction (2017–2024)",
        subtitle="Actual ASP fell faster than a 5% LR would predict — driven by competitive repricing, not process cost reduction.\n"
                 "Gross margin compressed 52% → 34% over same period, confirming prices fell faster than costs.\n"
                 "Sources: Leaderdrive 688017.SS annual reports; ~5% LR from wiki estimate anchored on IFR doubling rate",
        x="Year",
        y="ASP (USD, approx. at 7.2 RMB/USD)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_x=element_text(angle=45, ha="right"),
    )
)
p7b.save(f"{OUT}/07b_leaderdrive_asp.png", dpi=150)
print("Saved 07b_leaderdrive_asp.png")

print("\nAll plots saved to:", OUT)
