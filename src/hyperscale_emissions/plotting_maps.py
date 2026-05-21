from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

try:
    import geopandas as gpd
except Exception as exc:  # pragma: no cover
    gpd = None
    _GPD_IMPORT_ERROR = exc
else:
    _GPD_IMPORT_ERROR = None

from .utils import ensure_dir, first_existing_column

CRS_ALBERS = "EPSG:5070"
CRS_LATLON = "EPSG:4326"

FUEL_ORDER = ["COAL", "GAS", "OIL", "OFSL", "OTHF", "NUCLEAR", "BIOMASS", "GEOTHERMAL", "HYDRO", "SOLAR", "WIND"]
FUEL_COLORS = {
    "COAL": "#5b1a1a",       # dark brown-red
    "GAS": "#ff9f1c",        # orange
    "OIL": "#d62728",        # red
    "OFSL": "#76b7b2",       # teal
    "OTHF": "#59a14f",       # green
    "NUCLEAR": "#ffe45e",    # bright yellow
    "BIOMASS": "#9467bd",    # purple
    "GEOTHERMAL": "#e377c2", # pink
    "HYDRO": "#1f77b4",      # blue
    "SOLAR": "#fddc5c",      # pale yellow
    "WIND": "#2ca02c",       # green
}


def _require_geopandas() -> None:
    if gpd is None:
        raise ImportError(f"geopandas is required for map figures: {_GPD_IMPORT_ERROR}")


def _read_geo(path: str | Path):
    _require_geopandas()
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_LATLON)
    return gdf.to_crs(CRS_ALBERS)


def _scale_marker_area(values: pd.Series, min_area: float = 8, max_area: float = 70) -> pd.Series:
    log_values = np.log10(pd.to_numeric(values, errors="coerce").fillna(0).clip(lower=0) + 1.0)
    q05, q95 = log_values.quantile([0.05, 0.95])
    denom = max(float(q95 - q05), 1e-9)
    return min_area + ((log_values.clip(q05, q95) - q05) / denom) * (max_area - min_area)


def plot_figure1a_hyperscalers(
    df_emissions_per_dc_SF_path: str = "data/processed/df_emissions_per_dc_SF.geojson",
    gdf_EPA_totals_path: str = "data/processed/gdf_EPA_totals.geojson",
    output_path: str = "results/figures/figure1a_hyperscalers.pdf",
    show: bool = False,
) -> None:
    """Map HDCs by power-capacity quartile."""
    _require_geopandas()
    dc = _read_geo(df_emissions_per_dc_SF_path)
    ba = _read_geo(gdf_EPA_totals_path)
    cap_col = first_existing_column(dc, ["current_mw", "Total_MW", "capacity_mw"], "facility capacity")
    caps = pd.to_numeric(dc[cap_col], errors="coerce")
    q = caps.quantile([0.25, 0.50, 0.75]).values
    dc["quartile"] = pd.cut(caps, bins=[-np.inf, q[0], q[1], q[2], np.inf], labels=["Q1", "Q2", "Q3", "Q4"])
    colors = {"Q1": "#1f4e79", "Q2": "#7fb3d5", "Q3": "#1d8348", "Q4": "#a3a300"}

    fig, ax = plt.subplots(figsize=(13, 8))
    ba.plot(ax=ax, color="#f2f2f2", edgecolor="#aaaaaa", linewidth=0.35, zorder=0)
    for quartile in ["Q1", "Q2", "Q3", "Q4"]:
        sub = dc.loc[dc["quartile"] == quartile]
        if not sub.empty:
            sub.plot(ax=ax, color=colors[quartile], markersize=22, alpha=0.92,
                     edgecolor="white", linewidth=0.3, zorder=3)
    ax.set_title("a. Hyperscale data centers\n(colour = power capacity quartile)", fontsize=12,
                 fontweight="bold", loc="left")
    ax.axis("off")
    labels = {
        "Q1": f"<= {q[0]:.0f} MW",
        "Q2": f"{q[0]:.0f}-{q[1]:.0f} MW",
        "Q3": f"{q[1]:.0f}-{q[2]:.0f} MW",
        "Q4": f"> {q[2]:.0f} MW",
    }
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=colors[k],
                      markeredgecolor="white", markersize=9, label=labels[k]) for k in ["Q1", "Q2", "Q3", "Q4"]]
    ax.legend(handles=handles, title="Power capacity", loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    fig.tight_layout()
    ensure_dir(Path(output_path).parent)
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    fig.savefig(str(output_path).replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
    if show:
        plt.show()
    plt.close(fig)


def _prepare_plant_points(plants: pd.DataFrame, aggregate_by_operator: bool = True) -> pd.DataFrame:
    lat = first_existing_column(plants, ["LAT", "Plant latitude", "latitude"], "plant latitude")
    lon = first_existing_column(plants, ["LON", "Plant longitude", "longitude"], "plant longitude")
    gen = first_existing_column(plants, ["PLNGENAN", "Plant annual net generation (MWh)"], "plant annual generation")
    fuel = first_existing_column(plants, ["PLFUELCT", "Plant primary fuel category"], "plant primary fuel")

    out = plants[[lat, lon, gen, fuel] + (["OPRCODE"] if "OPRCODE" in plants.columns else [])].copy()
    out = out.rename(columns={lat: "lat", lon: "lon", gen: "generation_mwh", fuel: "fuel"})
    out["generation_mwh"] = pd.to_numeric(out["generation_mwh"], errors="coerce")
    out["fuel"] = out["fuel"].astype(str).str.upper().str.strip()
    out = out.dropna(subset=["lat", "lon", "generation_mwh"])
    out = out.loc[out["generation_mwh"] > 0].copy()

    if aggregate_by_operator and "OPRCODE" in out.columns:
        group_cols = ["OPRCODE", "fuel"]
        grouped = out.groupby(group_cols, as_index=False).agg(
            generation_mwh=("generation_mwh", "sum"),
            lat=("lat", "mean"),
            lon=("lon", "mean"),
        )
        out = grouped
    return out


def plot_figure1b_power_plants(
    plants_with_regions_path: str = "data/processed/plants_with_regions.csv",
    gdf_EPA_totals_path: str = "data/processed/gdf_EPA_totals.geojson",
    output_path: str = "results/figures/figure1b_power_plants.pdf",
    show: bool = False,
) -> None:
    """Map plant/operator-fuel records by primary fuel, keeping top 75% by generation."""
    _require_geopandas()
    plants = pd.read_csv(plants_with_regions_path)
    plants = _prepare_plant_points(plants, aggregate_by_operator=True)
    threshold = plants["generation_mwh"].quantile(0.25)
    plants = plants.loc[plants["generation_mwh"] >= threshold].copy()
    plants["size"] = _scale_marker_area(plants["generation_mwh"], min_area=7, max_area=60)

    plant_gdf = gpd.GeoDataFrame(plants, geometry=gpd.points_from_xy(plants["lon"], plants["lat"]), crs=CRS_LATLON).to_crs(CRS_ALBERS)
    ba = _read_geo(gdf_EPA_totals_path)

    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("#fbfbf7")
    ax.set_facecolor("#fbfbf7")
    ba.plot(ax=ax, color="#eeeeea", edgecolor="#b5b5b5", linewidth=0.35, zorder=0)
    for fuel in FUEL_ORDER:
        sub = plant_gdf.loc[plant_gdf["fuel"] == fuel]
        if not sub.empty:
            sub.plot(ax=ax, color=FUEL_COLORS.get(fuel, "#888888"), markersize=sub["size"], marker="s",
                     alpha=0.85, edgecolor="white", linewidth=0.15, zorder=3)

    ax.set_title("b. Power plants by primary fuel\n(top 75% by annual generation)", fontsize=12,
                 fontweight="bold", loc="left")
    ax.axis("off")
    handles = [Line2D([0], [0], marker="s", color="w", markerfacecolor=FUEL_COLORS[f],
                      markeredgecolor="white", markersize=8, label=f) for f in FUEL_ORDER if f in set(plant_gdf["fuel"])]
    ax.legend(handles=handles, title="Primary fuel type", loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=9, title_fontsize=10)
    fig.tight_layout()
    ensure_dir(Path(output_path).parent)
    fig.savefig(output_path, bbox_inches="tight", dpi=300)
    fig.savefig(str(output_path).replace(".pdf", ".png"), bbox_inches="tight", dpi=300)
    if show:
        plt.show()
    plt.close(fig)
