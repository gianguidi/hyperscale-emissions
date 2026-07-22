import numpy as np
import pandas as pd
import pytest

from hyperscale_emissions.validation import run_grouped_cv


def make_validation_fixture() -> pd.DataFrame:
    rng = np.random.default_rng(34)
    n = 120

    sqft = rng.uniform(50_000, 850_000, n)

    return pd.DataFrame(
        {
            "FILLED_baxtel_total_building_sqft": sqft,
            "climate_category": [
                f"CL_{i % 4}"
                for i in range(n)
            ],
            "region_B_1": [
                f"BA_{i % 6}"
                for i in range(n)
            ],
            "state": [
                f"ST_{i % 5}"
                for i in range(n)
            ],
            "current_mw": (
                10
                + 0.00011 * sqft
                + rng.normal(0, 5, n)
            ),
        }
    )


@pytest.mark.parametrize(
    "group_col",
    [
        "region_B_1",
        "state",
        "climate_category",
    ],
)
def test_grouped_validation_handles_group_columns_without_duplicates(
    group_col: str,
) -> None:
    df = make_validation_fixture()

    predictions, per_group, result = run_grouped_cv(
        df,
        group_col=group_col,
        min_group_size=3,
    )

    assert predictions.columns.is_unique
    assert group_col in predictions.columns

    assert len(predictions) == len(df)
    assert predictions["y_true"].notna().all()
    assert predictions["y_pred"].notna().all()
    assert predictions["residual"].notna().all()

    assert group_col in per_group.columns
    assert len(per_group) == df[group_col].nunique()

    assert "metrics" in result
    assert "splits" in result

    assert result["splits"]["group_col"] == group_col
    assert len(result["splits"]["folds"]) >= 2

    for fold in result["splits"]["folds"]:
        train_indices = set(fold["train_indices"])
        test_indices = set(fold["test_indices"])

        assert train_indices.isdisjoint(test_indices)
        assert fold["held_out_groups"]
