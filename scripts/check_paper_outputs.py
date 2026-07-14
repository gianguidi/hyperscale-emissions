#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

EXPECTED = {
    "low_load": (67.7, 21.3),
    "central_reference": (81.8, 25.7),
    "continuity_sensitivity": (93.5, 29.4),
    "ai_weighted_high": (98.6, 31.0),
}


def fail(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    p = Path("results/tables/scenario_totals_round3_total_output.csv")
    if not p.exists():
        fail(f"Missing {p}. Run scripts/run_emissions_total_output.py first.")
    df = pd.read_csv(p)
    required = {"scenario", "electricity_twh", "co2_mt_total_output", "ci_g_per_kwh_total_output"}
    missing = required - set(df.columns)
    if missing:
        fail(f"Scenario table missing columns: {missing}")
    for scenario, (target_twh, target_mt) in EXPECTED.items():
        row = df.loc[df["scenario"] == scenario]
        if row.empty:
            fail(f"Missing scenario: {scenario}")
        twh = float(row["electricity_twh"].iloc[0])
        mt = float(row["co2_mt_total_output"].iloc[0])
        if abs(twh - target_twh) > 0.2:
            fail(f"{scenario} electricity {twh:.3f} differs from expected {target_twh:.1f}")
        if abs(mt - target_mt) > 0.2:
            fail(f"{scenario} CO2 {mt:.3f} differs from expected {target_mt:.1f}")
    central = df.loc[df["scenario"] == "central_reference"].iloc[0]
    ci = float(central["ci_g_per_kwh_total_output"])
    if abs(ci - 314.0) > 2.0:
        fail(f"Weighted total-output CI {ci:.3f} is not approximately 314 gCO2/kWh")
    audit = pd.read_csv("results/tables/denominator_audit_round3.csv")
    if not (audit["basis"] == "combustion_output_diagnostic").any():
        fail("Denominator audit missing combustion-output diagnostic row")
    print("All Round 3 manuscript-output checks passed.")

if __name__ == "__main__":
    main()
