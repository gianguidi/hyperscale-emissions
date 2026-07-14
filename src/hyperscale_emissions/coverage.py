from __future__ import annotations

import pandas as pd


def aggregate_coverage(universe: pd.DataFrame, analytical: pd.DataFrame, key: str | None = None) -> dict[str, float]:
    """Return count-based coverage diagnostics for restricted facility data.

    This function is intentionally aggregate-only. It never writes facility IDs,
    coordinates, or addresses.
    """
    universe_n = len(universe)
    analytical_n = len(analytical)
    out = {
        "universe_facilities": float(universe_n),
        "analytical_facilities": float(analytical_n),
        "excluded_facilities": float(universe_n - analytical_n),
        "count_coverage_pct": float(100 * analytical_n / universe_n) if universe_n else float("nan"),
    }
    if key and key in universe.columns and key in analytical.columns:
        out[f"universe_{key}_nonmissing"] = float(universe[key].notna().sum())
        out[f"analytical_{key}_nonmissing"] = float(analytical[key].notna().sum())
    return out


def grouped_counts(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if group_col not in df.columns:
        return pd.DataFrame(columns=[group_col, "n_facilities"])
    return df.groupby(group_col, dropna=False).size().reset_index(name="n_facilities").sort_values("n_facilities", ascending=False)
