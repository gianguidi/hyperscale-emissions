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


def main():
    # Default paths – these assume you run from the repo root
    df_emissions_per_dc_SF_path = "data/processed/df_emissions_per_dc_SF.geojson"
    gdf_EPA_totals_path = "data/processed/gdf_EPA_totals.geojson"
    plants_with_regions_path = "data/processed/plants_with_regions.csv"

    # Figure 1a
    plot_figure1a_hyperscalers(
        df_emissions_per_dc_SF_path=df_emissions_per_dc_SF_path,
        gdf_EPA_totals_path=gdf_EPA_totals_path,
        output_path="results/figures/figure1a_hyperscalers.pdf",
        show=True,
    )

    # Figure 1b
    plot_figure1b_power_plants(
        plants_with_regions_path=plants_with_regions_path,
        gdf_EPA_totals_path=gdf_EPA_totals_path,
        output_path="results/figures/figure1b_power_plants.pdf",
        show=True,
    )


if __name__ == "__main__":
    main()
