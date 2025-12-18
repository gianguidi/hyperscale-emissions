from __future__ import annotations

import pandas as pd

from hyperscale_emissions.plotting_fuel_mix import plot_figure4_fuel_mix


DATA_PATH = "data/processed/fuel_mix_hyperscalers.csv"


def main():
    df_fuel = pd.read_csv(DATA_PATH)

    plot_figure4_fuel_mix(
        fuel_mix_hyperscalers=df_fuel,
        national_total_twh=93.66,
        save_path="results/figures/figure4_fuel_mix_GROUPED_final.pdf",
    )


if __name__ == "__main__":
    main()
