from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

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

    def __post_init__(self) -> None:
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
    numerical_features = ["FILLED_baxtel_total_building_sqft"]
    categorical_features = ["climate_category", "company_name", "region_B_1"]
    numerical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler()),
    ])
    categorical_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numerical_transformer, numerical_features),
        ("cat", categorical_transformer, categorical_features),
    ])


def split_with_and_without_power(df: pd.DataFrame, target: str = "current_mw") -> Tuple[pd.DataFrame, pd.DataFrame]:
    return df.dropna(subset=[target]).copy(), df[df[target].isna()].copy()


def train_capacity_model(df_with_power: pd.DataFrame, config: CapacityModelConfig) -> CapacityModelResults:
    missing = [c for c in config.predictors if c not in df_with_power.columns]
    if missing:
        raise KeyError(f"Missing model predictor columns: {missing}")

    X = df_with_power[config.predictors].copy()
    y = df_with_power[config.target].copy()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state
    )

    model = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("regressor", GradientBoostingRegressor(n_estimators=config.n_estimators, random_state=config.random_state)),
    ])

    cv = KFold(n_splits=config.n_splits_cv, shuffle=True, random_state=config.random_state)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="neg_mean_squared_error")
    mean_cv_rmse = float(np.mean(np.sqrt(-cv_scores)))

    model.fit(X_train, y_train)
    y_pred = np.maximum(model.predict(X_test), 0)
    metrics = {
        "cv_rmse": mean_cv_rmse,
        "test_mse": float(mean_squared_error(y_test, y_pred)),
        "test_r2": float(r2_score(y_test, y_pred)),
        "test_mae": float(mean_absolute_error(y_test, y_pred)),
        "test_mape": float(mean_absolute_percentage_error(y_test, y_pred)),
        "test_mean_error": float((y_test - y_pred).mean()),
    }
    return CapacityModelResults(model, X_train, X_test, y_train, y_test, metrics)


def plot_predicted_vs_observed(
    results: CapacityModelResults,
    out_path: str | None = None,
    title: str = "Predicted vs observed power capacities",
) -> None:
    y_test = results.y_test
    y_pred = np.maximum(results.model.predict(results.X_test), 0)
    residual = y_test - y_pred
    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(y_test, y_pred, c=residual, cmap="coolwarm_r", alpha=0.7)
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Prediction error (observed - predicted)")
    lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    ax.plot(lims, lims, "k--", lw=2)
    stats_text = (
        f"R2: {results.metrics['test_r2']:.3f}\n"
        f"MAE: {results.metrics['test_mae']:.2f} MW\n"
        f"CV RMSE: {results.metrics['cv_rmse']:.2f} MW\n"
        f"Bias: {results.metrics['test_mean_error']:.2f} MW"
    )
    ax.text(0.05, 0.95, stats_text, fontsize=12, va="top", transform=ax.transAxes,
            bbox=dict(facecolor="white", alpha=0.7))
    ax.set_xlabel("Observed power capacity (MW)")
    ax.set_ylabel("Predicted power capacity (MW)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if out_path is not None:
        ensure_dir(str(out_path).rsplit("/", 1)[0])
        fig.savefig(out_path, bbox_inches="tight", dpi=300)
    plt.close(fig)


def predict_missing_capacity(
    df_all: pd.DataFrame,
    config: CapacityModelConfig,
    results: CapacityModelResults,
    target_col: str = "current_mw",
    new_col: str = "predicted_current_mw",
) -> pd.DataFrame:
    df_with, df_without = split_with_and_without_power(df_all, target=target_col)
    if not df_without.empty:
        X_missing = df_without[config.predictors].copy()
        df_without[new_col] = np.maximum(results.model.predict(X_missing), 0)
    df_with[new_col] = df_with[target_col]
    return pd.concat([df_with, df_without], axis=0).sort_index()
