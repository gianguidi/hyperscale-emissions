from __future__ import annotations

from typing import Dict

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D
import pandas as pd

from .fuel_mix import (
    FOSSIL_FUELS,
    NUCLEAR,
    RENEWABLES,
    ALL_FUELS,
    compute_regional_fuel_mix,
)
from .utils import ensure_dir


def plot_figure4_fuel_mix(
    fuel_mix_hyperscalers: pd.DataFrame,
    national_total_twh: float = 93.66,
    save_path: str | None = None,
):
    """Produce the final Figure 4 fuel-mix chart."""
    mpl.rcParams.update(
        {
            "font.size": 44,
            "axes.titlesize": 48,
            "axes.titleweight": "bold",
            "axes.labelsize": 44,
            "axes.labelweight": "bold",
            "legend.fontsize": 38,
            "xtick.labelsize": 38,
            "ytick.labelsize": 38,
            "font.family": "DejaVu Sans",
            "figure.figsize": (40, 24),
            "axes.grid": False,
        }
    )

    fuel_columns = ALL_FUELS

    (regional_with_us,
     total_twh_with_national,
     national_mix,
     group_shares_us) = compute_regional_fuel_mix(
        fuel_mix_hyperscalers=fuel_mix_hyperscalers,
        fuel_cols=fuel_columns,
        national_total_twh=national_total_twh,
    )

    fossil_share = group_shares_us["fossil"]
    nuclear_share = group_shares_us["nuclear"]
    renewable_share = group_shares_us["renewables"]

    fuel_colors: Dict[str, str] = {
        "COAL": "#8B1A1A",
        "GAS": "#F28E2B",
        "OIL": "#E15759",
        "OFSL": "#C76B47",
        "OTHF": "#A0522D",
        "NUCLEAR": "#F1C232",
        "BIOMASS": "#1A9850",
        "GEOTHERMAL": "#66BD63",
        "HYDRO": "#3288BD",
        "SOLAR": "#FDBF6F",
        "WIND": "#31A354",
    }

    fig, ax = plt.subplots(figsize=(40, 24))

    regional_with_us.plot(
        kind="barh",
        stacked=True,
        color=[fuel_colors[f] for f in regional_with_us.columns],
        ax=ax,
        edgecolor="none",
        linewidth=0.0,
    )

    # TWh labels on the right
    for i, region in enumerate(regional_with_us.index):
        twh = total_twh_with_national.loc[region]
        ax.text(
            1.02,
            i,
            f"{twh:,.2f} TWh",
            va="center",
            ha="left",
            fontsize=42,
            fontweight="bold",
            transform=ax.get_yaxis_transform(),
        )

    # Per-segment labels ≥ 5%
    for i, region in enumerate(regional_with_us.index):
        row = regional_with_us.loc[region]
        cumulative = 0.0
        for fuel, value in row.items():
            pct = value * 100
            if pct >= 5:
                x_center = cumulative + value / 2
                ax.text(
                    x_center,
                    i,
                    f"{pct:.1f}%",
                    ha="center",
                    va="center",
                    fontsize=34,
                    color="white",
                    fontweight="bold",
                )
            cumulative += value

    # Group summary text above each bar
    group_shares = pd.DataFrame(index=regional_with_us.index)
    group_shares["Fossil"] = regional_with_us[FOSSIL_FUELS].sum(axis=1)
    group_shares["Nuclear"] = regional_with_us[NUCLEAR].sum(axis=1)
    group_shares["Renewables"] = regional_with_us[RENEWABLES].sum(axis=1)

    for i, region in enumerate(regional_with_us.index):
        fossil_pct = group_shares.loc[region, "Fossil"] * 100
        nuclear_pct = group_shares.loc[region, "Nuclear"] * 100
        renew_pct = group_shares.loc[region, "Renewables"] * 100

        summary = (
            f"Fossil {fossil_pct:.1f}%   |   "
            f"Nuclear {nuclear_pct:.1f}%   |   "
            f"Renewables {renew_pct:.1f}%"
        )
        ax.text(0.5, i + 0.32, summary, ha="center", va="bottom", fontsize=36)

    ax.set_xlim(0, 1)
    ax.set_xlabel("Fuel mix share", labelpad=25)
    ax.set_ylabel(
        "US and balancing authority",
        rotation="vertical",
        labelpad=25,
    )
    ax.set_yticklabels(regional_with_us.index, fontweight="bold")

    # Grouped legend
    handles = []
    labels = []

    def add_group_heading(label_text: str):
        handles.append(Line2D([], [], linestyle="none"))
        labels.append(label_text)

    add_group_heading(f"Fossil fuels ({fossil_share*100:.1f}%)")
    for f in FOSSIL_FUELS:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="s",
                markersize=18,
                color="none",
                markerfacecolor=fuel_colors[f],
            )
        )
        labels.append(f"   {f}")

    add_group_heading(f"Nuclear ({nuclear_share*100:.1f}%)")
    for f in NUCLEAR:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="s",
                markersize=18,
                color="none",
                markerfacecolor=fuel_colors[f],
            )
        )
        labels.append(f"   {f}")

    add_group_heading(f"Renewables ({renewable_share*100:.1f}%)")
    for f in RENEWABLES:
        handles.append(
            Line2D(
                [0],
                [0],
                marker="s",
                markersize=18,
                color="none",
                markerfacecolor=fuel_colors[f],
            )
        )
        labels.append(f"   {f}")

    ax.legend(
        handles,
        labels,
        bbox_to_anchor=(1.20, 0.5),
        loc="center left",
        frameon=False,
        title="Fuel groups & types",
        title_fontsize=42,
        handlelength=1.2,
    )

    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    if save_path is not None:
        ensure_dir(save_path.rsplit("/", 1)[0])
        plt.savefig(save_path, format="pdf", bbox_inches="tight")
    plt.show()
