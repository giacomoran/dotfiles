"""Create the OECD EU-born tertiary-education stock figure for the wiki."""

from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import pandas as pd
from plotnine import (
    aes,
    coord_flip,
    element_blank,
    element_line,
    element_text,
    geom_col,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


URL_SOURCE = (
    "https://webfs.oecd.org/Els-com/Migration/Databases/"
    "Database%20on%20Immigrants%20in%20OECD%20and%20non-OECD%20Countries%20DIOC/"
    "DIOC%20database%20-%20click%20here/Reference%20years%202020-2021/"
    "t1_TOP100.xlsx"
)
PATH_OUTPUT = Path("../Zxtra/Assets/european_union_united_states_tertiary_stock.png")

COUNTRIES_EUROPEAN_UNION = {
    "AUT",
    "BEL",
    "BGR",
    "HRV",
    "CYP",
    "CZE",
    "DNK",
    "EST",
    "FIN",
    "FRA",
    "DEU",
    "GRC",
    "HUN",
    "IRL",
    "ITA",
    "LVA",
    "LTU",
    "LUX",
    "MLT",
    "NLD",
    "POL",
    "PRT",
    "ROU",
    "SVK",
    "SVN",
    "ESP",
    "SWE",
}
COUNTRIES_OBSERVED_EXPECTED = {
    "AUT",
    "BEL",
    "BGR",
    "DEU",
    "ESP",
    "FIN",
    "FRA",
    "GRC",
    "HUN",
    "IRL",
    "ITA",
    "NLD",
    "POL",
    "PRT",
    "ROU",
    "SWE",
}
NAMES_COUNTRY = {
    "DEU": "Germany",
    "POL": "Poland",
    "FRA": "France",
    "ITA": "Italy",
    "ROU": "Romania",
    "ESP": "Spain",
}


# Download the provisional OECD workbook so the figure can be rebuilt from source.
with TemporaryDirectory() as directory_temporary:
    path_source = Path(directory_temporary) / "oecd-dioc-2020-2021.xlsx"
    urlretrieve(URL_SOURCE, path_source)
    data_population = pd.read_excel(path_source)

# Isolate the working-age EU-born tertiary-educated population residing in the US.
data_selected = data_population[
    data_population["country"].eq("USA")
    & data_population["coub"].isin(COUNTRIES_EUROPEAN_UNION)
    & data_population["age_lfs"].eq("25-64")
    & data_population["edu_lfs"].eq("ISCED 5/6/7/8")
].copy()
countries_observed = set(data_selected["coub"].unique())
assert countries_observed == COUNTRIES_OBSERVED_EXPECTED

# Aggregate sexes, retain the six largest origins, and combine the observed tail.
data_country = (
    data_selected.groupby("coub", as_index=False)["number"]
    .sum()
    .sort_values("number", ascending=False)
)
data_largest = data_country.head(6).copy()
data_largest["origin"] = data_largest["coub"].map(NAMES_COUNTRY)
assert data_largest["origin"].notna().all()

number_other_observed = data_country.iloc[6:]["number"].sum()
data_other_observed = pd.DataFrame(
    [{"coub": "OTHER", "number": number_other_observed, "origin": "Other observed EU"}]
)
data_plot = pd.concat([data_largest, data_other_observed], ignore_index=True)
data_plot["origin"] = pd.Categorical(
    data_plot["origin"],
    categories=list(reversed(data_plot["origin"].tolist())),
    ordered=True,
)
data_plot["category"] = data_plot["origin"].map(
    lambda origin: "Observed tail" if origin == "Other observed EU" else "Named origin"
)
data_plot["label"] = data_plot["number"].map(lambda number: f"{number / 1000:.0f}k")

number_total = data_plot["number"].sum()
assert number_total == 1_182_729

# Render a restrained horizontal bar chart with the lower-bound limitation visible.
plot = (
    ggplot(data_plot, aes(x="origin", y="number", fill="category"))
    + geom_col(width=0.72, show_legend=False)
    + geom_text(aes(label="label"), ha="left", nudge_y=8_000, size=9)
    + coord_flip()
    + scale_fill_manual(values={"Named origin": "#376a9f", "Observed tail": "#78a6c8"})
    + scale_y_continuous(
        limits=(0, 440_000),
        breaks=[0, 100_000, 200_000, 300_000, 400_000],
        labels=["0", "100k", "200k", "300k", "400k"],
        expand=(0, 0),
    )
    + labs(
        title="At least 1.18 million working-age EU-born tertiary graduates lived in the US",
        subtitle="Age 25-64, ISCED 5-8, OECD DIOC 2020/21 provisional data",
        x=None,
        y="Residents",
        caption=(
            "Lower bound: only 16 EU origins appear among the US top 100 origins; "
            "11 smaller EU origins are omitted. Source: OECD DIOC 2020/21."
        ),
    )
    + theme_minimal(base_size=12)
    + theme(
        figure_size=(10, 5.6),
        plot_title=element_text(weight="bold", size=15),
        plot_subtitle=element_text(size=11, color="#475569"),
        plot_caption=element_text(size=8.5, color="#64748b", ha="left"),
        axis_text_y=element_text(size=10.5),
        axis_text_x=element_text(size=9, color="#64748b"),
        axis_title_y=element_blank(),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#d9e0e7", size=0.6),
        plot_background=element_blank(),
        panel_background=element_blank(),
    )
)

PATH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
plot.save(PATH_OUTPUT, dpi=180, verbose=False)
print(PATH_OUTPUT.resolve())
