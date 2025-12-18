from __future__ import annotations

import geopandas as gpd
import pandas as pd

from hyperscale_emissions.plotting_maps import (
    plot_figure1a_hyperscalers,
    plot_figure1b_power_plants,
    prepare_plants_geodata,
)


def main():
    # Adjust these paths to your actual processed files.
    dc_path = "data/processed/df_emissions_per_dc_SF.geojson"
    ba_path = "data/processed/gdf_EPA_totals.geojson"
    plants_path = "data/processed/plants_with_regions.csv"

    df_dc = gpd.read_file(dc_path)
    gdf_ba = gpd.read_file(ba_path)
    plants_df = pd.read_csv(plants_path)

    gdf_plants = prepare_plants_geodata(plants_df)

    plot_figure1a_hyperscalers(
        df_emissions_per_dc_SF=df_dc,
        gdf_EPA_totals=gdf_ba,
        out_path="results/figures/figure1a_hyperscalers.pdf",
    )

    plot_figure1b_power_plants(
        plants_with_regions=gdf_plants,
        gdf_EPA_totals=gdf_ba,
        out_path="results/figures/figure1b_power_plants.pdf",
    )


if __name__ == "__main__":
    main()
