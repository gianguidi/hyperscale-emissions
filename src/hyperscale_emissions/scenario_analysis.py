from __future__ import annotations

import pandas as pd

SCENARIOS = [
    {"scenario": "low_load", "u": 0.480, "target_electricity_twh": 67.7, "target_co2_mt_total_output": 21.3},
    {"scenario": "central_reference", "u": 0.580, "target_electricity_twh": 81.8, "target_co2_mt_total_output": 25.7},
    {"scenario": "continuity_sensitivity", "u": 0.663, "target_electricity_twh": 93.5, "target_co2_mt_total_output": 29.4},
    {"scenario": "ai_weighted_high", "u": 0.700, "target_electricity_twh": 98.6, "target_co2_mt_total_output": 31.0},
]


def run_scenario_totals(base_twh_at_reference: float, reference_u: float, ci_total_g_per_kwh: float, ci_combustion_g_per_kwh: float, scenarios: list[dict] | None = None) -> pd.DataFrame:
    """Scale total electricity from a reference scenario and compute emissions.

    Parameters
    ----------
    base_twh_at_reference:
        Electricity demand in TWh corresponding to `reference_u`.
    reference_u:
        Facility-load coefficient for the base demand. In the public aggregate
        weights this is 0.663, because those weights were exported from the
        continuity-sensitivity scenario.
    ci_total_g_per_kwh:
        HDC-weighted total-output CI used for headline emissions.
    ci_combustion_g_per_kwh:
        HDC-weighted combustion-output CI retained as diagnostic only.
    """
    if scenarios is None:
        scenarios = SCENARIOS
    rows = []
    for s in scenarios:
        twh = base_twh_at_reference * (float(s["u"]) / reference_u)
        rows.append(
            {
                "scenario": s["scenario"],
                "u": float(s["u"]),
                "electricity_twh": twh,
                "co2_mt_total_output": twh * ci_total_g_per_kwh / 1000,
                "ci_g_per_kwh_total_output": ci_total_g_per_kwh,
                "co2_mt_combustion_diagnostic": twh * ci_combustion_g_per_kwh / 1000,
                "ci_g_per_kwh_combustion_diagnostic": ci_combustion_g_per_kwh,
                "target_electricity_twh": s.get("target_electricity_twh"),
                "target_co2_mt_total_output": s.get("target_co2_mt_total_output"),
            }
        )
    out = pd.DataFrame(rows)
    out["delta_twh_vs_target"] = out["electricity_twh"] - out["target_electricity_twh"]
    out["delta_co2_vs_target"] = out["co2_mt_total_output"] - out["target_co2_mt_total_output"]
    return out
