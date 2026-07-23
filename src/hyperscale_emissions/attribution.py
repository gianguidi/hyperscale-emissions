from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

LB_PER_MWH_TO_G_PER_KWH = 0.45359237


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _normalise_ba_codes(series: pd.Series) -> pd.Series:
    """Normalise BA identifiers without converting missing values to text."""
    return (
        series.astype("string")
        .str.strip()
        .str.upper()
    )


def _require_unique_ba_codes(
    df: pd.DataFrame,
    ba_col: str,
    label: str,
) -> None:
    """Require one non-empty row per normalised BA identifier."""
    if ba_col not in df.columns:
        raise KeyError(f"{label} is missing BA column: {ba_col}")

    codes = _normalise_ba_codes(df[ba_col])
    invalid = codes.isna() | codes.eq("")

    if invalid.any():
        raise ValueError(
            f"{label} contains {int(invalid.sum())} missing or blank "
            f"{ba_col} values"
        )

    duplicates = sorted(
        codes.loc[codes.duplicated(keep=False)]
        .dropna()
        .unique()
        .tolist()
    )

    if duplicates:
        raise ValueError(
            f"Duplicate {ba_col} rows in {label}: {duplicates}"
        )


def generation_weighted_national_ci(
    ci: pd.DataFrame,
    intensity_col: str,
    generation_col: str = "BANGENAN",
    ba_col: str = "BACODE",
) -> float:
    """Calculate a generation-weighted national carbon intensity.

    Only rows with positive reported generation and a non-missing intensity
    are included. This replaces unweighted averaging across balancing
    authorities when a national fallback factor is required.
    """
    required = {
        ba_col,
        intensity_col,
        generation_col,
    }
    missing = sorted(required.difference(ci.columns))

    if missing:
        raise KeyError(
            f"Missing columns for national CI calculation: {missing}"
        )

    table = ci.copy()
    table[ba_col] = _normalise_ba_codes(table[ba_col])
    _require_unique_ba_codes(
        table,
        ba_col,
        "BA factor table",
    )

    intensity = pd.to_numeric(
        table[intensity_col],
        errors="coerce",
    )
    generation = pd.to_numeric(
        table[generation_col],
        errors="coerce",
    )

    valid = (
        intensity.notna()
        & generation.notna()
        & generation.gt(0)
    )

    if not valid.any():
        raise ValueError(
            "No BA rows have both positive generation and a valid "
            f"{intensity_col}"
        )

    return float(
        np.average(
            intensity.loc[valid],
            weights=generation.loc[valid],
        )
    )


def find_egrid_ba_sheet(path: str | Path) -> str:
    """Return the first Excel sheet that contains the BA-level eGRID columns."""
    xls = pd.ExcelFile(path)
    for sheet in xls.sheet_names:
        sample = pd.read_excel(path, sheet_name=sheet, nrows=5)
        cols = {str(c).strip().upper() for c in sample.columns}
        if {"BACODE", "BACO2RTA", "BACO2CRT"}.issubset(cols):
            return sheet
    raise ValueError("Could not find an eGRID BA sheet with BACODE/BACO2RTA/BACO2CRT columns")


def read_egrid_ba_factors(path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    """Read EPA eGRID BA-level rates and convert lb/MWh to g/kWh.

    The Round 3 headline basis is total-output CO2 intensity:
    BACO2RTA * 0.45359237.

    Combustion-output intensity is retained as a diagnostic only:
    BACO2CRT * 0.45359237.
    """
    if sheet_name is None:
        sheet_name = find_egrid_ba_sheet(path)
    df = pd.read_excel(path, sheet_name=sheet_name)
    df = _normalise_columns(df)
    colmap = {c.upper(): c for c in df.columns}
    needed = ["BACODE", "BACO2RTA", "BACO2CRT"]
    missing = [c for c in needed if c not in colmap]
    if missing:
        raise ValueError(f"Missing required eGRID columns: {missing}")
    out = df.rename(columns={colmap["BACODE"]: "BACODE", colmap["BACO2RTA"]: "BACO2RTA", colmap["BACO2CRT"]: "BACO2CRT"})
    if "BANAME" in colmap:
        out = out.rename(columns={colmap["BANAME"]: "BANAME"})
    if "BANGENAN" in colmap:
        out = out.rename(columns={colmap["BANGENAN"]: "BANGENAN"})
    if "BACO2AN" in colmap:
        out = out.rename(columns={colmap["BACO2AN"]: "BACO2AN"})
    out["BACODE"] = _normalise_ba_codes(out["BACODE"])
    out["ci_total_g_per_kwh"] = (
        pd.to_numeric(out["BACO2RTA"], errors="coerce")
        * LB_PER_MWH_TO_G_PER_KWH
    )
    out["ci_combustion_g_per_kwh"] = (
        pd.to_numeric(out["BACO2CRT"], errors="coerce")
        * LB_PER_MWH_TO_G_PER_KWH
    )

    keep = [
        column
        for column in [
            "BACODE",
            "BANAME",
            "BANGENAN",
            "BACO2AN",
            "BACO2RTA",
            "BACO2CRT",
            "ci_total_g_per_kwh",
            "ci_combustion_g_per_kwh",
        ]
        if column in out.columns
    ]

    result = out[keep].copy()
    result = result.loc[
        result["BACODE"].notna()
        & result["BACODE"].ne("")
    ].copy()

    _require_unique_ba_codes(
        result,
        "BACODE",
        "eGRID BA factor table",
    )

    return result


def compute_weighted_ci(
    weights: pd.DataFrame,
    ci: pd.DataFrame,
    ba_col: str = "BACODE",
    weight_col: str = "ba_weight",
) -> dict[str, float]:
    """Compute HDC-weighted total-output and combustion-output CI.

    Both inputs must contain one row per balancing authority. The explicit
    one-to-one merge prevents duplicated factor rows from multiplying BA
    weights silently.
    """
    required_factor_columns = {
        ba_col,
        "ci_total_g_per_kwh",
        "ci_combustion_g_per_kwh",
    }
    missing_factor_columns = sorted(
        required_factor_columns.difference(ci.columns)
    )
    if missing_factor_columns:
        raise KeyError(
            f"Missing BA factor columns: {missing_factor_columns}"
        )

    if weight_col not in weights.columns:
        raise KeyError(f"Missing BA weight column: {weight_col}")

    w = weights.copy()
    w = w.drop(
        columns=[
            column
            for column in [
                "ci_total_g_per_kwh",
                "ci_combustion_g_per_kwh",
            ]
            if column in w.columns
        ]
    )
    c = ci.copy()

    w[ba_col] = _normalise_ba_codes(w[ba_col])
    c[ba_col] = _normalise_ba_codes(c[ba_col])

    _require_unique_ba_codes(
        w,
        ba_col,
        "BA weight table",
    )
    _require_unique_ba_codes(
        c,
        ba_col,
        "BA factor table",
    )

    merged = w.merge(
        c[
            [
                ba_col,
                "ci_total_g_per_kwh",
                "ci_combustion_g_per_kwh",
            ]
        ],
        on=ba_col,
        how="left",
        validate="one_to_one",
    )

    missing_total = merged["ci_total_g_per_kwh"].isna()
    if missing_total.any():
        missing_codes = sorted(
            merged.loc[missing_total, ba_col]
            .dropna()
            .unique()
            .tolist()
        )
        raise ValueError(
            f"Missing total-output CI for BA codes: {missing_codes}"
        )

    missing_combustion = merged[
        "ci_combustion_g_per_kwh"
    ].isna()
    if missing_combustion.any():
        missing_codes = sorted(
            merged.loc[missing_combustion, ba_col]
            .dropna()
            .unique()
            .tolist()
        )
        raise ValueError(
            "Missing combustion-output diagnostic CI for BA codes: "
            f"{missing_codes}"
        )

    weights_num = pd.to_numeric(
        merged[weight_col],
        errors="coerce",
    )

    if weights_num.isna().any():
        raise ValueError("BA weights must be numeric")

    if (weights_num < 0).any():
        raise ValueError("BA weights cannot be negative")

    if not (weights_num > 0).any():
        raise ValueError(
            "At least one BA weight must be positive"
        )

    denominator = weights_num.sum()

    total_ci = (
        weights_num * merged["ci_total_g_per_kwh"]
    ).sum() / denominator
    combustion_ci = (
        weights_num
        * merged["ci_combustion_g_per_kwh"]
    ).sum() / denominator

    return {
        "ci_total_g_per_kwh": float(total_ci),
        "ci_combustion_g_per_kwh": float(combustion_ci),
    }


def build_denominator_audit(weighted_ci: dict[str, float], central_twh: float, us_total_ci: float = 348.00014859533) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"basis": "total_output_default", "ci_g_per_kwh": weighted_ci["ci_total_g_per_kwh"], "central_emissions_mt": central_twh * weighted_ci["ci_total_g_per_kwh"] / 1000},
            {"basis": "combustion_output_diagnostic", "ci_g_per_kwh": weighted_ci["ci_combustion_g_per_kwh"], "central_emissions_mt": central_twh * weighted_ci["ci_combustion_g_per_kwh"] / 1000},
            {"basis": "us_egrid_total_output_reference", "ci_g_per_kwh": us_total_ci, "central_emissions_mt": None},
        ]
    )
