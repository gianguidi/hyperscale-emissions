#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
import os
import sys

# ------------------------------------------------------------------
# Ensure the src/ directory is on sys.path so we can import the
# hyperscale_emissions package without installing it.
# ------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from hyperscale_emissions.plotting_maps import (
    plot_figure1a_hyperscalers,
    plot_figure1b_power_plants,
)

from hyperscale_emissions.plotting_maps import plot_figure1a_hyperscalers, plot_figure1b_power_plants  # noqa: E402


def main() -> None:
    plot_figure1a_hyperscalers(
        df_emissions_per_dc_SF_path=str(ROOT / "data" / "processed" / "df_emissions_per_dc_SF.geojson"),
        gdf_EPA_totals_path=str(ROOT / "data" / "processed" / "gdf_EPA_totals.geojson"),
        output_path=str(ROOT / "results" / "figures" / "figure1a_hyperscalers.pdf"),
    )
    plot_figure1b_power_plants(
        plants_with_regions_path=str(ROOT / "data" / "processed" / "plants_with_regions.csv"),
        gdf_EPA_totals_path=str(ROOT / "data" / "processed" / "gdf_EPA_totals.geojson"),
        output_path=str(ROOT / "results" / "figures" / "figure1b_power_plants.pdf"),
    )


if __name__ == "__main__":
    main()
