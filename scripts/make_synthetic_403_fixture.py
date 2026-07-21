#!/usr/bin/env python3
"""Create a non-identifying 403-row fixture for public model/validation smoke tests."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path("data/synthetic/all_facilities.csv")
SEED = 42
N = 403


def main() -> None:
    rng = np.random.default_rng(SEED)
    sqft = np.exp(rng.normal(np.log(240_000), 0.65, N)).clip(25_000, 2_000_000)
    ba_idx = np.arange(N) % 12
    state_idx = np.arange(N) % 18
    climate_idx = np.arange(N) % 4

    climate = np.array(["cold", "mixed", "hot_humid", "hot_dry"])[climate_idx]
    region = np.array([f"SYN_BA_{i+1:02d}" for i in ba_idx])
    state = np.array([f"SYN_STATE_{i+1:02d}" for i in state_idx])
    operator = np.array([f"SYN_OPERATOR_{i%8+1:02d}" for i in range(N)])

    climate_effect = np.select(
        [climate == "cold", climate == "mixed", climate == "hot_humid", climate == "hot_dry"],
        [-2.0, 0.0, 4.0, 3.0],
        default=0.0,
    )
    ba_effect = ba_idx * 0.6
    current_mw = 7.5 + 0.000125 * sqft + climate_effect + ba_effect + rng.normal(0, 7, N)
    current_mw = np.clip(current_mw, 5, 250)

    missing_idx = rng.choice(N, size=6, replace=False)
    observed = current_mw.copy()
    observed[missing_idx] = np.nan

    df = pd.DataFrame(
        {
            "synthetic_id": [f"SYN_{i+1:04d}" for i in range(N)],
            "FILLED_baxtel_total_building_sqft": sqft.round(2),
            "climate_category": climate,
            "region_B_1": region,
            "state": state,
            "company_name": operator,
            "current_mw": observed,
            "is_imputed_capacity": np.isnan(observed),
        }
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Wrote {OUT}: {len(df)} synthetic rows; {df['current_mw'].isna().sum()} missing capacities")


if __name__ == "__main__":
    main()
