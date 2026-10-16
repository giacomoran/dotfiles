from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".scripts" / ".matplotlib-cache"))

import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

OUT = ROOT / "Zxtra" / "Assets" / "solar_pv_module_learning_curve_2026.png"


def price_at_capacity(
    anchor_price_usd_per_watt: float,
    anchor_capacity_gigawatts: float,
    target_capacity_gigawatts: np.ndarray | float,
    learning_rate: float,
) -> np.ndarray | float:
    """Project module price by Wright's Law from a capacity/price anchor."""
    doublings = np.log2(np.asarray(target_capacity_gigawatts) / anchor_capacity_gigawatts)
    return anchor_price_usd_per_watt * ((1 - learning_rate) ** doublings)


def annual_price(
    anchor_price_usd_per_watt: float,
    years_after_anchor: float,
    annual_decline: float,
) -> float:
    """Project module price by a simple annual cost decline assumption."""
    return anchor_price_usd_per_watt * ((1 - annual_decline) ** years_after_anchor)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

    # Official / primary-source anchors used in the plot.
    capacity_2024_gw = 2276.0
    capacity_2025_gw = 2276.0 + 698.0
    doe_q3_2024_global_spot_usd_w = 0.100
    infolink_june_2026_topcon_usd_w = 0.116
    infolink_june_2026_europe_topcon_usd_w = 0.126
    infolink_june_2026_us_topcon_usd_w = 0.310

    # Source check: SolarPower Europe 2026-2030 says 664 GW in 2025 and 3 TW total,
    # but IEA PVPS gives the more precise 2024-to-2025 bridge used here.
    solarpower_europe_2025_capacity_gw = 3000.0

    capacity_range_gw = np.geomspace(1800, 3900, 200)
    owid_long_run_price = price_at_capacity(
        doe_q3_2024_global_spot_usd_w,
        capacity_2024_gw,
        capacity_range_gw,
        0.20,
    )
    handmer_price = price_at_capacity(
        doe_q3_2024_global_spot_usd_w,
        capacity_2024_gw,
        capacity_range_gw,
        0.44,
    )

    handmer_at_2025 = float(
        price_at_capacity(
            doe_q3_2024_global_spot_usd_w,
            capacity_2024_gw,
            capacity_2025_gw,
            0.44,
        )
    )
    owid_at_2025 = float(
        price_at_capacity(
            doe_q3_2024_global_spot_usd_w,
            capacity_2024_gw,
            capacity_2025_gw,
            0.20,
        )
    )
    fifteen_percent_annual_at_june_2026 = annual_price(
        doe_q3_2024_global_spot_usd_w,
        1.72,
        0.15,
    )

    fig, ax = plt.subplots(figsize=(12, 7.8), dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fbfbf8")

    ax.plot(
        capacity_range_gw,
        owid_long_run_price,
        color="#476a6f",
        linewidth=2.4,
        label="20% per capacity doubling benchmark (OWID historical rule of thumb)",
    )
    ax.plot(
        capacity_range_gw,
        handmer_price,
        color="#c23b22",
        linewidth=2.4,
        linestyle="--",
        label="44% per capacity doubling continuation (Handmer 2024 claim)",
    )

    ax.scatter(
        [capacity_2024_gw],
        [doe_q3_2024_global_spot_usd_w],
        s=90,
        color="#2f5d8c",
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
    )
    ax.scatter(
        [capacity_2025_gw],
        [infolink_june_2026_topcon_usd_w],
        s=120,
        color="#f28c28",
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
        label="June 2026 InfoLink TOPCon spot quote",
    )
    ax.scatter(
        [capacity_2025_gw],
        [infolink_june_2026_europe_topcon_usd_w],
        s=110,
        color="#6f4e7c",
        edgecolor="white",
        linewidth=1.2,
        zorder=5,
        label="June 2026 Europe TOPCon FOB quote",
    )
    ax.axvline(capacity_2025_gw, color="#c7c7c7", linewidth=1.1, linestyle=":")
    ax.axvline(solarpower_europe_2025_capacity_gw, color="#d9d9d9", linewidth=1.1, linestyle=":")

    ax.annotate(
        "DOE/NREL Q3 2024\nmodule spot near $0.10/W",
        xy=(capacity_2024_gw, doe_q3_2024_global_spot_usd_w),
        xytext=(1850, 0.145),
        arrowprops={"arrowstyle": "->", "color": "#2f5d8c", "lw": 1.1},
        fontsize=9,
        color="#243447",
    )
    ax.annotate(
        "June 2026 TOPCon\n$0.116/W non-China spot",
        xy=(capacity_2025_gw, infolink_june_2026_topcon_usd_w),
        xytext=(3190, 0.147),
        arrowprops={"arrowstyle": "->", "color": "#f28c28", "lw": 1.1},
        fontsize=9,
        color="#50310b",
    )
    ax.annotate(
        "Europe project quote\n$0.126/W FOB",
        xy=(capacity_2025_gw, infolink_june_2026_europe_topcon_usd_w),
        xytext=(3180, 0.096),
        arrowprops={"arrowstyle": "->", "color": "#6f4e7c", "lw": 1.1},
        fontsize=9,
        color="#402949",
    )
    comparison_text = (
        "At latest official cumulative capacity (~2.97 TW, end-2025):\n"
        f"  20%/doubling path -> ${owid_at_2025:.3f}/W\n"
        f"  44%/doubling path -> ${handmer_at_2025:.3f}/W\n"
        f"  15%/yr from Q3 2024 -> ${fifteen_percent_annual_at_june_2026:.3f}/W\n"
        f"  June 2026 InfoLink TOPCon -> ${infolink_june_2026_topcon_usd_w:.3f}/W"
    )
    ax.text(
        1840,
        0.058,
        comparison_text,
        fontsize=9,
        linespacing=1.35,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": "#d0d0d0",
            "linewidth": 0.9,
        },
    )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1780, 3900)
    ax.set_ylim(0.045, 0.22)
    ax.set_xticks([1800, 2276, 2974, 3600])
    ax.set_xticklabels(["1.8 TW", "2.276 TW\nend-2024", "2.974 TW\nend-2025", "3.6 TW"])
    ax.set_yticks([0.05, 0.08, 0.10, 0.116, 0.126, 0.16, 0.20])
    ax.set_yticklabels(["$0.05", "$0.08", "$0.10", "$0.116", "$0.126", "$0.16", "$0.20"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", color="#dddddd", linewidth=0.9)
    ax.grid(True, which="minor", color="#eeeeee", linewidth=0.45, alpha=0.45)

    fig.suptitle(
        "Solar PV module learning curve: 2026 spot update",
        x=0.08,
        y=0.955,
        ha="left",
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.08,
        0.918,
        "Institutional annual history runs through 2024; 2026 dots are spot-market overlays, not annual institutional observations.",
        fontsize=10,
        color="#555555",
        ha="left",
    )
    ax.set_xlabel("Cumulative installed PV capacity, log scale")
    ax.set_ylabel("PV module price, USD/W, log scale")
    ax.legend(loc="upper right", frameon=True, framealpha=1, facecolor="white", edgecolor="#d0d0d0", fontsize=8.5)

    caption = (
        "Sources: OWID: long-run solar module prices fell around 20% per cumulative-capacity doubling.\n"
        "DOE/NREL: Q3 2024 module prices stayed near record lows around $0.10/Wdc.\n"
        "IEA PVPS Snapshot 2026: global PV rose from 2,276 GW in 2024 to ~3 TW after 698 GW installed in 2025.\n"
        "InfoLink June 2026: TOPCon averages are $0.116/W non-China and $0.126/W Europe FOB; U.S.-assembled DDP is $0.310/W.\n"
        "2026 dots are plotted at latest official cumulative capacity because no official mid-2026 global cumulative capacity series exists yet."
    )
    fig.text(0.08, 0.035, caption, fontsize=7.4, color="#5e5e5e", ha="left", va="bottom")
    fig.subplots_adjust(left=0.08, right=0.985, top=0.86, bottom=0.27)

    fig.savefig(OUT)
    print(f"Wrote {OUT}")
    print(f"20% path at end-2025 capacity: ${owid_at_2025:.3f}/W")
    print(f"44% path at end-2025 capacity: ${handmer_at_2025:.3f}/W")
    print(f"15%/yr path from Q3 2024 to Jun 2026: ${fifteen_percent_annual_at_june_2026:.3f}/W")
    print(f"InfoLink Jun 2026 non-China TOPCon spot: ${infolink_june_2026_topcon_usd_w:.3f}/W")


if __name__ == "__main__":
    main()
