import pandas as pd
import pytest

from hyperscale_emissions.attribution import (
    compute_weighted_ci,
    fill_undefined_combustion_ci,
    generation_weighted_national_ci,
)


def test_total_output_keeps_non_emitting_generation_in_denominator():
    # One BA with 50% gas at 1000 g/kWh and 50% zero-carbon generation.
    # The total-output CI must be 500 g/kWh, not 1000 g/kWh.
    weights = pd.DataFrame({"BACODE": ["X"], "ba_weight": [100.0]})
    factors = pd.DataFrame({"BACODE": ["X"], "ci_total_g_per_kwh": [500.0], "ci_combustion_g_per_kwh": [1000.0]})
    out = compute_weighted_ci(weights, factors)
    assert out["ci_total_g_per_kwh"] == 500.0
    assert out["ci_combustion_g_per_kwh"] == 1000.0
    assert out["ci_total_g_per_kwh"] < out["ci_combustion_g_per_kwh"]


    national_factors = pd.DataFrame(
        {
            "BACODE": ["A", "B"],
            "BANGENAN": [3.0, 1.0],
            "ci_total_g_per_kwh": [100.0, 500.0],
            "ci_combustion_g_per_kwh": [200.0, 600.0],
        }
    )
    assert generation_weighted_national_ci(
        national_factors,
        "ci_total_g_per_kwh",
    ) == 200.0

    diagnostic_factors = pd.DataFrame(
        {
            "BACODE": ["ZERO", "UNKNOWN"],
            "BACO2AN": [0.0, 10.0],
            "ci_total_g_per_kwh": [0.0, 300.0],
            "ci_combustion_g_per_kwh": [float("nan"), float("nan")],
        }
    )
    diagnostic_factors = fill_undefined_combustion_ci(
        diagnostic_factors
    )

    assert (
        diagnostic_factors.loc[
            diagnostic_factors["BACODE"] == "ZERO",
            "ci_combustion_g_per_kwh",
        ].iloc[0]
        == 0.0
    )
    assert bool(
        diagnostic_factors.loc[
            diagnostic_factors["BACODE"] == "ZERO",
            "combustion_ci_filled_noncombustion",
        ].iloc[0]
    )
    assert pd.isna(
        diagnostic_factors.loc[
            diagnostic_factors["BACODE"] == "UNKNOWN",
            "ci_combustion_g_per_kwh",
        ].iloc[0]
    )

    duplicated_factors = pd.concat(
        [factors, factors],
        ignore_index=True,
    )
    with pytest.raises(
        ValueError,
        match="Duplicate BACODE",
    ):
        compute_weighted_ci(
            weights,
            duplicated_factors,
        )
