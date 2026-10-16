"""
Approximate NVIDIA data-center accelerator price per kW of board power.

Run from .scripts/ with:
    uv run python gpu_cost_per_kw_trend.py
"""

from pathlib import Path

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_line,
    element_text,
    geom_errorbar,
    geom_hline,
    geom_line,
    geom_point,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_y_continuous,
    theme,
    theme_minimal,
)


OUTPUT_PATH = Path("../Zxtra/Assets/gpu_cost_per_kw_trend_2014_2026.png")


# Prices are accelerator-only purchase prices, not full system/rack costs.
# Power is board power or max TDP for the selected high-performance form factor.
gpu_prices = pd.DataFrame(
    [
        {
            "year": 2014,
            "model": "K80",
            "price_low_usd": 4500,
            "price_mid_usd": 5000,
            "price_high_usd": 7000,
            "power_w": 300,
            "generation": "Kepler",
            "source_note": "NextPlatform reports K80 launch around $5,000; contemporaneous sources cite $5,000-$7,000.",
        },
        {
            "year": 2016,
            "model": "P100 SXM2",
            "price_low_usd": 9428,
            "price_mid_usd": 9428,
            "price_high_usd": 9428,
            "power_w": 300,
            "generation": "Pascal",
            "source_note": "Microway single-unit P100 SXM2 price analysis; NVIDIA datasheet max power 300 W.",
        },
        {
            "year": 2017,
            "model": "V100 SXM2",
            "price_low_usd": 10664,
            "price_mid_usd": 11061,
            "price_high_usd": 11458,
            "power_w": 300,
            "generation": "Volta",
            "source_note": "Microway V100 SXM 16/32 GB price range; NVIDIA datasheet max power 300 W.",
        },
        {
            "year": 2020,
            "model": "A100 80GB SXM",
            "price_low_usd": 15000,
            "price_mid_usd": 17500,
            "price_high_usd": 20000,
            "power_w": 400,
            "generation": "Ampere",
            "source_note": "Modal/Northflank A100 80 GB SXM price ranges; NVIDIA datasheet max TDP 400 W.",
        },
        {
            "year": 2023,
            "model": "H100 SXM",
            "price_low_usd": 35000,
            "price_mid_usd": 37500,
            "price_high_usd": 40000,
            "power_w": 700,
            "generation": "Hopper",
            "source_note": "Northflank H100 SXM mid-2025 price range; NVIDIA page max TDP 700 W.",
        },
        {
            "year": 2024,
            "model": "H200 SXM",
            "price_low_usd": 30000,
            "price_mid_usd": 35000,
            "price_high_usd": 40000,
            "power_w": 700,
            "generation": "Hopper",
            "source_note": "Modal/TRG/market guide H200 price ranges; H200 SXM max TDP around 700 W.",
        },
        {
            "year": 2026,
            "model": "B200 SXM",
            "price_low_usd": 30000,
            "price_mid_usd": 40000,
            "price_high_usd": 50000,
            "power_w": 1000,
            "generation": "Blackwell",
            "source_note": "Jensen Huang cited $30k-$40k; later OEM quotes often $45k-$50k; Lenovo/NVIDIA DGX docs show 1000 W per GPU.",
        },
    ]
)

for price_column in ["price_low_usd", "price_mid_usd", "price_high_usd"]:
    gpu_prices[f"{price_column}_per_kw_thousands"] = (
        gpu_prices[price_column] / (gpu_prices["power_w"] / 1000) / 1000
    )

plot = (
    ggplot(
        gpu_prices,
        aes(
            x="year",
            y="price_mid_usd_per_kw_thousands",
            color="generation",
            group=1,
        ),
    )
    + geom_errorbar(
        aes(
            ymin="price_low_usd_per_kw_thousands",
            ymax="price_high_usd_per_kw_thousands",
        ),
        width=0.18,
        alpha=0.7,
        size=0.8,
    )
    + geom_line(color="#34495e", size=1.0, alpha=0.7)
    + geom_point(size=3.2)
    + geom_text(
        aes(label="model"),
        nudge_y=2.8,
        size=8,
        color="#263238",
        ha="center",
        va="bottom",
    )
    + geom_hline(yintercept=50, linetype="dashed", color="#c0392b", size=0.8)
    + annotate(
        "text",
        x=2018.2,
        y=52.5,
        label="Handmer heuristic: ~$50k/kW",
        color="#c0392b",
        size=8,
        ha="left",
    )
    + scale_color_manual(
        values={
            "Kepler": "#5dade2",
            "Pascal": "#58d68d",
            "Volta": "#f4d03f",
            "Ampere": "#eb984e",
            "Hopper": "#af7ac5",
            "Blackwell": "#2c3e50",
        }
    )
    + scale_y_continuous(
        limits=(0, 70),
        breaks=list(range(0, 71, 10)),
        labels=lambda values: [f"${int(value)}k" for value in values],
    )
    + labs(
        title="NVIDIA data-center accelerator price per kW of GPU board power",
        subtitle="Approximate purchase price divided by board/TDP power; uncertainty bars reflect opaque market pricing",
        x=None,
        y="Accelerator price per kW",
        color="GPU generation",
        caption="Sources: NVIDIA datasheets/product docs; Microway P100/V100 prices; Modal/Northflank/TRG/TweakTown/Lenovo market and product references. Not full server or rack capex.",
    )
    + theme_minimal(base_size=11)
    + theme(
        plot_title=element_text(weight="bold"),
        legend_position="bottom",
        axis_line_x=element_line(color="#bdc3c7"),
        panel_grid_minor=element_line(color="#eef2f3"),
    )
)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
plot.save(OUTPUT_PATH, dpi=180, width=10, height=5.8)
print(f"Saved {OUTPUT_PATH}")
