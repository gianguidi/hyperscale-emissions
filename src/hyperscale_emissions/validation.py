from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERICAL_FEATURES = ["FILLED_baxtel_total_building_sqft"]
CATEGORICAL_FEATURES = ["climate_category", "region_B_1"]
PREDICTORS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
TARGET = "current_mw"


def build_pipeline() -> Pipeline:
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
            ("num", numerical_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", GradientBoostingRegressor(n_estimators=100, random_state=42)),
        ]
    )
    return model


def metric_block(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    residuals = y_true - y_pred
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "bias": float(residuals.mean()),
        "underprediction_rate": float((residuals > 0).mean()),
        "overprediction_rate": float((residuals < 0).mean()),
        "p05_residual": float(np.quantile(residuals, 0.05)),
        "p95_residual": float(np.quantile(residuals, 0.95)),
    }


def run_random_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    obs = df.dropna(subset=[TARGET]).copy()
    X = obs[PREDICTORS]
    y = obs[TARGET].to_numpy()

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, obs.index.to_numpy(), test_size=0.15, random_state=42
    )

    model = build_pipeline()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    preds = obs.loc[idx_test, ["region_B_1", "climate_category"]].copy()
    preds["y_true"] = y_test
    preds["y_pred"] = y_pred
    preds["residual"] = preds["y_true"] - preds["y_pred"]

    metrics = metric_block(y_test, y_pred)
    splits = {
        "random_split": {
            "train_indices": idx_train.tolist(),
            "test_indices": idx_test.tolist(),
        }
    }
    return preds, {"metrics": metrics, "splits": splits}


def run_grouped_cv(df: pd.DataFrame, group_col: str, min_group_size: int = 3) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    obs = df.dropna(subset=[TARGET]).copy()
    group_sizes = obs[group_col].value_counts()
    keep_groups = group_sizes[group_sizes >= min_group_size].index
    obs = obs.loc[obs[group_col].isin(keep_groups)].copy()

    X = obs[PREDICTORS]
    y = obs[TARGET].to_numpy()
    groups = obs[group_col].astype(str).to_numpy()

    n_groups = pd.Series(groups).nunique()
    n_splits = min(5, n_groups)
    splitter = GroupKFold(n_splits=n_splits)

    preds_all = []
    split_artifact = {"group_col": group_col, "folds": []}

    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups), start=1):
        model = build_pipeline()
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        part = obs.iloc[test_idx][[group_col, "region_B_1", "climate_category"]].copy()
        part["fold"] = fold
        part["y_true"] = y_test
        part["y_pred"] = y_pred
        part["residual"] = part["y_true"] - part["y_pred"]
        preds_all.append(part)

        split_artifact["folds"].append(
            {
                "fold": fold,
                "train_indices": obs.index[train_idx].tolist(),
                "test_indices": obs.index[test_idx].tolist(),
                "held_out_groups": sorted(pd.Series(groups[test_idx]).unique().tolist()),
            }
        )

    preds = pd.concat(preds_all, ignore_index=True)

    overall = metric_block(preds["y_true"].to_numpy(), preds["y_pred"].to_numpy())
    per_group = (
        preds.groupby(group_col, as_index=False)
        .apply(lambda x: pd.Series(metric_block(x["y_true"].to_numpy(), x["y_pred"].to_numpy())))
        .reset_index(drop=True)
    )
    return preds, per_group, {"metrics": overall, "splits": split_artifact}
