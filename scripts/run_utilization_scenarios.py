from pathlib import Path

import pandas as pd

from hyperscale_emissions.scenario_analysis import (
    build_scenario_facility_table,
    summarize_scenarios,
    make_range_table,
    DEFAULT_SCENARIOS,
)

DATA_DIR = Path("data/processed")
RESULTS_DIR = Path("results/tables")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

FACILITY_FILE = DATA_DIR / "df_emissions_per_dc_SF.csv"
BA_INTENSITY_FILE = DATA_DIR / "ba_carbon_intensity.csv"


def main() -> None:
    facilities = pd.read_csv(FACILITY_FILE)

    if BA_INTENSITY_FILE.exists():
        ba_ci = pd.read_csv(BA_INTENSITY_FILE)
    else:
        ba_ci = None

    scenario_facilities = build_scenario_facility_table(
        facilities=facilities,
        ba_intensity=ba_ci,
        scenarios=DEFAULT_SCENARIOS,
        capacity_col="current_mw",
        ba_col="region_B_1",
        state_col="state",
    )

    scenario_facilities.to_csv(RESULTS_DIR / "facility_scenarios.csv", index=False)
    # complete-case sensitivity
    for flag_col, stem in [
        ("capacity_imputed", "exclude_capacity_imputed"),
        ("sqft_imputed", "exclude_sqft_imputed"),
    ]:
        if flag_col in scenario_facilities.columns:
            subset = scenario_facilities.loc[~scenario_facilities[flag_col]].copy()
            national_subset = (
                subset.groupby(["scenario", "utilization_u"], as_index=False)
                .agg(
                    total_energy_twh=("annual_energy_twh", "sum"),
                    total_co2_mt=("annual_co2_mt", "sum"),
                    n_facilities=("annual_energy_twh", "size"),
                )
            )
            national_subset.to_csv(
                RESULTS_DIR / f"national_utilization_scenarios_{stem}.csv",
                index=False,
            )

    national = summarize_scenarios(scenario_facilities)
    national.to_csv(RESULTS_DIR / "national_utilization_scenarios.csv", index=False)

    by_state = summarize_scenarios(scenario_facilities, group_col="state")
    by_state.to_csv(RESULTS_DIR / "state_utilization_scenarios_long.csv", index=False)
    make_range_table(by_state, id_col="state").to_csv(
        RESULTS_DIR / "state_utilization_scenarios_wide.csv", index=False
    )

    by_ba = summarize_scenarios(scenario_facilities, group_col="region_B_1")
    by_ba.to_csv(RESULTS_DIR / "ba_utilization_scenarios_long.csv", index=False)
    make_range_table(by_ba, id_col="region_B_1").to_csv(
        RESULTS_DIR / "ba_utilization_scenarios_wide.csv", index=False
    )

    print("Wrote scenario tables to results/tables/")


if __name__ == "__main__":
    main()
