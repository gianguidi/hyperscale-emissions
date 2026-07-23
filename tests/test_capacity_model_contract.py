import numpy as np
import pandas as pd

from hyperscale_emissions.capacity_model import (
    CapacityModelConfig,
    predict_missing_capacity,
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


    missing_row = df.iloc[[0]].copy()
    missing_row["current_mw"] = np.nan
    all_rows = pd.concat(
        [df, missing_row],
        ignore_index=True,
    )

    predicted = predict_missing_capacity(
        all_rows,
        cfg,
        results,
    )

    assert "is_imputed_capacity" in predicted.columns
    assert predicted["is_imputed_capacity"].dtype == bool
    assert not predicted.loc[: n - 1, "is_imputed_capacity"].any()
    assert bool(
        predicted.loc[n, "is_imputed_capacity"]
    )
    assert predicted.loc[n, "predicted_current_mw"] >= 0
    assert np.allclose(
        predicted.loc[: n - 1, "predicted_current_mw"],
        predicted.loc[: n - 1, "current_mw"],
    )
