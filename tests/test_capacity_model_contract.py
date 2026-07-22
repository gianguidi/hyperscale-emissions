import numpy as np
import pandas as pd

from hyperscale_emissions.capacity_model import (
    CapacityModelConfig,
    train_capacity_model,
)


def test_public_model_matches_disclosed_predictors_and_emits_test_rmse() -> None:
    cfg = CapacityModelConfig()

    assert cfg.predictors == [
        "FILLED_baxtel_total_building_sqft",
        "climate_category",
        "region_B_1",
    ]

    rng = np.random.default_rng(12)
    n = 80
    sqft = rng.uniform(40_000, 900_000, n)

    df = pd.DataFrame(
        {
            "FILLED_baxtel_total_building_sqft": sqft,
            "climate_category": [
                f"CL_{i % 4}"
                for i in range(n)
            ],
            "region_B_1": [
                f"BA_{i % 7}"
                for i in range(n)
            ],
            "current_mw": (
                8
                + 0.00012 * sqft
                + rng.normal(0, 4, n)
            ),
        }
    )

    results = train_capacity_model(df, cfg)

    assert "test_mse" in results.metrics
    assert "test_rmse" in results.metrics

    expected_rmse = results.metrics["test_mse"] ** 0.5

    assert np.isclose(
        results.metrics["test_rmse"],
        expected_rmse,
    )
    assert results.metrics["test_rmse"] > 0
