"""
NdPr oxide price history (2010-2026) and NdFeB demand by sector (2024).

Two plots:
  A - NdPr oxide price time series, annotated with the four supply-shock
      episodes from [[NdFeB supply is structurally inelastic]].
  B - Current global NdFeB demand by end-use sector (2024 snapshot).

Data caveats:
  - NdPr oxide price is the standard proxy for NdFeB magnet price (sintered
    NdFeB cost is roughly 1.5-2x NdPr oxide $/kg). Public year-by-year
    annual averages disagree across sources (SMM, Asian Metal, Argus,
    Statista, MacroMicro). The series below is a triangulated best-fit of
    publicly quoted annual averages.
  - Sector breakdown is triangulated across Adamas Intelligence (total
    ~260 kt in 2024), Grand View Research (automotive ~33% in 2024),
    SMM/Shanghai Metals Market, and IDTechEx narrative descriptions. No
    single source publishes the full tonnage split; percentages here
    should be read as +/- 3-5 pp.
"""

import pandas as pd
from plotnine import (
    ggplot, aes, geom_line, geom_point, geom_col, geom_text, geom_hline,
    geom_vline, annotate, scale_x_continuous, scale_y_continuous,
    scale_fill_manual, labs, theme_minimal, theme, element_text,
    element_blank, coord_flip,
)
import warnings
warnings.filterwarnings("ignore")

OUT = "/Users/giacomoran/Obsidian/giacomo/Zxtra/Assets"

# NdPr oxide annual average price, USD/kg.
# Triangulated from Strategic Metals Invest, MacroMicro, Asian Metal, SMM,
# Statista summaries, and CrossCurrents (2020 anchor at $45, 2022 peak $170).
# Confidence: MEDIUM for 2010-2024 annual averages, HIGH for episode timing,
# LOW for intra-year peaks (shown as separate points).
ndpr_price = pd.DataFrame({
    "year":  [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018,
              2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    "price": [  35,  200,  125,   70,   65,   50,   45,   65,   60,
                50,   45,  105,  130,   75,   55,   95,  215],
})

# Episode annotations (see NdFeB supply is structurally inelastic).
episodes = pd.DataFrame([
    (2011.0, 200, "2010-11 Senkaku\nshock: 5x spike"),
    (2022.0, 170, "2021-22 COVID\ncrunch: +375%"),
    (2026.0, 215, "Apr 2025\nexport controls"),
], columns=["x", "y", "label"])

p_A = (
    ggplot(ndpr_price, aes(x="year", y="price"))
    + geom_line(color="#1565C0", size=1.2)
    + geom_point(color="#1565C0", size=2.8)
    + geom_point(episodes, aes(x="x", y="y"), color="#F44336", size=4, inherit_aes=False)
    + geom_text(
        pd.DataFrame([
            (2011.4, 200, "2010-11 Senkaku\nshock: 5x spike", "left"),
            (2021.6, 170, "2021-22 COVID\ncrunch: +375%",     "right"),
            (2025.6, 215, "Apr 2025\nexport controls",        "right"),
        ], columns=["x", "y", "label", "ha"]),
        aes(x="x", y="y", label="label", ha="ha"),
        color="#F44336", size=8, nudge_y=12, inherit_aes=False,
    )
    + scale_x_continuous(breaks=list(range(2010, 2027, 2)))
    + scale_y_continuous(
        breaks=[0, 50, 100, 150, 200, 250],
        labels=["$0", "$50", "$100", "$150", "$200", "$250"],
    )
    + labs(
        title="NdPr oxide price, 2010-2026 (USD/kg)",
        subtitle=(
            "Three structural shocks in 15 years. Non-Chinese supply did not respond within any shock window.\n"
            "Triangulated annual averages from SMM, MacroMicro, Strategic Metals Invest, and CrossCurrents."
        ),
        x="Year",
        y="NdPr oxide price (USD / kg)",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5.5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        panel_grid_minor=element_blank(),
    )
)
p_A.save(f"{OUT}/ndpr_price_2010_2026.png", dpi=150)
print("Saved ndpr_price_2010_2026.png")


# Global NdFeB demand by end-use sector, 2024.
# Total anchor: ~250 kt NdFeB in 2024 (Adamas Intelligence puts rare earth
# magnets at ~260 kt and NdFeB is ~96% of that).
# Sector shares triangulated across Grand View Research, SMM, and standard
# literature. The "automotive" bucket includes EV traction motors plus small
# motors in ICE cars (EPS, starter, wipers, fans).
demand = pd.DataFrame([
    ("Automotive (EV traction + ICE small motors)", 82, "#1565C0"),
    ("Consumer electronics (HDDs, VCMs, speakers, phones)", 70, "#42A5F5"),
    ("Wind turbines (direct-drive generators)", 30, "#66BB6A"),
    ("Industrial motors, automation, robotics", 30, "#FFA726"),
    ("HVAC and appliances", 20, "#AB47BC"),
    ("Other (MRI, defense, aerospace, marine)", 18, "#78909C"),
], columns=["sector", "tonnes", "color"])
demand["label"] = (
    demand["tonnes"].astype(str) + " kt ("
    + (100 * demand["tonnes"] / demand["tonnes"].sum()).round().astype(int).astype(str)
    + "%)"
)
demand["sector"] = pd.Categorical(demand["sector"], categories=demand["sector"].tolist()[::-1])

p_B = (
    ggplot(demand, aes(x="sector", y="tonnes", fill="sector"))
    + geom_col(show_legend=False)
    + geom_text(aes(label="label"), ha="left", nudge_y=2, size=9, color="#222222")
    + scale_fill_manual(values=demand.sort_values("sector")["color"].tolist())
    + coord_flip()
    + scale_y_continuous(
        breaks=[0, 20, 40, 60, 80, 100],
        labels=["0", "20", "40", "60", "80", "100 kt"],
        limits=[0, 105],
    )
    + labs(
        title="Global NdFeB demand by end-use sector, 2024 (~250 kt/yr total)",
        subtitle=(
            "Triangulated from Adamas Intelligence (total), Grand View Research (automotive share), and SMM.\n"
            "Percentages are best estimates; source reports disagree by +/- 3-5 pp per sector."
        ),
        x="",
        y="Tonnes per year",
    )
    + theme_minimal()
    + theme(
        figure_size=(10, 5),
        plot_title=element_text(size=13, fontweight="bold"),
        plot_subtitle=element_text(size=9, color="#555555"),
        axis_text_y=element_text(size=9),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
)
p_B.save(f"{OUT}/ndfeb_demand_by_sector_2024.png", dpi=150)
print("Saved ndfeb_demand_by_sector_2024.png")
