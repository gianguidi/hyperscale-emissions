from __future__ import annotations

from typing import Optional

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from shapely.geometry import Point
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from .utils import ensure_dir


CRS_ALBERS = "EPSG:5070"
CRS_LATLON = "EPSG:4326"


FUEL_COLORS = {
    "COAL": "#A40000",
    "GAS": "#F28E2B",
    "OIL": "#E15759",
    "OFSL": "#76B7B2",
    "OTHF": "#59A14F",
    "NUCLEAR": "#EDC948",
    "BIOMASS": "#B07AA1",
    "GEOTHERMAL": "#FF9DA7",
    "HYDRO": "#9C755F",
    "SOLAR": "#BAB0AC",
    "WIND": "#86BCB6",
}


def scale_size_from_range(
    values,
    vmin: float,
    vmax: float,
    min_area: float = 400,
    max_area: float = 2500,
):
    """Map capacity values to marker areas (points^2)."""
    vals = np.asarray(values, dtype=float)
    vals = np.clip(vals, vmin, vmax)
    norm = (vals - vmin) / (vmax - vmin + 1e-9)
    return min_area + norm * (max_area - min_area)


def prepare_plants_geodata(plants_df: pd.DataFrame) -> gpd.GeoDataFrame:
    """Convert plants DataFrame to GeoDataFrame and reproject."""
    plants_df = plants_df.copy()
    plants_df["geometry"] = plants_df.apply(
        lambda row: Point(row["Plant longitude"], row["Plant latitude"]),
        axis=1,
    )
    gdf = gpd.GeoDataFrame(plants_df, geometry="geometry", crs=CRS_LATLON)
    gdf = gdf.to_crs(CRS_ALBERS)
    return gdf


def plot_figure1a_hyperscalers(
    df_emissions_per_dc_SF: gpd.GeoDataFrame,
    gdf_EPA_totals: gpd.GeoDataFrame,
    out_path: Optional[str] = None,
):
    """Figure 1a: Hyperscale data centers (dot size ∝ power capacity)."""
    plt.close("all")

    mpl.rcParams.update(
        {
            "font.size": 52,
            "axes.titlesize": 56,
            "axes.titleweight": "normal",
            "legend.fontsize": 60,
            "font.family": "DejaVu Sans",
        }
    )

    gdf_EPA_totals = gdf_EPA_totals.to_crs(CRS_ALBERS)
    df_emissions_per_dc_SF = df_emissions_per_dc_SF.to_crs(CRS_ALBERS)

    caps = df_emissions_per_dc_SF["current_mw"]
    CAP_MIN = 10.0
    CAP_MAX = 100.0
    dc_areas = scale_size_from_range(caps, CAP_MIN, CAP_MAX)
    legend_caps = [10, 50, 100]

    fig1, ax1 = plt.subplots(figsize=(40, 24))

    gdf_EPA_totals.plot(
        ax=ax1,
        color="#f0f0f0",
        edgecolor="#555555",
        linewidth=1.2,
        zorder=0,
    )

    df_emissions_per_dc_SF.plot(
        ax=ax1,
        color="black",
        markersize=dc_areas,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )

    ax1.set_axis_off()

    fig1.text(
        0.01,
        0.97,
        "a.  Hyperscale data centers\n(dot size ∝ power capacity)",
        ha="left",
        va="top",
        fontsize=56,
    )

    dc_legend_handles = []
    for cap in legend_caps:
        area = scale_size_from_range([cap], CAP_MIN, CAP_MAX)[0]
        r = np.sqrt(area) * 1.2
        dc_legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor="black",
                markeredgecolor="white",
                markersize=r,
                label=f"{cap} MW",
            )
        )

    leg1 = ax1.legend(
        handles=dc_legend_handles,
        title="Power capacity",
        loc="center left",
        bbox_to_anchor=(1.02, 0.50),
        frameon=False,
        borderpad=1.0,
        labelspacing=1.5,
    )
    plt.setp(leg1.get_title(), fontsize=60)

    plt.tight_layout()

    if out_path is not None:
        ensure_dir(out_path.rsplit("/", 1)[0])
        fig1.savefig(out_path, bbox_inches="tight", dpi=300)

    plt.show(fig1)


def plot_figure1b_power_plants(
    plants_with_regions: gpd.GeoDataFrame,
    gdf_EPA_totals: gpd.GeoDataFrame,
    out_path: Optional[str] = None,
):
    """Figure 1b: Power plants by primary fuel (top 75% by annual generation)."""
    plt.close("all")

    mpl.rcParams.update(
        {
            "font.size": 52,
            "axes.titlesize": 56,
            "axes.titleweight": "normal",
            "legend.fontsize": 60,
            "font.family": "DejaVu Sans",
        }
    )

    gdf_EPA_totals = gdf_EPA_totals.to_crs(CRS_ALBERS)
    plants_with_regions = plants_with_regions.to_crs(CRS_ALBERS)

    gen_threshold = plants_with_regions["Plant annual net generation (MWh)"].quantile(
        0.25
    )
    plants_plot = plants_with_regions[
        plants_with_regions["Plant annual net generation (MWh)"] >= gen_threshold
    ].copy()

    plant_gen = np.log10(plants_plot["Plant annual net generation (MWh)"] + 1.0)
    pmin, pmax = plant_gen.quantile(0.05), plant_gen.quantile(0.95)
    plant_norm = (np.clip(plant_gen, pmin, pmax) - pmin) / (pmax - pmin + 1e-9)
    plant_areas = 80 + plant_norm * 500

    fig2, ax2 = plt.subplots(figsize=(40, 24))

    gdf_EPA_totals.plot(
        ax=ax2,
        color="#f0f0f0",
        edgecolor="#555555",
        linewidth=1.2,
        zorder=0,
    )

    for fuel, subset in plants_plot.groupby("Plant primary fuel category"):
        color = FUEL_COLORS.get(fuel, "#cccccc")
        areas = plant_areas[subset.index]
        subset.plot(
            ax=ax2,
            color=color,
            markersize=areas,
            marker="s",
            linewidth=0.4,
            edgecolor="white",
            alpha=0.95,
            zorder=4,
        )

    ax2.set_axis_off()

    fig2.text(
        0.01,
        0.97,
        "b.  Power plants by primary fuel\n(top 75% by annual generation)",
        ha="left",
        va="top",
        fontsize=56,
    )

    fuel_legend_handles = [
        Patch(facecolor=color, edgecolor="white", label=fuel)
        for fuel, color in FUEL_COLORS.items()
        if fuel in plants_plot["Plant primary fuel category"].unique()
    ]

    leg2 = ax2.legend(
        handles=fuel_legend_handles,
        title="Primary fuel type",
        loc="center left",
        bbox_to_anchor=(1.02, 0.50),
        frameon=False,
        borderpad=1.0,
        labelspacing=1.2,
    )
    plt.setp(leg2.get_title(), fontsize=60)

    plt.tight_layout()
    if out_path is not None:
        ensure_dir(out_path.rsplit("/", 1)[0])
        fig2.savefig(out_path, bbox_inches="tight", dpi=300)

    plt.show(fig2)
