from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if it does not already exist and return it as a Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def first_existing_column(df: pd.DataFrame, candidates: Iterable[str], label: str) -> str:
    """Return the first candidate column that appears in a dataframe."""
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"Could not find {label}. Tried {list(candidates)}. Available: {list(df.columns)}")


def normalize_code(series: pd.Series) -> pd.Series:
    """Normalize balancing-authority and state-like codes."""
    return series.astype(str).str.strip().str.upper()
