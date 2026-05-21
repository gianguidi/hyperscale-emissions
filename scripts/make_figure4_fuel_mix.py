#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.plotting_fuel_mix import plot_figure4_fuel_mix  # noqa: E402

DATA_PATH = ROOT / "data" / "processed" / "fuel_mix_hyperscalers.csv"
OUT_PATH = ROOT / "results" / "figures" / "figure4_fuel_mix_GROUPED_final.pdf"


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing input: {DATA_PATH}\nSee REPRO.md for schema.")
    df_fuel = pd.read_csv(DATA_PATH)
    plot_figure4_fuel_mix(df_fuel, national_total_twh=81.8, save_path=str(OUT_PATH), show=False)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
