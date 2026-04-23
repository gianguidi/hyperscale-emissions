from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import pandas as pd
import numpy as np


HOURS_PER_YEAR = 8760.0
DEFAULT_SCENARIOS = {
    "low_load": 0.48,
    "intermediate": 0.58,
    "reference": 0.663,
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
    """
    Infer average BA carbon intensity (gCO2/kWh) from reference-scenario
    facility-level energy/emissions if those columns exist.
    """
    energy_col = _find_col(df, ["annual_energy_twh", "energy_twh", "twh"])
    emissions_col = _find_col(df, ["annual_co2_mt", "co2_mt", "emissions_mt"])

    if energy_col is None or emissions_col is None:
        raise ValueError(
            "Need reference-scenario facility energy and emissions columns "
            "(e.g. annual_energy_twh, annual_co2_mt) to infer BA intensity."
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
    """
    Build facility-level energy and emissions under multiple utilization scenarios.

    Required:
      - facilities[current_mw]
      - facilities[region_B_1]
      - either:
          (a) a BA-level intensity table with columns [region_B_1, ba_ci_gco2_per_kwh], or
          (b) facility-level reference energy+emissions to infer BA intensity.
    """
    df = facilities.copy()

    if ba_intensity is None:
        ba_intensity = infer_ba_intensity_from_reference(df, ba_col=ba_col)

    df = df.merge(ba_intensity, on=ba_col, how="left", validate="m:1")

    if df["ba_ci_gco2_per_kwh"].isna().any():
        missing = df.loc[df["ba_ci_gco2_per_kwh"].isna(), ba_col].dropna().unique().tolist()
        raise ValueError(f"Missing BA carbon intensity for: {missing}")

    out_frames = []
    for scenario_name, u in scenarios.items():
        tmp = df.copy()
        tmp["scenario"] = scenario_name
        tmp["utilization_u"] = u
        tmp["annual_energy_twh"] = tmp[capacity_col] * HOURS_PER_YEAR * u / 1e6
        tmp["annual_co2_mt"] = (
            tmp["annual_energy_twh"] * 1e9 * tmp["ba_ci_gco2_per_kwh"]
        ) / 1e9
        out_frames.append(tmp)

    out = pd.concat(out_frames, ignore_index=True)
    return out


def summarize_scenarios(
    scenario_df: pd.DataFrame,
    group_col: Optional[str] = None,
) -> pd.DataFrame:
    if group_col is None:
        out = (
            scenario_df.groupby(["scenario", "utilization_u"], as_index=False)
            .agg(
                total_energy_twh=("annual_energy_twh", "sum"),
                total_co2_mt=("annual_co2_mt", "sum"),
                n_facilities=("annual_energy_twh", "size"),
            )
        )
    else:
        out = (
            scenario_df.groupby([group_col, "scenario", "utilization_u"], as_index=False)
            .agg(
                total_energy_twh=("annual_energy_twh", "sum"),
                total_co2_mt=("annual_co2_mt", "sum"),
                n_facilities=("annual_energy_twh", "size"),
            )
        )
    return out


def make_range_table(summary_df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """
    Convert long scenario summaries into a wide min/reference/max table.
    """
    pivot = summary_df.pivot(index=id_col, columns="scenario", values=["total_energy_twh", "total_co2_mt"])
    pivot.columns = [f"{metric}_{scenario}" for metric, scenario in pivot.columns]
    pivot = pivot.reset_index()
    return pivot
