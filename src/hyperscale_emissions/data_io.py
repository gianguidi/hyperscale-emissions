from __future__ import annotations

from pathlib import Path
import pandas as pd
import geopandas as gpd


def load_csv(path: str | Path) -> pd.DataFrame:
    """Simple CSV loader with a consistent interface."""
    return pd.read_csv(path)


def load_geodata(path: str | Path) -> gpd.GeoDataFrame:
    """Load a geospatial file (e.g. Shapefile, GeoPackage, GeoJSON)."""
    return gpd.read_file(path)
