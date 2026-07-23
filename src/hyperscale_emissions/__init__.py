"""Utilities for reproducing the hyperscale-emissions Round 3 attribution results."""

__version__ = "0.3.0-round3"

from .attribution import (
    LB_PER_MWH_TO_G_PER_KWH,
    compute_weighted_ci,
    generation_weighted_national_ci,
    read_egrid_ba_factors,
)
from .scenario_analysis import SCENARIOS, run_scenario_totals
