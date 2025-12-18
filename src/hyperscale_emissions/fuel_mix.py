from __future__ import annotations

from typing import List, Dict, Tuple
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
    national_total_twh: float = 93.66,
    top_n_regions: int = 7,
) -> Tuple[pd.DataFrame, pd.Series, pd.Series, Dict[str, float]]:
    """Compute US + top-N BA fuel mixes, as used in Figure 4."""
    if fuel_cols is None:
        fuel_cols = ALL_FUELS

    fm = fuel_mix_hyperscalers.copy()

    # absolute MWh by fuel
    for f in fuel_cols:
        fm[f] = fm[total_col] * fm[f]

    regional_totals = fm.groupby(region_col)[fuel_cols].sum()
    regional_totals[total_col] = fm.groupby(region_col)[total_col].sum()
    regional_totals = regional_totals.dropna(axis=0, how="any")

    top_regions = regional_totals.sort_values(
        by=total_col, ascending=False
    ).head(top_n_regions)

    regional_norm = top_regions[fuel_cols].div(
        top_regions[fuel_cols].sum(axis=1),
        axis=0,
    )

    national_totals = fm[fuel_cols].sum()
    national_mix = national_totals / national_totals.sum()
    national_row = pd.DataFrame([national_mix], index=["US Total"])

    regional_with_us = pd.concat([national_row, regional_norm], axis=0)
    # reverse so US Total is at top of the plot
    regional_with_us = regional_with_us[::-1]

    total_twh = pd.concat(
        [
            pd.Series({"US Total": national_total_twh}),
            top_regions[total_col] / 1_000_000,
        ]
    )
    total_twh = total_twh.loc[regional_with_us.index[::-1]]

    def group_share(group: List[str]) -> float:
        return float(national_mix.reindex(group).fillna(0).sum())

    group_shares_us = {
        "fossil": group_share(FOSSIL_FUELS),
        "nuclear": group_share(NUCLEAR),
        "renewables": group_share(RENEWABLES),
    }

    return regional_with_us, total_twh, national_mix, group_shares_us
