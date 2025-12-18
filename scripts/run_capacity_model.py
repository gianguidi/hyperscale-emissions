from __future__ import annotations

import pandas as pd

from hyperscale_emissions.capacity_model import (
    CapacityModelConfig,
    split_with_and_without_power,
    train_capacity_model,
    plot_predicted_vs_observed,
    predict_missing_capacity,
)
from hyperscale_emissions.utils import ensure_dir


DATA_PATH = "data/processed/all_facilities.csv"


def main():
    df = pd.read_csv(DATA_PATH)

    cfg = CapacityModelConfig()
    df_with, _ = split_with_and_without_power(df, target="current_mw")

    results = train_capacity_model(df_with, cfg)

    print("Model: GradientBoostingRegressor(n_estimators=100)")
    print(f"Cross-Validation RMSE: {results.metrics['cv_rmse']:.4f}")
    print(f"Test Mean Squared Error (MSE): {results.metrics['test_mse']:.4f}")
    print(f"Test R-squared (R²): {results.metrics['test_r2']:.4f}")
    print(f"Test Mean Absolute Error (MAE): {results.metrics['test_mae']:.4f}")
    print(f"Test Mean Absolute Percentage Error (MAPE): {results.metrics['test_mape']:.4f}")
    print(f"Test Mean Error: {results.metrics['test_mean_error']:.4f}")

    plot_predicted_vs_observed(
        results,
        out_path="results/figures/hyp_model_performance.pdf",
    )

    df_with_predictions = predict_missing_capacity(
        df_all=df,
        config=cfg,
        results=results,
        target_col="current_mw",
        new_col="predicted_current_mw",
    )

    ensure_dir("data/processed")
    df_with_predictions.to_csv(
        "data/processed/facilities_with_predicted_capacity.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
