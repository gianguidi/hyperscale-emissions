from __future__ import annotations

import pandas as pd

from hyperscale_emissions.fuel_mix import compute_regional_fuel_mix


def test_fuel_mix_preserves_expected_national_groups() -> None:
    df = pd.DataFrame(
        {
            "region_B_1": ["A", "B"],
            "Total_MW_scaled": [60.0, 40.0],
            "COAL": [0.5, 0.0],
            "GAS": [0.2, 0.5],
            "OIL": [0.0, 0.0],
            "OFSL": [0.0, 0.0],
            "OTHF": [0.0, 0.0],
            "NUCLEAR": [0.2, 0.1],
            "BIOMASS": [0.0, 0.0],
            "GEOTHERMAL": [0.0, 0.0],
            "HYDRO": [0.1, 0.2],
            "SOLAR": [0.0, 0.1],
            "WIND": [0.0, 0.1],
        }
    )
    _, _, _, groups = compute_regional_fuel_mix(df, national_total_twh=0.0001)
    assert abs(groups["fossil"] - 0.62) < 1e-12
    assert abs(groups["nuclear"] - 0.16) < 1e-12
    assert abs(groups["renewables"] - 0.22) < 1e-12
