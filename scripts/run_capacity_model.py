#!/usr/bin/env python3
from __future__ import annotations

import os
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

PROCESSED_DATA_PATH = ROOT / "data" / "processed" / "all_facilities.csv"
SYNTHETIC_DATA_PATH = ROOT / "data" / "synthetic" / "all_facilities.csv"
OUT_FIG = ROOT / "results" / "figures" / "hyp_model_performance.pdf"
OUT_DATA = ROOT / "data" / "processed" / "facilities_with_predicted_capacity.csv"


def resolve_data_path() -> Path:
    """Return an available facility dataset, preferring processed data."""
    override = os.environ.get("HYPERSCALE_FACILITIES_PATH")

    candidates = (
        [Path(override).expanduser()]
        if override
        else [
            PROCESSED_DATA_PATH,
            SYNTHETIC_DATA_PATH,
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    expected = ", ".join(str(candidate) for candidate in candidates)
    raise SystemExit(
        "Missing facility input. Checked: "
        f"{expected}\n"
        "Run scripts/make_synthetic_403_fixture.py or see REPRO.md."
    )


def main() -> None:
    data_path = resolve_data_path()
    print(f"Input data: {data_path}")
    df = pd.read_csv(data_path)
    cfg = CapacityModelConfig()
    df_with, _ = split_with_and_without_power(df, target="current_mw")
    results = train_capacity_model(df_with, cfg)
    for key, value in results.metrics.items():
        print(f"{key}: {value:.4f}")
    plot_predicted_vs_observed(results, out_path=str(OUT_FIG))
    df_with_predictions = predict_missing_capacity(df, cfg, results)
    n_imputed = int(
        df_with_predictions["is_imputed_capacity"].sum()
    )
    print(
        f"Imputed capacities: {n_imputed} "
        f"of {len(df_with_predictions)}"
    )
    ensure_dir(OUT_DATA.parent)
    df_with_predictions.to_csv(OUT_DATA, index=False)
    print(f"Wrote {OUT_DATA}")


if __name__ == "__main__":
    main()
