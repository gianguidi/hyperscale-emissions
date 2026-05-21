#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hyperscale_emissions.scenario_analysis import (  # noqa: E402
    DEFAULT_SCENARIOS,
    build_scenario_facility_table,
    make_range_table,
    summarize_scenarios,
)

DATA_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

FACILITY_FILE = DATA_DIR / "df_emissions_per_dc_SF.csv"
BA_INTENSITY_FILE = DATA_DIR / "ba_carbon_intensity.csv"


def main() -> None:
    if not FACILITY_FILE.exists():
        raise SystemExit(f"Missing input: {FACILITY_FILE}\nSee REPRO.md for schema.")
    facilities = pd.read_csv(FACILITY_FILE)
    ba_ci = pd.read_csv(BA_INTENSITY_FILE) if BA_INTENSITY_FILE.exists() else None

    state_col = "state" if "state" in facilities.columns else "STUSPS"
    scenario_facilities = build_scenario_facility_table(
        facilities=facilities,
        ba_intensity=ba_ci,
        scenarios=DEFAULT_SCENARIOS,
        capacity_col="current_mw",
        ba_col="region_B_1",
        state_col=state_col,
    )
    scenario_facilities.to_csv(RESULTS_DIR / "facility_scenarios.csv", index=False)

    national = summarize_scenarios(scenario_facilities)
    national.to_csv(RESULTS_DIR / "national_utilization_scenarios.csv", index=False)

    if state_col in scenario_facilities.columns:
        by_state = summarize_scenarios(scenario_facilities, group_col=state_col)
        by_state.to_csv(RESULTS_DIR / "state_utilization_scenarios_long.csv", index=False)
        make_range_table(by_state, id_col=state_col).to_csv(RESULTS_DIR / "state_utilization_scenarios_wide.csv", index=False)

    by_ba = summarize_scenarios(scenario_facilities, group_col="region_B_1")
    by_ba.to_csv(RESULTS_DIR / "ba_utilization_scenarios_long.csv", index=False)
    make_range_table(by_ba, id_col="region_B_1").to_csv(RESULTS_DIR / "ba_utilization_scenarios_wide.csv", index=False)

    for flag_col, stem in [("capacity_imputed", "exclude_capacity_imputed"), ("sqft_imputed", "exclude_sqft_imputed")]:
        if flag_col in scenario_facilities.columns:
            subset = scenario_facilities.loc[~scenario_facilities[flag_col].astype(bool)].copy()
            national_subset = summarize_scenarios(subset)
            national_subset.to_csv(RESULTS_DIR / f"national_utilization_scenarios_{stem}.csv", index=False)

    print(f"Wrote scenario tables to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
