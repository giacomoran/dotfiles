"""Create EU-to-US permanent-inflow and duration-of-stay figures for the wiki."""

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_text,
    geom_area,
    geom_col,
    geom_text,
    ggplot,
    labs,
    position_stack,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


URL_PERMANENT_INFLOW = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.ELS.IMD,DSD_MIG@DF_MIG,1.0/USA..A.B11._T...?"
    "startPeriod=2013&dimensionAtObservation=AllDimensions"
)
URL_DURATION_OF_STAY = (
    "https://webfs.oecd.org/Els-com/Migration/Databases/"
    "Database%20on%20Immigrants%20in%20OECD%20and%20non-OECD%20Countries%20DIOC/"
    "DIOC%20database%20-%20click%20here/Reference%20years%202020-2021/"
    "t3_TOP100.xlsx"
)
PATH_OUTPUT_PERMANENT_INFLOW = Path(
    "../Zxtra/Assets/european_union_united_states_permanent_inflows.png"
)
PATH_OUTPUT_DURATION_OF_STAY = Path(
    "../Zxtra/Assets/european_union_united_states_tertiary_duration_of_stay.png"
)

NAMES_COUNTRY_EUROPEAN_UNION = {
    "AUT": "Austria",
    "BEL": "Belgium",
    "BGR": "Bulgaria",
    "HRV": "Croatia",
    "CYP": "Cyprus",
    "CZE": "Czechia",
    "DNK": "Denmark",
    "EST": "Estonia",
    "FIN": "Finland",
    "FRA": "France",
    "DEU": "Germany",
    "GRC": "Greece",
    "HUN": "Hungary",
    "IRL": "Ireland",
    "ITA": "Italy",
    "LVA": "Latvia",
    "LTU": "Lithuania",
    "LUX": "Luxembourg",
    "MLT": "Malta",
    "NLD": "Netherlands",
    "POL": "Poland",
    "PRT": "Portugal",
    "ROU": "Romania",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "ESP": "Spain",
    "SWE": "Sweden",
}
COUNTRIES_DURATION_OF_STAY = {
    "DEU": "Germany",
    "POL": "Poland",
    "FRA": "France",
    "ITA": "Italy",
    "ROU": "Romania",
    "ESP": "Spain",
}
COUNTRIES_PERMANENT_INFLOW_NAMED = {
    "DEU",
    "ESP",
    "FRA",
    "ITA",
    "POL",
    "ROU",
}
COLORS_PERMANENT_INFLOW = {
    "Germany": "#315b7d",
    "Spain": "#d69b2d",
    "France": "#5487a5",
    "Italy": "#66a77a",
    "Poland": "#b85c5c",
    "Romania": "#8b6ca8",
    "Other EU-27": "#cbd5df",
}
ORDER_DURATION_OF_STAY = [
    "<=1 year",
    "1-5 years",
    "5-10 years",
    "10-20 years",
    ">20 years",
]
LABELS_DURATION_OF_STAY = {
    "≤ 1 years": "<=1 year",
    "> 1 & ≤ 5 years": "1-5 years",
    "> 5 & ≤ 10 years": "5-10 years",
    "> 10 & ≤ 20 years": "10-20 years",
    "> 20 years": ">20 years",
}
COLORS_DURATION_OF_STAY = {
    "<=1 year": "#d9edf4",
    "1-5 years": "#9bc9dc",
    "5-10 years": "#65a6c4",
    "10-20 years": "#3d7fa4",
    ">20 years": "#244f70",
}


# Download the annual OECD series and validate its expected dimensions.
response_permanent_inflow = requests.get(
    URL_PERMANENT_INFLOW,
    headers={"Accept": "text/csv"},
    timeout=60,
)
response_permanent_inflow.raise_for_status()
df_permanent_inflow_source = pd.read_csv(BytesIO(response_permanent_inflow.content))
assert set(df_permanent_inflow_source["MEASURE"]) == {"B11"}
assert set(df_permanent_inflow_source["UNIT_MEASURE"]) == {"PS"}

# Sum the constant EU-27 membership by year and retain six named country series.
df_permanent_inflow_european_union = df_permanent_inflow_source[
    df_permanent_inflow_source["CITIZENSHIP"].isin(NAMES_COUNTRY_EUROPEAN_UNION)
].copy()
df_permanent_inflow_european_union["year"] = df_permanent_inflow_european_union[
    "TIME_PERIOD"
].astype(int)
df_permanent_inflow_european_union["origin"] = df_permanent_inflow_european_union[
    "CITIZENSHIP"
].map(NAMES_COUNTRY_EUROPEAN_UNION)
df_permanent_inflow_european_union.loc[
    ~df_permanent_inflow_european_union["CITIZENSHIP"].isin(
        COUNTRIES_PERMANENT_INFLOW_NAMED
    ),
    "origin",
] = "Other EU-27"
df_permanent_inflow_plot = df_permanent_inflow_european_union.groupby(
    ["year", "origin"], as_index=False
)["OBS_VALUE"].sum()
assert set(df_permanent_inflow_plot["year"]) == set(range(2013, 2024))

# Confirm the headline totals before rendering the country-by-year stack.
df_permanent_inflow_total = df_permanent_inflow_plot.groupby(
    "year", as_index=False
)["OBS_VALUE"].sum()
count_permanent_inflow_average = df_permanent_inflow_total["OBS_VALUE"].mean()
assert int(count_permanent_inflow_average.round()) == 38_677
assert df_permanent_inflow_total.set_index("year").loc[2013, "OBS_VALUE"] == 43_163
assert df_permanent_inflow_total.set_index("year").loc[2023, "OBS_VALUE"] == 36_600

plot_permanent_inflow = (
    ggplot(
        df_permanent_inflow_plot,
        aes(x="year", y="OBS_VALUE", fill="origin"),
    )
    + geom_area(color="white", size=0.25, alpha=0.98)
    + geom_text(
        data=df_permanent_inflow_total[
            df_permanent_inflow_total["year"].isin([2013, 2016, 2020, 2023])
        ].assign(label=lambda df: df["OBS_VALUE"].map(lambda value: f"{value / 1000:.1f}k")),
        mapping=aes(x="year", y="OBS_VALUE", label="label"),
        inherit_aes=False,
        nudge_y=1_700,
        size=8.5,
        color="#334155",
    )
    + scale_fill_manual(values=COLORS_PERMANENT_INFLOW)
    + scale_x_continuous(
        limits=(2012.6, 2023.4),
        breaks=list(range(2013, 2024)),
        expand=(0, 0),
    )
    + scale_y_continuous(
        limits=(0, 51_000),
        breaks=[0, 10_000, 20_000, 30_000, 40_000, 50_000],
        labels=["0", "10k", "20k", "30k", "40k", "50k"],
        expand=(0, 0),
    )
    + labs(
        title="EU-27 permanent inflows to the US remain below their mid-2010s peak",
        subtitle=(
            "Citizens obtaining permanent residence, including status adjustments; "
            "2013-23 average: 38.7k"
        ),
        x=None,
        y="People obtaining permanent residence",
        fill="Citizenship",
        caption=(
            "Constant EU-27 membership. Fiscal years; not border arrivals and no education filter. "
            "Source: OECD International Migration Database, updated November 2025."
        ),
    )
    + theme_minimal(base_size=12)
    + theme(
        figure_size=(11, 6.2),
        plot_title=element_text(weight="bold", size=15),
        plot_subtitle=element_text(size=11, color="#475569"),
        plot_caption=element_text(size=8.5, color="#64748b", ha="left"),
        axis_text_x=element_text(size=9, rotation=45, ha="right"),
        axis_text_y=element_text(size=9, color="#64748b"),
        axis_title_x=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#d9e0e7", size=0.6),
        legend_position="right",
        legend_title=element_text(weight="bold"),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Download the matching DIOC duration workbook and isolate tertiary-educated US residents.
response_duration_of_stay = requests.get(URL_DURATION_OF_STAY, timeout=60)
response_duration_of_stay.raise_for_status()
df_duration_of_stay_source = pd.read_excel(BytesIO(response_duration_of_stay.content))
df_duration_of_stay_selected = df_duration_of_stay_source[
    df_duration_of_stay_source["country"].eq("USA")
    & df_duration_of_stay_source["coub"].isin(COUNTRIES_DURATION_OF_STAY)
    & df_duration_of_stay_source["edu_lfs"].eq("ISCED 5/6/7/8")
].copy()
assert set(df_duration_of_stay_selected["fborn"]) == {"Foreign-born"}

# Convert duration totals to within-origin shares for a comparable cohort profile.
df_duration_of_stay_plot = df_duration_of_stay_selected.groupby(
    ["coub", "dos_cen"], as_index=False
)["number"].sum()
df_duration_of_stay_plot["origin"] = df_duration_of_stay_plot["coub"].map(
    COUNTRIES_DURATION_OF_STAY
)
df_duration_of_stay_plot["duration"] = df_duration_of_stay_plot["dos_cen"].map(
    LABELS_DURATION_OF_STAY
)
assert df_duration_of_stay_plot["duration"].notna().all()
df_duration_of_stay_plot["share"] = df_duration_of_stay_plot["number"] / (
    df_duration_of_stay_plot.groupby("coub")["number"].transform("sum")
)
df_duration_of_stay_plot["duration"] = pd.Categorical(
    df_duration_of_stay_plot["duration"],
    categories=ORDER_DURATION_OF_STAY,
    ordered=True,
)
order_origin = ["Spain", "France", "Romania", "Poland", "Italy", "Germany"]
df_duration_of_stay_plot["origin"] = pd.Categorical(
    df_duration_of_stay_plot["origin"],
    categories=order_origin,
    ordered=True,
)
df_duration_of_stay_plot["label"] = df_duration_of_stay_plot["share"].map(
    lambda share: f"{share:.0%}" if share >= 0.075 else ""
)

# Validate Germany's legacy-stock result before rendering the comparison.
df_duration_of_stay_germany = df_duration_of_stay_plot[
    df_duration_of_stay_plot["coub"].eq("DEU")
].set_index("duration")
assert round(df_duration_of_stay_germany.loc[">20 years", "share"], 4) == 0.7971
count_germany_recent_ten_years = df_duration_of_stay_germany.loc[
    ["<=1 year", "1-5 years", "5-10 years"], "number"
].sum()
count_germany_total = df_duration_of_stay_germany["number"].sum()
assert round(count_germany_recent_ten_years / count_germany_total, 3) == 0.104

plot_duration_of_stay = (
    ggplot(
        df_duration_of_stay_plot,
        aes(x="origin", y="share", fill="duration"),
    )
    + geom_col(width=0.72)
    + geom_text(
        aes(label="label"),
        position=position_stack(vjust=0.5),
        size=8.5,
        color="white",
    )
    + coord_flip()
    + scale_fill_manual(values=COLORS_DURATION_OF_STAY)
    + scale_y_continuous(
        limits=(0, 1.001),
        breaks=[0, 0.25, 0.5, 0.75, 1],
        labels=["0%", "25%", "50%", "75%", "100%"],
        expand=(0, 0),
    )
    + labs(
        title="Germany's tertiary-educated US population is overwhelmingly legacy stock",
        subtitle="Share by duration of residence, all ages, OECD DIOC 2020/21 provisional data",
        x=None,
        y="Share of tertiary-educated residents",
        fill="Years in the US",
        caption=(
            "Country of birth; all ages; ISCED 5-8. Percent labels below 7.5% omitted. "
            "Source: OECD DIOC 2020/21."
        ),
    )
    + theme_minimal(base_size=12)
    + theme(
        figure_size=(10.5, 5.8),
        plot_title=element_text(weight="bold", size=15),
        plot_subtitle=element_text(size=11, color="#475569"),
        plot_caption=element_text(size=8.5, color="#64748b", ha="left"),
        axis_text_y=element_text(size=10.5),
        axis_text_x=element_text(size=9, color="#64748b"),
        axis_title_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#d9e0e7", size=0.6),
        legend_position="bottom",
        legend_title=element_text(weight="bold"),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

# Save both assets in the shared Obsidian attachment directory.
PATH_OUTPUT_PERMANENT_INFLOW.parent.mkdir(parents=True, exist_ok=True)
plot_permanent_inflow.save(PATH_OUTPUT_PERMANENT_INFLOW, dpi=180, verbose=False)
plot_duration_of_stay.save(PATH_OUTPUT_DURATION_OF_STAY, dpi=180, verbose=False)
print(PATH_OUTPUT_PERMANENT_INFLOW.resolve())
print(PATH_OUTPUT_DURATION_OF_STAY.resolve())
