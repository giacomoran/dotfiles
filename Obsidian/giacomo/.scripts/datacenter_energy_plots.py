"""
Data center energy constraint & HBM price plots.

Sources documented inline. Run with:
    uv run python datacenter_energy_plots.py
"""

import pandas as pd
from plotnine import (
    ggplot, aes,
    geom_col, geom_line, geom_point, geom_hline, geom_vline,
    geom_area, geom_text, geom_rect, geom_label,
    scale_x_continuous, scale_y_continuous, scale_color_manual,
    scale_fill_manual, scale_alpha_manual,
    coord_flip,
    labs, theme_minimal, theme, element_text, element_line, element_blank,
    annotate,
    facet_wrap,
)
from plotnine.scales import scale_y_log10
import warnings
warnings.filterwarnings("ignore")

OUTPUT_DIR = "../👾 Wiki/img"


# ---------------------------------------------------------------------------
# Plot 1: US electricity generation 2010–2024 — flatness then breakout
# Source: EIA Electric Power Monthly Table 1.01 / Electric Power Annual
# https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=table_1_01
# ---------------------------------------------------------------------------

us_gen = pd.DataFrame({
    "year": [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    "twh":  [4125, 4106, 4048, 4065, 4093, 4078, 4078, 4035, 4181, 4131, 4010, 4110, 4231, 4178, 4309],
})
us_gen["era"] = us_gen["year"].apply(lambda y: "2024 breakout" if y == 2024 else "2010–2023 flat")

p1 = (
    ggplot(us_gen, aes(x="year", y="twh"))
    + geom_area(fill="#d4e6f1", alpha=0.6)
    + geom_line(color="#2e86c1", size=1.2)
    + geom_point(aes(color="era"), size=3)
    + geom_hline(yintercept=4120, linetype="dashed", color="#7f8c8d", alpha=0.5)
    + annotate("text", x=2011.5, y=4145, label="Flat band ~4,000–4,230 TWh (2010–2023)",
               color="#7f8c8d", size=8, ha="left")
    + annotate("text", x=2024, y=4325, label="4,309 TWh\n+4.5% YoY\n(all-time high)",
               color="#e74c3c", size=7, ha="right")
    + scale_x_continuous(breaks=list(range(2010, 2025, 2)))
    + scale_y_continuous(limits=[3900, 4400], labels=lambda l: [f"{int(x):,}" for x in l])
    + scale_color_manual(values={"2010–2023 flat": "#2e86c1", "2024 breakout": "#e74c3c"})
    + labs(
        title="US net electricity generation (TWh), 2010–2024",
        subtitle="13 years of stagnation; 2024 data-center-driven breakout is the first meaningful move",
        x=None, y="TWh",
        caption="Source: EIA Electric Power Monthly Table 1.01 | EIA Electric Power Annual",
        color=None,
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
        axis_line_x=element_line(color="#bdc3c7"),
    )
)
p1.save(f"{OUTPUT_DIR}/01_us_electricity_generation.png", dpi=150, width=9, height=5)
print("Saved 01_us_electricity_generation.png")


# ---------------------------------------------------------------------------
# Plot 2: Data center power density escalation (kW per rack)
# Sources:
#   Legacy / Omdia 2030: SemiAnalysis, Datacenter Anatomy Part 1 (Oct 2024)
#   https://newsletter.semianalysis.com/p/datacenter-anatomy-part-1-electrical
#   GB200 / Blackwell Ultra: Nvidia published TDPs; SemiAnalysis TCO analysis
# ---------------------------------------------------------------------------

rack_density = pd.DataFrame({
    "label": [
        "Legacy avg\n(pre-2020)",
        "Cloud\nmodern",
        "AI air-cooled\n(H100 dense)",
        "Google\ntypical",
        "Nvidia GB200\nNVL72",
        "Nvidia\nBlackwell Ultra",
    ],
    "kw": [8, 15, 35, 45, 130, 140],
    "category": [
        "Traditional", "Traditional", "AI GPU", "AI GPU", "AI GPU", "AI GPU"
    ],
})
rack_density["label"] = pd.Categorical(
    rack_density["label"], categories=rack_density["label"], ordered=True
)

p2 = (
    ggplot(rack_density, aes(x="label", y="kw", fill="category"))
    + geom_col(width=0.6)
    + geom_text(aes(label="kw"), va="bottom", nudge_y=2, size=9, format_string="{:.0f} kW")
    + scale_fill_manual(values={"Traditional": "#aed6f1", "AI GPU": "#e74c3c"})
    + scale_y_continuous(limits=[0, 160])
    + labs(
        title="Data center rack power density (kW/rack)",
        subtitle="AI GPU racks run 3–17× hotter than legacy; liquid cooling becomes mandatory above ~40 kW",
        x=None, y="kW per rack",
        caption="Source: SemiAnalysis Datacenter Anatomy Part 1 (Oct 2024); Nvidia published TDPs",
        fill=None,
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
        axis_text_x=element_text(size=8),
    )
)
p2.save(f"{OUTPUT_DIR}/02_rack_power_density.png", dpi=150, width=9, height=5)
print("Saved 02_rack_power_density.png")


# ---------------------------------------------------------------------------
# Plot 3: Grid interconnection queue vs installed US capacity
# Source: LBNL Queued Up 2025 Edition
# https://emp.lbl.gov/publications/queued-2025-edition-characteristics
# ---------------------------------------------------------------------------

grid = pd.DataFrame({
    "category": [
        "US installed\ncapacity\n(total grid)",
        "Active\ninterconnection\nqueue (generation)",
        "Active\ninterconnection\nqueue (storage)",
        "Queue: has\nagreement, not\nyet built",
    ],
    "gw": [1250, 1400, 890, 408],
    "type": ["Installed", "Queue", "Queue", "Queue"],
})
grid["category"] = pd.Categorical(
    grid["category"], categories=grid["category"], ordered=True
)

p3 = (
    ggplot(grid, aes(x="category", y="gw", fill="type"))
    + geom_col(width=0.55)
    + geom_text(aes(label="gw"), va="bottom", nudge_y=15, size=9, format_string="{:.0f} GW")
    + scale_fill_manual(values={"Installed": "#27ae60", "Queue": "#e67e22"})
    + scale_y_continuous(limits=[0, 1600])
    + labs(
        title="US grid: installed capacity vs interconnection queue (end-2024)",
        subtitle="Queue exceeds installed capacity; 77% of requests withdrawn historically; median wait now 5 years",
        x=None, y="Gigawatts (GW)",
        caption="Source: LBNL Queued Up 2025 Edition",
        fill=None,
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
        axis_text_x=element_text(size=8.5),
    )
)
p3.save(f"{OUTPUT_DIR}/03_grid_interconnection_queue.png", dpi=150, width=9, height=5)
print("Saved 03_grid_interconnection_queue.png")


# ---------------------------------------------------------------------------
# Plot 4: AI data center power demand — current vs 2030 projections
# Sources: IEA Energy and AI; Goldman Sachs; EPRI Powering Intelligence 2026
# ---------------------------------------------------------------------------

demand = pd.DataFrame({
    "scenario": [
        "US data centers\n2024 actual",
        "US data centers\n2030 (IEA base)",
        "AI-specific\nUS 2024",
        "AI-specific\nUS 2030\n(EPRI >50 GW)",
        "US data centers\n2030 (EPRI high\n9–17% of grid)",
    ],
    "twh": [218, 458, 50, 438, 580],  # 50 GW × 8760h ≈ 438 TWh; 17% of 4309 ≈ 733 but capped at EPRI 580 high
    "source": ["IEA", "IEA", "EPRI", "EPRI", "EPRI"],
    "kind": ["Actual", "Projection", "Actual", "Projection", "Projection"],
})
demand["scenario"] = pd.Categorical(
    demand["scenario"], categories=demand["scenario"], ordered=True
)

p4 = (
    ggplot(demand, aes(x="scenario", y="twh", fill="kind"))
    + geom_col(width=0.6)
    + geom_text(aes(label="twh"), va="bottom", nudge_y=8, size=9, format_string="{:.0f} TWh")
    + scale_fill_manual(values={"Actual": "#2980b9", "Projection": "#e74c3c"})
    + scale_y_continuous(limits=[0, 650])
    + labs(
        title="US data center electricity demand: 2024 actual vs 2030 projections",
        subtitle="+130–166% by 2030 (IEA base) vs US generation growth of +4.5% in 2024",
        x=None, y="TWh/year",
        caption="Sources: IEA Energy and AI (2025); EPRI Powering Intelligence 2026; Goldman Sachs AI power report",
        fill=None,
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
        axis_text_x=element_text(size=7.5),
    )
)
p4.save(f"{OUTPUT_DIR}/04_ai_data_center_demand.png", dpi=150, width=9, height=5)
print("Saved 04_ai_data_center_demand.png")


# ---------------------------------------------------------------------------
# Plot 5: HBM blended ASP and TAM growth
# Source: TrendForce / FMS 2025; Micron; NextPlatform
# ---------------------------------------------------------------------------

hbm_price = pd.DataFrame({
    "year": [2022, 2023, 2024, 2025],
    "asp_per_gb": [1.40, 1.38, 1.49, 1.80],
    "tam_bn": [None, None, 35.0, 35.0],  # 2025 confirmed by Micron
})

hbm_tam = pd.DataFrame({
    "year": [2025, 2028],
    "tam_bn": [35, 100],
})

p5a = (
    ggplot(hbm_price, aes(x="year", y="asp_per_gb"))
    + geom_line(color="#8e44ad", size=1.3)
    + geom_point(color="#8e44ad", size=4)
    + geom_text(
        aes(label="asp_per_gb"),
        va="bottom", nudge_y=0.03, size=9, format_string="${:.2f}/GB"
    )
    + annotate("text", x=2024.5, y=1.55, label="2025F: +20.8% YoY\n(HBM3e 12-layer mix shift)",
               color="#8e44ad", size=7.5, ha="left")
    + scale_x_continuous(breaks=[2022, 2023, 2024, 2025])
    + scale_y_continuous(limits=[1.2, 2.0])
    + labs(
        title="HBM blended average selling price ($/GB)",
        subtitle="Flat 2022–2023, then surge as AI demand overwhelms supply",
        x=None, y="$/GB",
        caption="Source: TrendForce / FMS 2025 proceedings",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"))
)
p5a.save(f"{OUTPUT_DIR}/05a_hbm_price.png", dpi=150, width=7, height=4.5)
print("Saved 05a_hbm_price.png")

p5b = (
    ggplot(hbm_tam, aes(x="year", y="tam_bn"))
    + geom_col(fill="#8e44ad", width=1.5, alpha=0.8)
    + geom_text(aes(label="tam_bn"), va="bottom", nudge_y=1.5, size=10, format_string="${:.0f}B")
    + annotate("text", x=2026.5, y=60,
               label="$100B by 2028\n> entire DRAM market in 2024",
               color="#6c3483", size=8, ha="center")
    + scale_x_continuous(breaks=[2025, 2028], limits=[2023, 2030])
    + scale_y_continuous(limits=[0, 115])
    + labs(
        title="HBM total addressable market",
        subtitle="From ~$35B (2025) to $100B (2028 Micron forecast)",
        x=None, y="$B",
        caption="Source: Micron CEO forecast; NextPlatform Dec 2025",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"))
)
p5b.save(f"{OUTPUT_DIR}/05b_hbm_tam.png", dpi=150, width=6, height=4.5)
print("Saved 05b_hbm_tam.png")


# ---------------------------------------------------------------------------
# Plot 6: Memory as % of hyperscaler AI spend — the rising inelastic share
# Source: SemiAnalysis (via Tom's Hardware)
# https://www.tomshardware.com/tech-industry/memory-will-consume-30-percent-of-hyperscaler-spending-this-year
# ---------------------------------------------------------------------------

mem_share = pd.DataFrame({
    "year": [2023, 2024, 2025, 2026],
    "memory_pct": [8, 8, 20, 30],
    "other_pct": [92, 92, 80, 70],
})
mem_share_long = mem_share.melt(id_vars="year", var_name="component", value_name="pct")
mem_share_long["component"] = mem_share_long["component"].map({
    "memory_pct": "Memory (HBM-dominated)",
    "other_pct": "Compute, networking, infra",
})

p6 = (
    ggplot(mem_share_long, aes(x="year", y="pct", fill="component"))
    + geom_col(width=0.7)
    + scale_fill_manual(values={
        "Memory (HBM-dominated)": "#8e44ad",
        "Compute, networking, infra": "#bdc3c7",
    })
    + scale_x_continuous(breaks=[2023, 2024, 2025, 2026])
    + scale_y_continuous(labels=lambda l: [f"{int(x)}%" for x in l])
    + annotate("text", x=2026, y=15, label="30%", color="white", size=11)
    + annotate("text", x=2023, y=4, label="8%", color="white", size=11)
    + labs(
        title="Memory as % of hyperscaler AI capex spend",
        subtitle="From a footnote (8%) to the dominant cost driver (30%) in 3 years — same pattern as energy",
        x=None, y="% of AI capex",
        caption="Source: SemiAnalysis estimate, via Tom's Hardware (2026)",
        fill=None,
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
    )
)
p6.save(f"{OUTPUT_DIR}/06_memory_share_hyperscaler_spend.png", dpi=150, width=8, height=5)
print("Saved 06_memory_share_hyperscaler_spend.png")


# ---------------------------------------------------------------------------
# Plot 7: PJM capacity auction price surge — energy cost shock arriving
# Source: SemiAnalysis, "Are AI Datacenters Increasing Electric Bills?"
# https://newsletter.semianalysis.com/p/are-ai-datacenters-increasing-electric
# ---------------------------------------------------------------------------

pjm = pd.DataFrame({
    "auction": ["2024/25\ndelivery", "2025/26\ndelivery"],
    "price": [29, 270],
})

p7 = (
    ggplot(pjm, aes(x="auction", y="price"))
    + geom_col(fill=["#27ae60", "#e74c3c"], width=0.5)
    + geom_text(aes(label="price"), va="bottom", nudge_y=4, size=10,
                format_string="${:.0f}/MW-day")
    + annotate("text", x=1.5, y=200, label="9.3× increase\nin one year",
               color="#c0392b", size=9, ha="center")
    + scale_y_continuous(limits=[0, 330])
    + labs(
        title="PJM capacity auction clearing price ($/MW-day)",
        subtitle="Data center load growth forcing capacity scarcity into wholesale prices; $329/MW-day cap nearly hit",
        x="Delivery year", y="$/MW-day",
        caption="Source: SemiAnalysis 'Are AI Datacenters Increasing Electric Bills?' (2025)",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"))
)
p7.save(f"{OUTPUT_DIR}/07_pjm_capacity_price.png", dpi=150, width=7, height=5)
print("Saved 07_pjm_capacity_price.png")

print("\nAll plots saved.")


# ---------------------------------------------------------------------------
# Plot 8: Colocation lease rates — national avg + Northern Virginia
# Source: CBRE semi-annual North America Data Center Trends H2 2021–H2 2025
# https://www.cbre.com/insights/reports/north-america-data-center-trends-h2-2024
# ---------------------------------------------------------------------------

import pandas as pd
from plotnine import *

colo = pd.DataFrame({
    "period": ["H2 2021", "H1 2022", "H2 2022", "H2 2023", "H2 2024", "H2 2025"],
    "period_num": [2021.5, 2022.0, 2022.5, 2023.5, 2024.5, 2025.5],
    "national": [120, 127.5, 138, 163.44, 184.06, 195.94],
    "nova": [None, None, None, 155, 200, 215],  # NoVA midpoints
})

colo_long = pd.melt(
    colo, id_vars=["period", "period_num"],
    value_vars=["national", "nova"],
    var_name="market", value_name="rate"
).dropna()
colo_long["market"] = colo_long["market"].map({
    "national": "National primary market avg",
    "nova": "Northern Virginia (approx midpoint)",
})

p8 = (
    ggplot(colo_long, aes(x="period_num", y="rate", color="market"))
    + geom_line(size=1.2)
    + geom_point(size=3.5)
    + annotate("text", x=2023.5, y=148, label="+42% YoY\nin NoVA", color="#e74c3c", size=7.5, ha="right")
    + annotate("text", x=2022.0, y=112, label="$120 → $196\n+53% in 3 yr", color="#2980b9", size=7.5)
    + scale_x_continuous(breaks=[2021.5, 2022.5, 2023.5, 2024.5, 2025.5],
                         labels=["H2 2021", "H2 2022", "H2 2023", "H2 2024", "H2 2025"])
    + scale_y_continuous(limits=[90, 240], labels=lambda l: [f"${int(x)}" for x in l])
    + scale_color_manual(values={
        "National primary market avg": "#2980b9",
        "Northern Virginia (approx midpoint)": "#e74c3c",
    })
    + labs(
        title="Colocation lease rates ($/kW/month)",
        subtitle="National avg +53% in 3 years; NoVA +42% YoY in 2023; vacancy at 0.5% in H2 2024",
        x=None, y="$/kW/month",
        caption="Source: CBRE Semi-annual North America Data Center Trends H2 2021–H2 2025; Cushman & Wakefield",
        color=None,
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"), legend_position="bottom")
)
p8.save("08_colocation_rates.png", dpi=150, width=9, height=5)
print("Saved 08_colocation_rates.png")


# ---------------------------------------------------------------------------
# Plot 9: Northern Virginia land prices per acre, 2017–2025
# Source: Loudoun Now transaction records; CBRE; Northern Virginia Magazine
# ---------------------------------------------------------------------------

land = pd.DataFrame({
    "year": [2017, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "price_k": [500, 2000, 2000, 2500, 3000, 6300, 2340, 3760],
    "note": ["Baseline", "Entitled\nAshburn", "", "", "Shift to\nPrince William", "Record\n$615M / 97ac", "242ac blended\navg", "Q1 avg"],
})

p9 = (
    ggplot(land, aes(x="year", y="price_k"))
    + geom_line(color="#8e44ad", size=1.2)
    + geom_point(color="#8e44ad", size=3.5)
    + geom_point(data=land[land["year"] == 2024], color="#e74c3c", size=5)
    + annotate("text", x=2024, y=6600, label="$6.3M/acre\nrecord (Nov 2024)", color="#e74c3c", size=7.5, ha="center")
    + annotate("text", x=2017.3, y=700, label="$500K\n(2017 baseline)", color="#7f8c8d", size=7.5)
    + scale_x_continuous(breaks=list(range(2017, 2027)))
    + scale_y_continuous(labels=lambda l: [f"${int(x/1000)}M" if x >= 1000 else f"${int(x)}K" for x in l])
    + labs(
        title="Northern Virginia data center land price ($/acre)",
        subtitle="+12.6× from 2017 baseline to Nov 2024 record; 41% CAGR in Loudoun assessed values 2018–2022",
        x=None, y="$/acre",
        caption="Source: Loudoun Now transaction records; CBRE; Northern Virginia Magazine",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"), axis_text_x=element_text(size=8))
)
p9.save("09_nova_land_prices.png", dpi=150, width=9, height=5)
print("Saved 09_nova_land_prices.png")


# ---------------------------------------------------------------------------
# Plot 10: PPA prices — LevelTen P25 blended Q1 2021–Q4 2023
# Source: LevelTen Energy PPA Price Index quarterly reports
# https://www.leveltenenergy.com/post/q1-2022-ppa-prices-north-america
# ---------------------------------------------------------------------------

ppa = pd.DataFrame({
    "quarter": ["Q1 2021", "Q2 2021", "Q1 2022", "Q1 2023", "Q4 2023", "Q1 2024"],
    "q_num":   [2021.0, 2021.25, 2022.0, 2023.0, 2023.75, 2024.0],
    "blended": [31, 32.3, 40, 50.32, 56.40, 56.73],
})

p10 = (
    ggplot(ppa, aes(x="q_num", y="blended"))
    + geom_area(fill="#f39c12", alpha=0.25)
    + geom_line(color="#f39c12", size=1.3)
    + geom_point(color="#f39c12", size=3.5)
    + annotate("text", x=2022, y=42.5, label="+28.5% YoY\n(Q1 2021→Q1 2022)", color="#d68910", size=7.5, ha="center")
    + annotate("text", x=2021, y=29, label="~$28–30\n(2020 trough)", color="#7f8c8d", size=7)
    + scale_x_continuous(breaks=[2021.0, 2021.25, 2022.0, 2023.0, 2023.75, 2024.0],
                         labels=["Q1\n2021", "Q2\n2021", "Q1\n2022", "Q1\n2023", "Q4\n2023", "Q1\n2024"])
    + scale_y_continuous(limits=[20, 65], labels=lambda l: [f"${int(x)}/MWh" for x in l])
    + labs(
        title="Renewable PPA prices — LevelTen P25 blended (solar + wind)",
        subtitle="+90% from 2020 trough to Q4 2023; largest single-year jump +28.5% (2021→2022)",
        x=None, y="$/MWh (P25)",
        caption="Source: LevelTen Energy PPA Price Index quarterly reports",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"))
)
p10.save("10_ppa_prices.png", dpi=150, width=9, height=5)
print("Saved 10_ppa_prices.png")


# ---------------------------------------------------------------------------
# Plot 11: PJM interconnection wait time — spot markets vs contract markets
# Source: RMI PJM speed-to-power analysis; CBRE pre-lease data
# ---------------------------------------------------------------------------

wait = pd.DataFrame({
    "year": [2008, 2012, 2016, 2019, 2022, 2025],
    "wait_yr": [1.5, 2.5, 3.0, 4.5, 6.5, 8.2],
})

p11 = (
    ggplot(wait, aes(x="year", y="wait_yr"))
    + geom_area(fill="#e74c3c", alpha=0.15)
    + geom_line(color="#e74c3c", size=1.3)
    + geom_point(color="#e74c3c", size=3.5)
    + geom_hline(yintercept=2, linetype="dashed", color="#27ae60", alpha=0.7)
    + annotate("text", x=2009, y=1.7, label="~2yr typical\n(pre-2012)", color="#27ae60", size=7.5)
    + annotate("text", x=2025, y=8.5, label=">8yr (2025)\n6.53yr avg\nfor DC projects", color="#c0392b", size=7.5, ha="right")
    + annotate("text", x=2015, y=6.5, label="74% of capacity under\nconstruction already\npre-leased (CBRE H1 2025)", color="#7f8c8d", size=7, ha="center")
    + scale_x_continuous(breaks=list(range(2008, 2026, 2)))
    + scale_y_continuous(limits=[0, 10], labels=lambda l: [f"{int(x)}yr" if x > 0 else "" for x in l])
    + labs(
        title="PJM grid interconnection wait time (years)",
        subtitle="Quadrupled since 2008; data center projects average 6.53yr; demand locked up years in advance",
        x=None, y="Years from request to commercial operation",
        caption="Source: RMI PJM speed-to-power analysis; CBRE H1 2025 pre-leasing data",
    )
    + theme_minimal(base_size=11)
    + theme(plot_title=element_text(weight="bold"))
)
p11.save("11_pjm_wait_time.png", dpi=150, width=9, height=5)
print("Saved 11_pjm_wait_time.png")

print("\nPlots 8–11 done.")
