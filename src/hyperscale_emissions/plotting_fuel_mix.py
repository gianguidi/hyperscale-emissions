from __future__ import annotations

from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from .fuel_mix import ALL_FUELS, FOSSIL_FUELS, NUCLEAR, RENEWABLES, compute_regional_fuel_mix
from .utils import ensure_dir

FUEL_COLORS: Dict[str, str] = {
    "COAL": "#6b1d1d",
    "GAS": "#f28e2b",
    "OIL": "#d62728",
    "OFSL": "#76b7b2",
    "OTHF": "#59a14f",
    "NUCLEAR": "#ffd92f",
    "BIOMASS": "#1a9850",
    "GEOTHERMAL": "#66bd63",
    "HYDRO": "#2166ac",
    "SOLAR": "#fdbf6f",
    "WIND": "#85c1a8",
}


def plot_figure4_fuel_mix(
    fuel_mix_hyperscalers: pd.DataFrame,
    national_total_twh: float = 81.8,
    save_path: str | None = None,
    top_n_regions: int = 7,
    show: bool = False,
) -> None:
    """Produce the manuscript Figure 4 fuel-mix chart."""
    fuel_columns = ALL_FUELS
    regional_with_us, total_twh, _national_mix, group_shares_us = compute_regional_fuel_mix(
        fuel_mix_hyperscalers=fuel_mix_hyperscalers,
        fuel_cols=fuel_columns,
        national_total_twh=national_total_twh,
        top_n_regions=top_n_regions,
    )

    fig, ax = plt.subplots(figsize=(15, 9))
    regional_with_us.plot(
        kind="barh",
        stacked=True,
        color=[FUEL_COLORS[f] for f in regional_with_us.columns],
        ax=ax,
        edgecolor="none",
        width=0.72,
    )

    for i, region in enumerate(regional_with_us.index):
        twh = total_twh.loc[region]
        ax.text(1.02, i, f"{twh:,.2f} TWh", va="center", ha="left", fontsize=11,
                fontweight="bold", transform=ax.get_yaxis_transform())

    for i, region in enumerate(regional_with_us.index):
        cumulative = 0.0
        for fuel, value in regional_with_us.loc[region].items():
            pct = value * 100
            if pct >= 4:
                ax.text(cumulative + value / 2, i, f"{pct:.1f}%", ha="center", va="center",
                        fontsize=9, color="white", fontweight="bold")
            cumulative += value

    group_shares = pd.DataFrame(index=regional_with_us.index)
    group_shares["Fossil"] = regional_with_us[FOSSIL_FUELS].sum(axis=1)
    group_shares["Nuclear"] = regional_with_us[NUCLEAR].sum(axis=1)
    group_shares["Renewables"] = regional_with_us[RENEWABLES].sum(axis=1)
    for i, region in enumerate(regional_with_us.index):
        summary = (
            f"Fossil {group_shares.loc[region, 'Fossil']*100:.1f}%   |   "
            f"Nuclear {group_shares.loc[region, 'Nuclear']*100:.1f}%   |   "
            f"Renewables {group_shares.loc[region, 'Renewables']*100:.1f}%"
        )
        ax.text(0.5, i + 0.30, summary, ha="center", va="bottom", fontsize=10)

    ax.set_xlim(0, 1)
    ax.set_xlabel("Fuel mix share")
    ax.set_ylabel("US and balancing authority")
    ax.set_yticklabels(regional_with_us.index, fontweight="bold")
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)

    handles = []
    labels = []

    def add_heading(text: str) -> None:
        handles.append(Line2D([], [], linestyle="none"))
        labels.append(text)

    add_heading(f"Fossil fuels ({group_shares_us['fossil']*100:.1f}%)")
    for fuel in FOSSIL_FUELS:
        handles.append(Line2D([0], [0], marker="s", markersize=10, color="none", markerfacecolor=FUEL_COLORS[fuel]))
        labels.append(f" {fuel}")
    add_heading(f"Nuclear ({group_shares_us['nuclear']*100:.1f}%)")
    for fuel in NUCLEAR:
        handles.append(Line2D([0], [0], marker="s", markersize=10, color="none", markerfacecolor=FUEL_COLORS[fuel]))
        labels.append(f" {fuel}")
    add_heading(f"Renewables ({group_shares_us['renewables']*100:.1f}%)")
    for fuel in RENEWABLES:
        handles.append(Line2D([0], [0], marker="s", markersize=10, color="none", markerfacecolor=FUEL_COLORS[fuel]))
        labels.append(f" {fuel}")

    ax.legend(handles, labels, bbox_to_anchor=(1.16, 0.5), loc="center left", frameon=False,
              title="Fuel groups & types", title_fontsize=12, fontsize=10)
    fig.tight_layout()
    if save_path is not None:
        ensure_dir(str(save_path).rsplit("/", 1)[0])
        fig.savefig(save_path, format="pdf", bbox_inches="tight", dpi=300)
        fig.savefig(str(save_path).replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
    if show:
        plt.show()
    plt.close(fig)
