#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from hyperscale_emissions.attribution import compute_weighted_ci, build_denominator_audit, read_egrid_ba_factors
from hyperscale_emissions.scenario_analysis import run_scenario_totals


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce Round 3 total-output HDC emissions totals.")
    parser.add_argument("--ba-weights", default="data/processed/ba_load_weights_public_u0663.csv", help="Aggregate BA load weights from the reference u=0.663 scenario.")
    parser.add_argument("--ba-factors", default="data/processed/ba_effective_emission_factor_egrid2023_rev2.csv", help="BA-level CI factors. If --egrid-xlsx is supplied, this is ignored.")
    parser.add_argument("--egrid-xlsx", default=None, help="Optional raw EPA eGRID2023 Rev. 2 workbook. If provided, BA factors are recomputed from it.")
    parser.add_argument("--reference-u", type=float, default=0.663, help="Facility-load coefficient represented by the aggregate BA weights.")
    parser.add_argument("--outdir", default="results/tables", help="Output directory.")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    weights = pd.read_csv(args.ba_weights)
    if args.egrid_xlsx:
        factors = read_egrid_ba_factors(args.egrid_xlsx)
    else:
        factors = pd.read_csv(args.ba_factors)

    # Ensure the expected factor names are present.
    if "ci_total_g_per_kwh" not in factors.columns and "co2_total_g_per_kwh" in factors.columns:
        factors = factors.rename(columns={"co2_total_g_per_kwh": "ci_total_g_per_kwh"})
    if "ci_combustion_g_per_kwh" not in factors.columns and "co2_combustion_g_per_kwh" in factors.columns:
        factors = factors.rename(columns={"co2_combustion_g_per_kwh": "ci_combustion_g_per_kwh"})

    weighted_ci = compute_weighted_ci(weights, factors, weight_col="ba_weight")
    base_twh = pd.to_numeric(weights["ba_weight"], errors="raise").sum() / 1e6
    scenarios = run_scenario_totals(
        base_twh_at_reference=base_twh,
        reference_u=args.reference_u,
        ci_total_g_per_kwh=weighted_ci["ci_total_g_per_kwh"],
        ci_combustion_g_per_kwh=weighted_ci["ci_combustion_g_per_kwh"],
    )
    audit = build_denominator_audit(weighted_ci, central_twh=float(scenarios.loc[scenarios.scenario == "central_reference", "electricity_twh"].iloc[0]))

    scenarios.to_csv(outdir / "scenario_totals_round3_total_output.csv", index=False)
    audit.to_csv(outdir / "denominator_audit_round3.csv", index=False)

    print("Round 3 total-output reproduction")
    print(scenarios[["scenario", "u", "electricity_twh", "co2_mt_total_output", "co2_mt_combustion_diagnostic"]].round(3).to_string(index=False))
    print("\nDenominator audit")
    print(audit.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
