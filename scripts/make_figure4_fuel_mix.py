from __future__ import annotations
import pandas as pd

import os
import sys

# ------------------------------------------------------------------
# Ensure src/ is on sys.path so we can import hyperscale_emissions
# without needing pip install -e .
# ------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

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
