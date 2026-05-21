from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

FOSSIL_FUELS = ["COAL", "GAS", "OIL", "OFSL", "OTHF"]
NUCLEAR = ["NUCLEAR"]
RENEWABLES = ["BIOMASS", "GEOTHERMAL", "HYDRO", "SOLAR", "WIND"]
ALL_FUELS = FOSSIL_FUELS + NUCLEAR + RENEWABLES


def compute_regional_fuel_mix(
    fuel_mix_hyperscalers: pd.DataFrame,
    region_col: str = "region_B_1",
    total_col: str = "Total_MW_scaled",
    fuel_cols: List[str] | None = None,
    national_total_twh: float = 81.8,
    top_n_regions: int = 7,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, Dict[str, float]]:
    """Compute national and top-BA fuel mixes for the Figure 4 plot.

    Parameters
    ----------
    fuel_mix_hyperscalers:
        BA-level table with one total-load column and one share column per fuel.
    region_col:
        Balancing-authority code column.
    total_col:
        BA total HDC electricity/load column. If values are in MWh, labels are
        converted to TWh by dividing by 1e6.
    fuel_cols:
        Fuel share columns. Defaults to the paper fuel ordering.
    national_total_twh:
        National HDC electricity total to label the US Total row.
    top_n_regions:
        Number of BAs to show below the US Total row.
    """
    if fuel_cols is None:
        fuel_cols = ALL_FUELS

    missing = [c for c in [region_col, total_col, *fuel_cols] if c not in fuel_mix_hyperscalers.columns]
    if missing:
        raise KeyError(f"Fuel-mix input missing required columns: {missing}")

    fm = fuel_mix_hyperscalers.copy()
    for f in fuel_cols:
        fm[f] = pd.to_numeric(fm[total_col], errors="coerce") * pd.to_numeric(fm[f], errors="coerce").fillna(0)

    regional_totals = fm.groupby(region_col)[fuel_cols].sum()
    regional_totals[total_col] = fm.groupby(region_col)[total_col].sum()
    regional_totals = regional_totals.dropna(axis=0, how="any")

    top_regions = regional_totals.sort_values(by=total_col, ascending=False).head(top_n_regions)
    regional_norm = top_regions[fuel_cols].div(top_regions[fuel_cols].sum(axis=1), axis=0).fillna(0)

    national_totals = fm[fuel_cols].sum()
    national_mix = (national_totals / national_totals.sum()).fillna(0)
    national_row = pd.DataFrame([national_mix], index=["US Total"])

    regional_with_us = pd.concat([national_row, regional_norm], axis=0)
    # barh draws first row at bottom; reverse so US Total appears at top
    regional_with_us = regional_with_us.iloc[::-1]

    total_twh = pd.concat([
        pd.Series({"US Total": national_total_twh}),
        top_regions[total_col] / 1_000_000.0,
    ])
    total_twh = total_twh.reindex(regional_with_us.index)

    def group_share(group: List[str]) -> float:
        return float(national_mix.reindex(group).fillna(0).sum())

    group_shares_us = {
        "fossil": group_share(FOSSIL_FUELS),
        "nuclear": group_share(NUCLEAR),
        "renewables": group_share(RENEWABLES),
    }
    return regional_with_us, total_twh, national_mix, group_shares_us
