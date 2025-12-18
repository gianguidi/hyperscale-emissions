"""
Plotting functions for Figure 1:
- Figure 1a: Hyperscale data centers (dot size ∝ power capacity)
- Figure 1b: Power plants by primary fuel (top 75% by annual generation)

Data expectations (all paths relative to repo root by default):

1. df_emissions_per_dc_SF_path (GeoJSON)
   - geometry (Point, in EPSG:4326 or convertible)
   - current_mw (float): IT power capacity in MW

2. gdf_EPA_totals_path (GeoJSON)
   - geometry (Polygon/MultiPolygon of balancing authorities)
   - CRS convertible to EPSG:5070

3. plants_with_regions_path (CSV)
   - Plant latitude (float)
   - Plant longitude (float)
   - Plant annual net generation (MWh) (float)
   - Plant primary fuel category (str)

All figures are saved into results/figures/.
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from shapely.geometry import Point
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# -------------------------------------------------------------------
# Global style (Nature-ish, big & clean)
# -------------------------------------------------------------------
mpl.rcParams.update({
    "font.size": 52,
    "axes.titlesize": 56,
    "axes.titleweight": "normal",
    "legend.fontsize": 60,
    "font.family": "DejaVu Sans",
})

CRS_ALBERS = "EPSG:5070"
CRS_LATLON = "EPSG:4326"

# Fuel colours (harmonised with other figures)
FUEL_COLORS = {
    "COAL":       "#A40000",
    "GAS":        "#F28E2B",
    "OIL":        "#E15759",
    "OFSL":       "#76B7B2",
    "OTHF":       "#59A14F",
    "NUCLEAR":    "#EDC948",
    "BIOMASS":    "#B07AA1",
    "GEOTHERMAL": "#FF9DA7",
    "HYDRO":      "#9C755F",
    "SOLAR":      "#BAB0AC",
    "WIND":       "#86BCB6",
}


# -------------------------------------------------------------------
# Helper: ensure output directory
# -------------------------------------------------------------------
def _ensure_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


# -------------------------------------------------------------------
# Helper: scale marker AREA (points^2) from a fixed MW range
# -------------------------------------------------------------------
def scale_size_from_range(values, vmin, vmax, min_area=400, max_area=2500):
    """
    Map capacity values to marker areas in points^2, given a fixed
    [vmin, vmax] range.

    Parameters
    ----------
    values : array-like
        Capacity values (e.g., MW).
    vmin, vmax : float
        Minimum and maximum values of capacity used for scaling.
    min_area, max_area : float
        Marker areas (points^2) corresponding to vmin and vmax.

    Returns
    -------
    np.ndarray of areas (points^2).
    """
    vals = np.asarray(values, dtype=float)
    vals = np.clip(vals, vmin, vmax)
    norm = (vals - vmin) / (vmax - vmin + 1e-9)
    return min_area + norm * (max_area - min_area)


# -------------------------------------------------------------------
# Figure 1a – Hyperscale data centers
# -------------------------------------------------------------------
def plot_figure1a_hyperscalers(
    df_emissions_per_dc_SF_path: str = "data/processed/df_emissions_per_dc_SF.geojson",
    gdf_EPA_totals_path: str = "data/processed/gdf_EPA_totals.geojson",
    output_path: str = "results/figures/figure1a_hyperscalers.pdf",
    show: bool = True,
):
    """
    Figure 1a: map of hyperscale data centers.
    - Dot size ∝ power capacity (MW)
    - Legend shows 10 / 50 / 100 MW categories (proportional)

    Parameters
    ----------
    df_emissions_per_dc_SF_path : str
        Path to GeoJSON with data center geometries and current_mw.
    gdf_EPA_totals_path : str
        Path to GeoJSON with balancing authority polygons.
    output_path : str
        Path to save the PDF figure.
    show : bool
        Whether to display the figure interactively.
    """
    # ----------------- Load data -----------------
    df_emissions_per_dc_SF = gpd.read_file(df_emissions_per_dc_SF_path)
    gdf_EPA_totals = gpd.read_file(gdf_EPA_totals_path)

    # Ensure CRS
    if df_emissions_per_dc_SF.crs is None:
        df_emissions_per_dc_SF = df_emissions_per_dc_SF.set_crs(CRS_LATLON)
    if gdf_EPA_totals.crs is None:
        gdf_EPA_totals = gdf_EPA_totals.set_crs(CRS_LATLON)

    df_emissions_per_dc_SF = df_emissions_per_dc_SF.to_crs(CRS_ALBERS)
    gdf_EPA_totals = gdf_EPA_totals.to_crs(CRS_ALBERS)

    # ----------------- Capacity scaling (fixed bins) -----------------
    caps = df_emissions_per_dc_SF["current_mw"].astype(float)
    CAP_MIN = 10.0
    CAP_MAX = 100.0
    dc_areas = scale_size_from_range(caps, CAP_MIN, CAP_MAX)

    legend_caps = [10, 50, 100]

    # ----------------- Figure -----------------
    plt.close("all")
    fig1, ax1 = plt.subplots(figsize=(40, 24))

    # Background: BA polygons with strong borders
    gdf_EPA_totals.plot(
        ax=ax1,
        color="#f0f0f0",
        edgecolor="#666666",
        linewidth=1.2,
        zorder=0,
    )

    # Hyperscale dots
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

    # Title in top-left of the figure
    fig1.text(
        0.01,
        0.97,
        "a.  Hyperscale data centers\n(dot size ∝ power capacity)",
        ha="left",
        va="top",
        fontsize=56,
    )

    # Legend: 10 / 50 / 100 MW, with proportional radii
    dc_legend_handles = []
    for cap in legend_caps:
        area = scale_size_from_range([cap], CAP_MIN, CAP_MAX)[0]
        r = np.sqrt(area) * 1.2  # slight boost so legend dots are visually clear
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

    # Save
    _ensure_dir(output_path)
    fig1.savefig(output_path, bbox_inches="tight", dpi=300)

    if show:
        plt.show()


# -------------------------------------------------------------------
# Figure 1b – Power plants by primary fuel (top 75% by generation)
# -------------------------------------------------------------------
def plot_figure1b_power_plants(
    plants_with_regions_path: str = "data/processed/plants_with_regions.csv",
    gdf_EPA_totals_path: str = "data/processed/gdf_EPA_totals.geojson",
    output_path: str = "results/figures/figure1b_power_plants.pdf",
    show: bool = True,
):
    """
    Figure 1b: map of power plants by primary fuel, showing only
    the top 75% of plants by annual generation.

    - Each plant is a square marker
    - Colour encodes primary fuel type
    - Marker size ∝ log(annual generation)
    - Balancing authorities shown as background polygons

    Parameters
    ----------
    plants_with_regions_path : str
        Path to CSV with plant locations and annual generation.
    gdf_EPA_totals_path : str
        Path to GeoJSON with balancing authority polygons.
    output_path : str
        Path to save the PDF figure.
    show : bool
        Whether to display the figure interactively.
    """
    # ----------------- Load data -----------------
    plants_df = pd.read_csv(plants_with_regions_path)

    # Build GeoDataFrame for plants (assumed lat/lon)
    plants_gdf = gpd.GeoDataFrame(
        plants_df,
        geometry=plants_df.apply(
            lambda row: Point(row["Plant longitude"], row["Plant latitude"]),
            axis=1,
        ),
        crs=CRS_LATLON,
    )

    gdf_EPA_totals = gpd.read_file(gdf_EPA_totals_path)
    if gdf_EPA_totals.crs is None:
        gdf_EPA_totals = gdf_EPA_totals.set_crs(CRS_LATLON)

    # Reproject
    plants_gdf = plants_gdf.to_crs(CRS_ALBERS)
    gdf_EPA_totals = gdf_EPA_totals.to_crs(CRS_ALBERS)

    # ----------------- Filter: top 75% by generation -----------------
    gen_series = plants_gdf["Plant annual net generation (MWh)"].astype(float)
    gen_threshold = gen_series.quantile(0.25)  # keep top 75%
    plants_plot = plants_gdf[gen_series >= gen_threshold].copy()

    # Scale plant marker areas by log(generation)
    plant_gen = np.log10(plants_plot["Plant annual net generation (MWh)"] + 1.0)
    pmin, pmax = plant_gen.quantile(0.05), plant_gen.quantile(0.95)
    plant_norm = (np.clip(plant_gen, pmin, pmax) - pmin) / (pmax - pmin + 1e-9)
    plant_areas = 80 + plant_norm * 500  # points^2

    # ----------------- Figure -----------------
    plt.close("all")
    fig2, ax2 = plt.subplots(figsize=(40, 24))

    # Background: BA polygons with visible borders
    gdf_EPA_totals.plot(
        ax=ax2,
        color="#f0f0f0",
        edgecolor="#666666",
        linewidth=1.2,
        zorder=0,
    )

    # Plants: coloured by fuel, sized by generation
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

    # Title on top-left of the figure
    fig2.text(
        0.01,
        0.97,
        "b.  Power plants by primary fuel\n(top 75% by annual generation)",
        ha="left",
        va="top",
        fontsize=56,
    )

    # Legend: one square per fuel present in data
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

    # Save
    _ensure_dir(output_path)
    fig2.savefig(output_path, bbox_inches="tight", dpi=300)

    if show:
        plt.show()
