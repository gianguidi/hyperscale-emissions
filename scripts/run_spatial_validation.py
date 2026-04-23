from pathlib import Path
import json
import pandas as pd

from hyperscale_emissions.validation import run_random_split, run_grouped_cv

DATA_FILE = Path("data/processed/all_facilities.csv")
OUTDIR = Path("results/tables")
OUTDIR.mkdir(parents=True, exist_ok=True)

def main() -> None:
    df = pd.read_csv(DATA_FILE)

    random_preds, random_out = run_random_split(df)
    random_preds.to_csv(OUTDIR / "validation_random_predictions.csv", index=False)
    pd.DataFrame([random_out["metrics"]]).to_csv(OUTDIR / "validation_random_metrics.csv", index=False)

    artifacts = {"random": random_out["splits"]}

    for group_col, stem in [
        ("region_B_1", "ba"),
        ("state", "state"),
        ("climate_category", "climate"),
    ]:
        if group_col not in df.columns:
            continue

        preds, per_group, out = run_grouped_cv(df, group_col=group_col, min_group_size=3)
        preds.to_csv(OUTDIR / f"validation_{stem}_predictions.csv", index=False)
        per_group.to_csv(OUTDIR / f"validation_{stem}_per_group.csv", index=False)
        pd.DataFrame([out["metrics"]]).to_csv(OUTDIR / f"validation_{stem}_metrics.csv", index=False)
        artifacts[stem] = out["splits"]

    with open(OUTDIR / "splits.json", "w") as f:
        json.dump(artifacts, f, indent=2)

    print("Validation outputs written to results/tables/")

if __name__ == "__main__":
    main()
