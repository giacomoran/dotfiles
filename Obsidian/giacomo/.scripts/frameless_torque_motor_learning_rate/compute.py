"""
Wright's Law learning rate analysis for frameless torque motors
(robot-actuator class — the pancake, high-pole-count, hollow-shaft BLDC
motors matched to harmonic drives in precision robot arms).

This note sits next to the outrunner-BLDC LR note:
  - Outrunner BLDC = drone-motor lineage, low-KV, large-diameter, large air gap,
    used in QDD robot actuators (CubeMars AK, Damiao, RobStride, Unitree GO).
  - Frameless torque motor = industrial-servo lineage, high-pole-count, thin
    pancake, hollow shaft, used as the motor half of harmonic-drive actuators
    in precision industrial arms and cobots (Universal Robots, Franka,
    Fanuc CR, KUKA LBR iiwa).

The two are distinct product classes with different manufacturing heritage,
different production volumes, and different learning rates. This script
analyses the frameless torque motor class alone.

Raw data sources are cited inline. Plots save to Zxtra/Assets/.
"""

import numpy as np
import pandas as pd
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_text, geom_hline,
    geom_col, geom_linerange, annotate, geom_segment,
    scale_x_log10, scale_y_log10, scale_x_continuous, scale_y_continuous,
    scale_color_manual, scale_fill_manual, scale_shape_manual,
    labs, theme_minimal, theme, element_text,
)
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"

c_kollmorgen = "#003366"
c_moog       = "#8B0000"
c_allient    = "#556B2F"
c_maxon      = "#FF8C00"
c_chinese    = "#CD5C5C"
c_outrunner  = "#4CAF50"
c_frameless  = "#7B2D8B"
c_ev         = "#2196F3"
c_reducer    = "#F44336"


# ── 1. PRODUCT CLASS TIMELINE ────────────────────────────────────────────────
# Sources:
#   - Kollmorgen history page (via web search, 2026-04-17)
#   - Moog Inc. company profile (wiki: Moog Inc. (MOG.A) — company profile)
#   - Kollmorgen company profile (wiki: Kollmorgen — company profile)
#   - Allient company profile (wiki: Allient Inc. (ALLT) — company profile)

timeline = pd.DataFrame([
    # year, event, category
    (1916, "Kollmorgen Optical founded", "company"),
    (1951, "Moog Inc. founded (East Aurora, NY)", "company"),
    (1953, "Moog electrohydraulic servovalve patent", "tech"),
    (1960, "Kollmorgen Optical + Inland Motor → Kollmorgen Corp", "company"),
    (1962, "Allied Motion (later Allient) founded", "company"),
    (1970, "Harmonic Drive SE founded (Germany)", "company"),
    (1979, "Kollmorgen Inland Motor = worldwide servo leader", "market"),
    (1983, "NdFeB magnets discovered (Sagawa/Sumitomo, GM)", "tech"),
    (1988, "NdFeB magnets in production motors", "tech"),
    (2000, "Danaher acquires Kollmorgen", "M&A"),
    (2005, "Universal Robots founded (cobot market genesis)", "market"),
    (2008, "UR5 cobot ships — first commercially successful cobot", "market"),
    (2018, "Moog acquires VUES Brno (motor mfg)", "M&A"),
    (2018, "Fortive sells Kollmorgen → Altra", "M&A"),
    (2022, "Kollmorgen TBM2G launched (cobot-specific)", "product"),
    (2023, "Altra → Regal Rexnord ($4.95B)", "M&A"),
    (2023, "Allied Motion → Allient rebrand", "company"),
    (2024, "Allient launches ElectroFlux (cobot-specific)", "product"),
    (2025, "China rare-earth export controls hit AMC margins", "market"),
], columns=["year", "event", "category"])


# ── 2. MODERN PRICE ANCHORS (2026 SNAPSHOT) ──────────────────────────────────
# Sources cited inline. All retail/list pricing where available; OEM-only
# products flagged as "quote-only".

frameless_prices_2026 = pd.DataFrame([
    # vendor, model, price_usd, peak_nm, od_mm, confidence, source
    # Kollmorgen TBM — cobot-specific, launched 2022
    ("Kollmorgen", "TBM(S)-6025-A",      None,  0.73,  60, "N/A (quote)",
     "electromate.com/tbm-s-6025-a"),
    ("Kollmorgen", "TBM(S)-7615-A",      None,  None, 76, "N/A (quote)",
     "electromate.com/tbm-s-7615-a"),
    # Moog DB Matrix frameless
    ("Moog",       "DB-1500",            None,  1.48, 38, "N/A (quote)",
     "moog.com DB-1500 datasheet"),
    ("Moog",       "DB-6000",            None,  70.6, 152, "N/A (quote)",
     "moog.com DB-6000 datasheet"),
    # Allient Megaflux — broadest catalog
    ("Allient",    "Megaflux 60mm",      None,  None, 60, "N/A (quote)",
     "allient.com Megaflux page"),
    ("Allient",    "Megaflux 310mm",     None,  181,  310, "N/A (quote)",
     "allient.com Megaflux page"),
    # Maxon EC frameless DT series
    ("Maxon",      "EC frameless DT50M", None,  None, 50, "N/A (quote)",
     "maxongroup.com DT series"),
    ("Maxon",      "EC frameless DT85L", None,  None, 85, "N/A (quote)",
     "maxongroup.com DT85L"),
    # CubeMars RI/RO — Chinese retail frameless for robot applications
    ("CubeMars",   "RI50 KV100",         114.90, None, 50, "HIGH",
     "store.cubemars.com RI series (April 2026)"),
    ("CubeMars",   "RO100 KV50",         163.90, None, 100, "HIGH",
     "store.cubemars.com RO series (April 2026)"),
    # Catalog reference (industry range estimate for Western premium)
    ("Industry",   "Premium 100mm OD (cobot joint)",  1500, 20, 100, "LOW (range)",
     "industry estimate from Kollmorgen/Moog/Allient profiles"),
    ("Industry",   "Chinese 100mm OD (commodity)",    300, 20, 100, "LOW (range)",
     "industry estimate from wiki profiles"),
], columns=["vendor", "model", "price_usd", "peak_nm", "od_mm", "confidence", "source"])


# ── 3. MARGIN-STABILITY PROXY DATA ───────────────────────────────────────────
# The frameless motor industry does not publish unit-cost or COGS/unit figures.
# The only tractable LR proxy is operating margin stability over many years
# combined with revenue growth: if cumulative production doubles with margins
# flat and prices flat, manufacturing cost must be roughly flat in real terms
# (0% real LR) OR gains are being competed away to customers (positive LR that
# does not accrue to producers). Both outcomes are consistent with a low
# producer-side manufacturing LR.
#
# Sources: Moog Inc. company profile; Kollmorgen company profile;
# Allient Inc. company profile.

moog_industrial_margin = pd.DataFrame([
    # year, revenue_musd, adj_op_margin_pct
    (2019, 918, 10.5),
    (2020, 909, 10.0),
    (2021, 892, 9.5),
    (2022, 907, 10.0),
    (2023, 983, 11.7),
    (2024, 991, 12.4),
    (2025, 956, 13.5),
], columns=["year", "revenue_musd", "margin_pct"])

allient_margin = pd.DataFrame([
    # year, revenue_musd, op_margin_pct, gross_margin_pct
    (2019, 371, None, None),
    (2020, 367, 6.4, 29.6),
    (2021, 404, 6.3, 30.0),
    (2022, 503, 6.3, 31.3),
    (2023, 579, 8.0, 29.6),
    (2024, 530, 5.7, 31.3),
    (2025, 555, 7.9, 32.8),
], columns=["year", "revenue_musd", "op_margin_pct", "gross_margin_pct"])

# Kollmorgen sits inside Regal Rexnord AMC segment — only segment-level data
rrx_amc_margin = pd.DataFrame([
    (2022, 1700, 21.0),  # pro forma pre-Altra close
    (2023, None, None),  # transition year
    (2024, 1634, 22.1),
    (2025, 1690, 20.6),  # rare earth headwind
], columns=["year", "revenue_musd", "ebitda_margin_pct"])


# ── 4. VOLUME ESTIMATES ──────────────────────────────────────────────────────
# Global frameless BLDC motor market size via Strategic Revenue Insights
# (2024 estimate ~$1.5B, 7.6% CAGR) per Allient company profile.
# Unit ASP across the industry: $500–$2,500 for Western premium, $200–$600 for
# Chinese commodity. Mid-point ASP ~$800 → 2024 units ~1.9M/year globally.
#
# Pre-robot (pre-2005) volume was dominated by aerospace gimbals, semiconductor
# equipment, and industrial servo applications — likely 200k–500k units/year
# globally in the 1990s (reportedly; LOW confidence, no authoritative series).
#
# Post-robot (2005+) cobot and humanoid applications added incremental volume
# but still small as share of total; the 2024 ~1.9M units is dominated by
# legacy industrial and semiconductor applications, not robot joints.
#
# Growth since 2005: ~4–5× over 20 years ≈ 2–2.3 cumulative doublings over
# the robot-era window, or ~5–6 doublings over the full ~60-year industry life.

frameless_volume_est = pd.DataFrame([
    # year, units_per_year_k, notes
    (1970,   20,  "aerospace gimbals + Inland Motor industrial, rough est."),
    (1980,   50,  "industrial servo expansion + semiconductor"),
    (1990,  200,  "semiconductor + industrial automation growth"),
    (2000,  500,  "cobot pre-history, industrial servo mature"),
    (2010,  800,  "cobot emerging (UR5 etc.), medical robotics"),
    (2020, 1500,  "cobot scale-up + humanoid interest"),
    (2024, 1900,  "derived from $1.5B / ~$800 ASP (LOW confidence)"),
], columns=["year", "units_k_per_year", "notes"])
frameless_volume_est["cum_units_M"] = (
    frameless_volume_est["units_k_per_year"].cumsum() / 1000
)


# ── 5. LR COMPUTATION (BOUNDED) ──────────────────────────────────────────────
# The strongest claim defensible from this data is that the frameless torque
# motor LR is *low and flat* across the NdFeB era (1985–present). Four
# supporting observations:
#
#   1. Margin stability. Moog Industrial 9.5–13.5% adjusted operating margin
#      over 7 years; Allient operating margin 5.7–8.0% over 5 years; RRX AMC
#      EBITDA margin 20–22% over 3 years. None show sustained compression
#      (inconsistent with high producer-side LR that customers are capturing)
#      or sustained expansion (inconsistent with pricing power-driven
#      LR capture). Stable margins = LR near zero in real terms.
#
#   2. Volume per SKU is small. Allient reports 12+ frameless motor series
#      × 8-650 mm diameter range = hundreds of SKUs, each selling thousands
#      to tens of thousands of units/year. Per-SKU scale is too small to
#      drive strong process learning curves on any single configuration.
#
#   3. The category is 60+ years old. By 2000, most of the easy process
#      learning from electrical steel lamination, winding automation, and
#      NdFeB material adoption had been consumed. The remaining cost-down
#      levers are small (yield on the tail, incremental BOM optimization).
#
#   4. Chinese competitive entry is a step-function, not a learning curve.
#      CubeMars RI/RO at $115–$164 for 50–100 mm frameless is an order-
#      of-magnitude-lower starting point than Kollmorgen/Moog/Allient
#      OEM quoted pricing. This is the same pattern documented in
#      Chinese-competitive-entry-has-compressed-harmonic-reducer-prices:
#      a one-time structural repricing from competitive entry, not a
#      Wright's Law effect.

lr_scenarios = {
    "0% (margin floor)": 0.00,
    "1% (low end)":      0.01,
    "3% (best guess)":   0.03,
    "5% (high end)":     0.05,
    "8% (outrunner-class, hypothetical)": 0.08,
}


# ── 6. PLOTS ──────────────────────────────────────────────────────────────────

# Plot A — industry timeline
timeline_plot = timeline.copy()
timeline_plot["y"] = range(len(timeline_plot))
cat_colors = {
    "company":  "#1976D2",
    "tech":     "#D32F2F",
    "market":   "#388E3C",
    "M&A":      "#7B1FA2",
    "product":  "#F57C00",
}

plot_A = (
    ggplot(timeline_plot, aes(x="year", y="y", color="category"))
    + geom_point(size=3.5)
    + geom_segment(aes(x="year", xend="year", y=-1, yend="y"),
                   alpha=0.2, size=0.4, color="#666666")
    + geom_text(aes(label="event"),
                nudge_x=1, size=8, ha="left", color="#333333")
    + scale_color_manual(values=cat_colors)
    + scale_x_continuous(limits=(1910, 2040),
                         breaks=list(range(1910, 2030, 10)))
    + labs(
        title="Frameless torque motor industry timeline, 1916–2025",
        subtitle="60+ years of continuous production; robot-specific SKUs are a 2020s development on a mature base",
        x="Year", y="", color="Event type",
        caption=(
            "Sources: Kollmorgen history page (web search, April 2026); "
            "Moog Inc., Kollmorgen, Allient company profiles in wiki. "
            "NdFeB magnet commercialisation enabled modern compact frameless "
            "designs around 1988; Universal Robots founded 2005 and shipped "
            "the UR5 in 2008, marking the commercial-cobot-era origin."
        ),
    )
    + theme_minimal(base_size=10)
    + theme(figure_size=(12, 8),
            axis_text_y=element_text(size=0),
            plot_caption=element_text(size=8, color="#666666"))
)
plot_A.save(f"{OUT}/frameless_A_timeline.png", dpi=150)
print("Saved A")


# Plot B — margin history across incumbents (Wright's Law proxy)
margin_long = []
for _, r in moog_industrial_margin.iterrows():
    margin_long.append({"year": r["year"], "margin": r["margin_pct"],
                        "company": "Moog Industrial (adj. op. margin)"})
for _, r in allient_margin.iterrows():
    if r["op_margin_pct"] is not None:
        margin_long.append({"year": r["year"], "margin": r["op_margin_pct"],
                            "company": "Allient (op. margin)"})
for _, r in rrx_amc_margin.iterrows():
    if r["ebitda_margin_pct"] is not None:
        margin_long.append({"year": r["year"], "margin": r["ebitda_margin_pct"],
                            "company": "RRX AMC / Kollmorgen (EBITDA margin)"})
margin_df = pd.DataFrame(margin_long)

plot_B = (
    ggplot(margin_df, aes(x="year", y="margin", color="company"))
    + geom_line(size=1.2)
    + geom_point(size=3)
    + scale_color_manual(values={
        "Moog Industrial (adj. op. margin)":       c_moog,
        "Allient (op. margin)":                    c_allient,
        "RRX AMC / Kollmorgen (EBITDA margin)":    c_kollmorgen,
    })
    + scale_x_continuous(breaks=[2019, 2020, 2021, 2022, 2023, 2024, 2025])
    + scale_y_continuous(limits=(0, 25),
                         breaks=[0, 5, 10, 15, 20, 25],
                         labels=lambda l: [f"{v:.0f}%" for v in l])
    + labs(
        title="Margin stability at Western frameless motor incumbents, 2019–2025",
        subtitle="No sustained compression or expansion — consistent with low producer-side LR",
        x="Year", y="Operating / EBITDA margin",
        color="Company / segment",
        caption=(
            "Different margin bases (Moog adj. op.; Allient GAAP op.; RRX AMC EBITDA); "
            "compare levels-within-series, not cross-company levels. "
            "A high producer-side LR with competitive pass-through would show "
            "gradual margin compression; a high LR captured as pricing power "
            "would show expansion. Neither is observed. "
            "2025 Kollmorgen/RRX dip reflects China rare-earth export controls, "
            "not manufacturing LR dynamics. Sources: company profiles in wiki."
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(11, 5.5), plot_caption=element_text(size=8, color="#666666"))
)
plot_B.save(f"{OUT}/frameless_B_margin_history.png", dpi=150)
print("Saved B")


# Plot C — modern price anchors (Chinese commodity vs. Western premium)
price_df = frameless_prices_2026.dropna(subset=["price_usd"]).copy()
price_df["label"] = price_df["vendor"] + " " + price_df["model"]

# Build a comparison with industry range estimate
range_df = pd.DataFrame([
    {"class": "Chinese commodity\n(CubeMars RI/RO)",
     "low": 115, "mid": 140, "high": 165, "note": "HIGH (listed prices)"},
    {"class": "Western premium\n(Kollmorgen TBM / Moog DB /\nAllient Megaflux)",
     "low": 500, "mid": 1500, "high": 5000, "note": "LOW (industry estimate)"},
])
range_df["y_order"] = [0, 1]

plot_C = (
    ggplot(range_df, aes(x="mid", y="class"))
    + geom_segment(aes(x="low", xend="high", y="class", yend="class"),
                   size=6, color=c_frameless)
    + geom_point(size=5, color="#333333")
    + geom_text(aes(label="note"),
                nudge_y=0.15, size=8, color="#666666")
    + scale_x_log10(labels=lambda l: [f"${v:,.0f}" for v in l])
    + labs(
        title="Frameless torque motor pricing by producer class, April 2026",
        subtitle="Chinese retail pricing is 3–15× below Western premium OEM-quoted pricing",
        x="Price per motor (USD, log scale)",
        y="",
        caption=(
            "Chinese retail range from CubeMars RI/RO listings at store.cubemars.com "
            "(HIGH confidence). Western premium range from industry estimates in "
            "Kollmorgen, Moog, and Allient company profiles — these vendors quote OEM-"
            "specific pricing and publish no list prices. The step-function difference "
            "is a Chinese-competitive-entry effect, not a Wright's Law trajectory."
        ),
    )
    + theme_minimal(base_size=11)
    + theme(figure_size=(11, 5),
            axis_text_y=element_text(size=10),
            plot_caption=element_text(size=8, color="#666666"))
)
plot_C.save(f"{OUT}/frameless_C_price_ranges.png", dpi=150)
print("Saved C")


# Plot D — LR comparison across motor classes
lr_compare = pd.DataFrame([
    ("EV traction motors\n(~17M units/yr)",
     0.10, 0.11, 0.15, "MEDIUM",
     "DOE VTO + IEA"),
    ("Outrunner BLDC\n(drone-class, ~80M/yr)\nmature phase",
     0.02, 0.04, 0.06, "LOW",
     "T-Motor U8 flat 2019–2026"),
    ("Frameless torque motor\n(robot-class, ~2M/yr)",
     0.01, 0.03, 0.05, "LOW",
     "Moog/Kollmorgen/Allient margin stability, 60-yr mature industry"),
    ("Harmonic / cycloidal\nreducers (~2M/yr)",
     0.00, 0.00, 0.03, "HIGH",
     "Leaderdrive COGS flat real"),
], columns=["category", "lr_low", "lr_mid", "lr_high", "quality", "notes"])
lr_compare["lr_low_p"]  = lr_compare["lr_low"]  * 100
lr_compare["lr_mid_p"]  = lr_compare["lr_mid"]  * 100
lr_compare["lr_high_p"] = lr_compare["lr_high"] * 100

bar_cols = [c_ev, c_outrunner, c_frameless, c_reducer]

plot_D = (
    ggplot(lr_compare, aes(x="category", y="lr_mid_p"))
    + geom_col(fill=bar_cols, width=0.6)
    + geom_linerange(aes(ymin="lr_low_p", ymax="lr_high_p"),
                     size=1.5, color="#333333")
    + geom_text(aes(label="quality", y="lr_high_p"),
                nudge_y=0.8, size=8, color="#555555")
    + scale_y_continuous(breaks=[0, 1, 3, 5, 10, 15],
                         labels=lambda l: [f"{v:.0f}%" for v in l])
    + labs(
        title="Manufacturing learning rates by motor/reducer class",
        subtitle="Frameless torque motors sit near the reducer floor, below the outrunner class",
        x="", y="Learning rate per production doubling (%)",
        caption=(
            "Labels = evidence quality. Error bars = defensible range. "
            "Frameless torque motors have a slower LR than outrunner BLDCs "
            "because (a) category is ~60 yrs old vs. ~15 yrs for outrunner "
            "drone-motor scale, (b) volume per SKU is lower, and (c) Western "
            "incumbents protect margins via customisation and switching cost."
        ),
    )
    + theme_minimal(base_size=11)
    + theme(axis_text_x=element_text(size=9),
            figure_size=(11, 5.5),
            plot_caption=element_text(size=8, color="#666666"))
)
plot_D.save(f"{OUT}/frameless_D_lr_comparison.png", dpi=150)
print("Saved D")


# ── 7. SUMMARY ────────────────────────────────────────────────────────────────
print("\n=== FRAMELESS TORQUE MOTOR LR ANALYSIS ===")
print("\nCategory history: 60+ years (Kollmorgen-Inland Motor merger 1960)")
print("Modern cobot-specific SKUs: TBM2G 2022, ElectroFlux 2024\n")

print("Moog Industrial margin range 2019–2025:")
m_range = moog_industrial_margin["margin_pct"]
print(f"  {m_range.min():.1f}% – {m_range.max():.1f}% "
      f"(range {m_range.max()-m_range.min():.1f} pp)")

print("Allient op. margin range 2020–2025:")
a_range = allient_margin["op_margin_pct"].dropna()
print(f"  {a_range.min():.1f}% – {a_range.max():.1f}% "
      f"(range {a_range.max()-a_range.min():.1f} pp)")

print("\nLR scenario projections (from Chinese-commodity $140 baseline, +1 doubling):")
for label, lr in lr_scenarios.items():
    pred = 140 * (1 - lr) ** 1.0
    print(f"  {label:38s}  ${pred:6.2f}  (−{(1-pred/140)*100:4.1f}%)")
