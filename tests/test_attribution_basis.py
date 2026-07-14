import pandas as pd

from hyperscale_emissions.attribution import compute_weighted_ci


def test_total_output_keeps_non_emitting_generation_in_denominator():
    # One BA with 50% gas at 1000 g/kWh and 50% zero-carbon generation.
    # The total-output CI must be 500 g/kWh, not 1000 g/kWh.
    weights = pd.DataFrame({"BACODE": ["X"], "ba_weight": [100.0]})
    factors = pd.DataFrame({"BACODE": ["X"], "ci_total_g_per_kwh": [500.0], "ci_combustion_g_per_kwh": [1000.0]})
    out = compute_weighted_ci(weights, factors)
    assert out["ci_total_g_per_kwh"] == 500.0
    assert out["ci_combustion_g_per_kwh"] == 1000.0
    assert out["ci_total_g_per_kwh"] < out["ci_combustion_g_per_kwh"]
