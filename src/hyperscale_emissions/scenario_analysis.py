from __future__ import annotations

from typing import Dict, Iterable, Optional

import pandas as pd

HOURS_PER_YEAR = 8760.0
DEFAULT_SCENARIOS: Dict[str, float] = {
    "low_load": 0.48,
    "central": 0.58,
    "continuity_u0663": 0.663,
    "ai_weighted_high": 0.70,
}


def _find_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def infer_ba_intensity_from_reference(
    df: pd.DataFrame,
    ba_col: str = "region_B_1",
) -> pd.DataFrame:
    """Infer BA carbon intensity from facility-level reference energy/emissions."""
    energy_col = _find_col(df, ["annual_energy_twh", "energy_twh", "twh"])
    emissions_col = _find_col(df, ["annual_co2_mt", "co2_mt", "emissions_mt"])
    if energy_col is None or emissions_col is None:
        raise ValueError(
            "Need either a BA intensity table or facility energy/emissions columns "
            "such as annual_energy_twh and annual_co2_mt."
        )

    tmp = df[[ba_col, energy_col, emissions_col]].copy()
    tmp = tmp.groupby(ba_col, as_index=False).sum()
    tmp["ba_ci_gco2_per_kwh"] = (tmp[emissions_col] * 1e9) / (tmp[energy_col] * 1e9)
    return tmp[[ba_col, "ba_ci_gco2_per_kwh"]]


def build_scenario_facility_table(
    facilities: pd.DataFrame,
    ba_intensity: Optional[pd.DataFrame] = None,
    scenarios: Dict[str, float] = DEFAULT_SCENARIOS,
    capacity_col: str = "current_mw",
    ba_col: str = "region_B_1",
    state_col: str = "state",
) -> pd.DataFrame:
    """Build facility-level electricity and CO2 under facility-load scenarios."""
    if capacity_col not in facilities.columns:
        raise KeyError(f"Missing capacity column: {capacity_col}")
    if ba_col not in facilities.columns:
        raise KeyError(f"Missing BA column: {ba_col}")

    df = facilities.copy()
    if ba_intensity is None:
        ba_intensity = infer_ba_intensity_from_reference(df, ba_col=ba_col)

    if "ba_ci_gco2_per_kwh" not in ba_intensity.columns:
        raise KeyError("BA intensity table must include ba_ci_gco2_per_kwh")

    df = df.merge(ba_intensity[[ba_col, "ba_ci_gco2_per_kwh"]], on=ba_col, how="left", validate="m:1")
    if df["ba_ci_gco2_per_kwh"].isna().any():
        missing = sorted(df.loc[df["ba_ci_gco2_per_kwh"].isna(), ba_col].dropna().unique().tolist())
        raise ValueError(f"Missing BA carbon intensity for: {missing}")

    out_frames = []
    for scenario_name, u in scenarios.items():
        tmp = df.copy()
        tmp["scenario"] = scenario_name
        tmp["utilization_u"] = u
        tmp["annual_energy_mwh"] = pd.to_numeric(tmp[capacity_col], errors="coerce") * HOURS_PER_YEAR * u
        tmp["annual_energy_twh"] = tmp["annual_energy_mwh"] / 1_000_000.0
        # gCO2/kWh equals kgCO2/MWh; kg = EF * MWh; Mt = kg/1e9
        tmp["annual_co2_mt"] = tmp["annual_energy_mwh"] * tmp["ba_ci_gco2_per_kwh"] / 1e9
        out_frames.append(tmp)

    return pd.concat(out_frames, ignore_index=True)


def summarize_scenarios(scenario_df: pd.DataFrame, group_col: Optional[str] = None) -> pd.DataFrame:
    """Summarize scenario totals nationally or by a grouping column."""
    group_cols = ["scenario", "utilization_u"] if group_col is None else [group_col, "scenario", "utilization_u"]
    return (
        scenario_df.groupby(group_cols, as_index=False)
        .agg(
            total_energy_twh=("annual_energy_twh", "sum"),
            total_co2_mt=("annual_co2_mt", "sum"),
            n_facilities=("annual_energy_twh", "size"),
        )
    )


def make_range_table(summary_df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Convert long scenario summaries into wide scenario columns."""
    pivot = summary_df.pivot(index=id_col, columns="scenario", values=["total_energy_twh", "total_co2_mt"])
    pivot.columns = [f"{metric}_{scenario}" for metric, scenario in pivot.columns]
    return pivot.reset_index()
