#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from hyperscale_emissions.coverage import aggregate_coverage, grouped_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate-only 675-to-403 coverage diagnostics for restricted data.")
    parser.add_argument("--universe", required=True, help="Restricted 675-facility universe CSV")
    parser.add_argument("--analytical", required=True, help="Restricted 403-facility analytical-sample CSV")
    parser.add_argument("--capacity-col", default="current_mw")
    parser.add_argument("--outdir", default="results/tables/restricted_coverage")
    parser.add_argument("--group-cols", nargs="*", default=["company_name", "region_B_1", "STUSPS", "status"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    universe = pd.read_csv(args.universe)
    analytical = pd.read_csv(args.analytical)

    summary = pd.DataFrame([aggregate_coverage(universe, analytical, key=args.capacity_col)])
    if args.capacity_col in universe.columns:
        summary["universe_capacity_mw_nonmissing_sum"] = pd.to_numeric(universe[args.capacity_col], errors="coerce").sum()
    if args.capacity_col in analytical.columns:
        summary["analytical_capacity_mw_nonmissing_sum"] = pd.to_numeric(analytical[args.capacity_col], errors="coerce").sum()
    summary.to_csv(outdir / "coverage_summary.csv", index=False)

    for col in args.group_cols:
        if col in universe.columns:
            grouped_counts(universe, col).to_csv(outdir / f"universe_counts_by_{col}.csv", index=False)
        if col in analytical.columns:
            grouped_counts(analytical, col).to_csv(outdir / f"analytical_counts_by_{col}.csv", index=False)
    print(f"Wrote aggregate-only diagnostics to {outdir}")

if __name__ == "__main__":
    main()
