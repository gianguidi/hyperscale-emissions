#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.validation import run_grouped_cv, run_random_split  # noqa: E402

DATA_FILE = ROOT / "data" / "processed" / "all_facilities.csv"
OUTDIR = ROOT / "results" / "tables"
OUTDIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(f"Missing input: {DATA_FILE}\nSee REPRO.md for schema.")
    df = pd.read_csv(DATA_FILE)

    random_preds, random_out = run_random_split(df)
    random_preds.to_csv(OUTDIR / "validation_random_predictions.csv", index=False)
    pd.DataFrame([random_out["metrics"]]).to_csv(OUTDIR / "validation_random_metrics.csv", index=False)

    artifacts = {"random": random_out["splits"]}
    for group_col, stem in [("region_B_1", "ba"), ("state", "state"), ("climate_category", "climate")]:
        if group_col not in df.columns:
            print(f"Skipping {stem}: missing {group_col}")
            continue
        preds, per_group, out = run_grouped_cv(df, group_col=group_col, min_group_size=3)
        preds.to_csv(OUTDIR / f"validation_{stem}_predictions.csv", index=False)
        per_group.to_csv(OUTDIR / f"validation_{stem}_per_group.csv", index=False)
        pd.DataFrame([out["metrics"]]).to_csv(OUTDIR / f"validation_{stem}_metrics.csv", index=False)
        artifacts[stem] = out["splits"]

    with open(OUTDIR / "splits.json", "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2)
    print(f"Validation outputs written to {OUTDIR}")


if __name__ == "__main__":
    main()
