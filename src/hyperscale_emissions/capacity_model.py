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


# Complete GradientBoostingRegressor specification used in the manuscript.
# Values matching scikit-learn defaults are written explicitly so results do
# not depend on implicit defaults changing between software versions.
GBRT_PARAMETERS = {
    "loss": "squared_error",
    "learning_rate": 0.1,
    "n_estimators": 100,
    "subsample": 1.0,
    "min_samples_split": 2,
    "min_samples_leaf": 1,
    "min_weight_fraction_leaf": 0.0,
    "max_depth": 3,
    "min_impurity_decrease": 0.0,
    "init": None,
    "random_state": 42,
    "max_features": None,
    "alpha": 0.9,
    "verbose": 0,
    "max_leaf_nodes": None,
    "warm_start": False,
    "validation_fraction": 0.1,
    "n_iter_no_change": None,
    "tol": 0.0001,
    "ccp_alpha": 0.0,
}


def gbrt_parameters(
    n_estimators: int = 100,
    random_state: int = 42,
) -> dict[str, object]:
    """Return the fully explicit manuscript GBRT specification."""
    parameters = GBRT_PARAMETERS.copy()
    parameters["n_estimators"] = n_estimators
    parameters["random_state"] = random_state
    return parameters


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
    categorical_features = ["climate_category", "region_B_1"]
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
        (
            "regressor",
            GradientBoostingRegressor(
                **gbrt_parameters(
                    n_estimators=config.n_estimators,
                    random_state=config.random_state,
                )
            ),
        ),
    ])

    cv = KFold(n_splits=config.n_splits_cv, shuffle=True, random_state=config.random_state)
    cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="neg_mean_squared_error")
    mean_cv_rmse = float(np.mean(np.sqrt(-cv_scores)))

    model.fit(X_train, y_train)
    y_pred = np.maximum(model.predict(X_test), 0)
    metrics = {
        "cv_rmse": mean_cv_rmse,
        "test_mse": float(mean_squared_error(y_test, y_pred)),
        "test_rmse": float(
            mean_squared_error(y_test, y_pred) ** 0.5
        ),
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
    imputed_flag_col: str = "is_imputed_capacity",
) -> pd.DataFrame:
    """Fill the model-output column and record explicit prediction provenance.

    ``imputed_flag_col`` is True only when the original target value was
    missing and ``new_col`` was therefore supplied by the fitted model.
    Observed capacities are copied unchanged into ``new_col``.
    """
    if target_col not in df_all.columns:
        raise KeyError(f"Missing capacity target column: {target_col}")

    missing_predictors = [
        column
        for column in config.predictors
        if column not in df_all.columns
    ]
    if missing_predictors:
        raise KeyError(
            f"Missing model predictor columns: {missing_predictors}"
        )

    out = df_all.copy()
    observed_capacity = pd.to_numeric(
        out[target_col],
        errors="coerce",
    )
    imputed_mask = observed_capacity.isna()

    out[new_col] = observed_capacity

    if imputed_mask.any():
        X_missing = out.loc[
            imputed_mask,
            config.predictors,
        ].copy()
        predictions = np.maximum(
            results.model.predict(X_missing),
            0,
        )
        out.loc[imputed_mask, new_col] = predictions

    out[imputed_flag_col] = imputed_mask.astype(bool)

    return out.sort_index()
