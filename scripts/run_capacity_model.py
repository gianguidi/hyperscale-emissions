#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.capacity_model import (  # noqa: E402
    CapacityModelConfig,
    plot_predicted_vs_observed,
    predict_missing_capacity,
    split_with_and_without_power,
    train_capacity_model,
)
from hyperscale_emissions.utils import ensure_dir  # noqa: E402

DATA_PATH = ROOT / "data" / "processed" / "all_facilities.csv"
OUT_FIG = ROOT / "results" / "figures" / "hyp_model_performance.pdf"
OUT_DATA = ROOT / "data" / "processed" / "facilities_with_predicted_capacity.csv"


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing input: {DATA_PATH}\nSee REPRO.md for the required schema.")
    df = pd.read_csv(DATA_PATH)
    cfg = CapacityModelConfig()
    df_with, _ = split_with_and_without_power(df, target="current_mw")
    results = train_capacity_model(df_with, cfg)
    for key, value in results.metrics.items():
        print(f"{key}: {value:.4f}")
    plot_predicted_vs_observed(results, out_path=str(OUT_FIG))
    df_with_predictions = predict_missing_capacity(df, cfg, results)
    ensure_dir(OUT_DATA.parent)
    df_with_predictions.to_csv(OUT_DATA, index=False)
    print(f"Wrote {OUT_DATA}")


if __name__ == "__main__":
    main()
