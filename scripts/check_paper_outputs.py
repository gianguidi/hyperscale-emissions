#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"

EXPECTED = {
    "low_load": {"u": 0.48, "twh": 67.7, "co2": 36.9},
    "central": {"u": 0.58, "twh": 81.8, "co2": 44.6},
    "continuity_u0663": {"u": 0.663, "twh": 93.5, "co2": 51.0},
    "ai_weighted_high": {"u": 0.70, "twh": 98.6, "co2": 53.8},
}
TOL_TWH = 0.2
TOL_CO2 = 0.2


def _fail(msg: str) -> None:
    raise SystemExit(f"CHECK FAILED: {msg}")


def main() -> None:
    scenario_path = TABLES / "national_utilization_scenarios.csv"
    if not scenario_path.exists():
        _fail(f"Missing {scenario_path}; run scripts/run_utilization_scenarios.py first.")
    df = pd.read_csv(scenario_path)
    print(f"Checking {scenario_path}")

    for scenario, exp in EXPECTED.items():
        sub = df.loc[df["scenario"] == scenario]
        if sub.empty:
            _fail(f"Missing scenario {scenario!r}. Available: {sorted(df['scenario'].unique())}")
        row = sub.iloc[0]
        if not np.isclose(row["utilization_u"], exp["u"], atol=1e-6):
            _fail(f"Scenario {scenario}: u={row['utilization_u']} expected {exp['u']}")
        if abs(row["total_energy_twh"] - exp["twh"]) > TOL_TWH:
            _fail(f"Scenario {scenario}: TWh={row['total_energy_twh']:.3f}, expected {exp['twh']:.1f}")
        if abs(row["total_co2_mt"] - exp["co2"]) > TOL_CO2:
            _fail(f"Scenario {scenario}: CO2={row['total_co2_mt']:.3f}, expected {exp['co2']:.1f}")
        print(f"  OK {scenario}: {row['total_energy_twh']:.2f} TWh, {row['total_co2_mt']:.2f} Mt")

    print("Paper headline-output check passed.")


if __name__ == "__main__":
    main()
