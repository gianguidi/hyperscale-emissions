from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
)
import matplotlib.pyplot as plt

from .utils import ensure_dir


@dataclass
class CapacityModelConfig:
    """Configuration for the hyperscale capacity model."""
    predictors: List[str] | None = None
    target: str = "current_mw"
    test_size: float = 0.15
    random_state: int = 42
    n_splits_cv: int = 5
    n_estimators: int = 100

    def __post_init__(self):
        if self.predictors is None:
            self.predictors = [
                "FILLED_baxtel_total_building_sqft",
                "climate_category",
                "company_name",
                "region_B_1",
            ]


@dataclass
class CapacityModelResults:
    model: Pipeline
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    metrics: Dict[str, float]


def build_preprocessor() -> ColumnTransformer:
    """Build the preprocessing transformer (numeric + categorical)."""
    numerical_features = ["FILLED_baxtel_total_building_sqft"]
    categorical_features = ["climate_category", "company_name", "region_B_1"]

    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_transformer, numerical_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor


def split_with_and_without_power(
    df: pd.DataFrame,
    target: str = "current_mw",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split dataframe into rows with and without the target (current_mw)."""
    df_with = df.dropna(subset=[target]).copy()
    df_without = df[df[target].isna()].copy()
    return df_with, df_without


def train_capacity_model(
    df_with_power: pd.DataFrame,
    config: CapacityModelConfig,
) -> CapacityModelResults:
    """Train the GradientBoostingRegressor model with cross-validation."""
    X = df_with_power[config.predictors].copy()
    y = df_with_power[config.target].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
    )

    preprocessor = build_preprocessor()

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                GradientBoostingRegressor(
                    n_estimators=config.n_estimators,
                    random_state=config.random_state,
                ),
            ),
        ]
    )

    # Cross-validation RMSE
    cv = KFold(
        n_splits=config.n_splits_cv,
        shuffle=True,
        random_state=config.random_state,
    )
    cv_scores = cross_val_score(
        model,
        X_train,
        y_train,
        cv=cv,
        scoring="neg_mean_squared_error",
    )
    mean_cv_rmse = float(np.mean(np.sqrt(-cv_scores)))

    # Fit on training set
    model.fit(X_train, y_train)

    # Evaluate on test set
    y_pred = model.predict(X_test)
    y_pred = np.where(y_pred < 0, 0, y_pred)

    mse = float(mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))
    mae = float(mean_absolute_error(y_test, y_pred))
    mape = float(mean_absolute_percentage_error(y_test, y_pred))
    mean_error = float((y_test - y_pred).mean())

    metrics = {
        "cv_rmse": mean_cv_rmse,
        "test_mse": mse,
        "test_r2": r2,
        "test_mae": mae,
        "test_mape": mape,
        "test_mean_error": mean_error,
    }

    return CapacityModelResults(
        model=model,
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        metrics=metrics,
    )


def plot_predicted_vs_observed(
    results: CapacityModelResults,
    out_path: str | None = None,
    title: str = "Predicted vs observed power capacities",
):
    """Predicted vs observed scatterplot with residual coloring."""
    y_test = results.y_test
    y_pred = results.model.predict(results.X_test)
    y_pred = np.where(y_pred < 0, 0, y_pred)

    mse = results.metrics["test_mse"]
    r2 = results.metrics["test_r2"]
    mae = results.metrics["test_mae"]
    mape = results.metrics["test_mape"]
    mean_error = results.metrics["test_mean_error"]
    cv_rmse = results.metrics["cv_rmse"]

    plt.figure(figsize=(10, 6))
    sc = plt.scatter(
        y_test,
        y_pred,
        c=(y_test - y_pred),
        cmap="coolwarm_r",
        alpha=0.7,
    )
    cbar = plt.colorbar(sc)
    cbar.set_label("Prediction error (observed – predicted)")

    lims = [
        min(y_test.min(), y_pred.min()),
        max(y_test.max(), y_pred.max()),
    ]
    plt.plot(lims, lims, "k--", lw=2)

    stats_text = (
        f"R²: {r2:.3f}\n"
        f"MAE: {mae:.2f}\n"
        f"RMSE (CV): {cv_rmse:.2f}\n"
        f"Mean Error: {mean_error:.2f}"
    )

    plt.text(
        0.05,
        0.95,
        stats_text,
        fontsize=12,
        verticalalignment="top",
        transform=plt.gca().transAxes,
        bbox=dict(facecolor="white", alpha=0.5),
    )

    plt.xlabel("Observed power capacity (MW)")
    plt.ylabel("Predicted power capacity (MW)")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()

    if out_path is not None:
        ensure_dir(out_path.rsplit("/", 1)[0])
        plt.savefig(out_path, bbox_inches="tight")
    plt.show()


def predict_missing_capacity(
    df_all: pd.DataFrame,
    config: CapacityModelConfig,
    results: CapacityModelResults,
    target_col: str = "current_mw",
    new_col: str = "predicted_current_mw",
) -> pd.DataFrame:
    """Predict missing current_mw, truncate negatives, and return combined dataframe."""
    df_with, df_without = split_with_and_without_power(df_all, target=target_col)

    X_missing = df_without[config.predictors].copy()
    y_pred_missing = results.model.predict(X_missing)
    y_pred_missing = np.where(y_pred_missing < 0, 0, y_pred_missing)

    df_without[new_col] = y_pred_missing
    df_with[new_col] = df_with[target_col]

    df_combined = pd.concat([df_with, df_without], axis=0)

    return df_combined
