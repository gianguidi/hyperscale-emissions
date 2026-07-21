#!/usr/bin/env python3
"""Run public model validation on synthetic data without restricted facility records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.validation import run_grouped_cv, run_random_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/synthetic/all_facilities.csv"),
        help="Synthetic public fixture or a local restricted facility CSV.",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("results/tables/synthetic_validation"),
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    args.outdir.mkdir(parents=True, exist_ok=True)

    random_preds, random_out = run_random_split(df)
    random_preds.to_csv(args.outdir / "validation_random_predictions.csv", index=False)
    pd.DataFrame([random_out["metrics"]]).to_csv(
        args.outdir / "validation_random_metrics.csv", index=False
    )
    artifacts = {"random": random_out["splits"]}

    for group_col, stem in [
        ("region_B_1", "ba"),
        ("state", "state"),
        ("climate_category", "climate"),
    ]:
        preds, per_group, out = run_grouped_cv(df, group_col=group_col, min_group_size=3)
        preds.to_csv(args.outdir / f"validation_{stem}_predictions.csv", index=False)
        per_group.to_csv(args.outdir / f"validation_{stem}_per_group.csv", index=False)
        pd.DataFrame([out["metrics"]]).to_csv(
            args.outdir / f"validation_{stem}_metrics.csv", index=False
        )
        artifacts[stem] = out["splits"]

    with (args.outdir / "splits_synthetic.json").open("w", encoding="utf-8") as handle:
        json.dump(artifacts, handle, indent=2)

    print(f"Synthetic validation outputs written to {args.outdir}")


if __name__ == "__main__":
    main()
