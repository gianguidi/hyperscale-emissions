from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

LB_PER_MWH_TO_G_PER_KWH = 0.45359237


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


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
    out["BACODE"] = out["BACODE"].astype(str).str.strip()
    out["ci_total_g_per_kwh"] = pd.to_numeric(out["BACO2RTA"], errors="coerce") * LB_PER_MWH_TO_G_PER_KWH
    out["ci_combustion_g_per_kwh"] = pd.to_numeric(out["BACO2CRT"], errors="coerce") * LB_PER_MWH_TO_G_PER_KWH
    keep = [c for c in ["BACODE", "BANAME", "BANGENAN", "BACO2AN", "BACO2RTA", "BACO2CRT", "ci_total_g_per_kwh", "ci_combustion_g_per_kwh"] if c in out.columns]
    return out[keep].dropna(subset=["BACODE"])


def compute_weighted_ci(weights: pd.DataFrame, ci: pd.DataFrame, ba_col: str = "BACODE", weight_col: str = "ba_weight") -> dict[str, float]:
    """Compute HDC-weighted total-output and combustion-output CI.

    `weights[weight_col]` can be any positive BA-level load weights. The result
    is invariant to scenario scaling when the BA distribution is unchanged.
    """
    w = weights.copy()
    # Some public aggregate weight files already include CI columns for convenience.
    # Drop them before merging with the authoritative factor table to avoid suffixes.
    w = w.drop(columns=[col for col in ["ci_total_g_per_kwh", "ci_combustion_g_per_kwh"] if col in w.columns])
    w[ba_col] = w[ba_col].astype(str).str.strip()
    c = ci.copy()
    c[ba_col] = c[ba_col].astype(str).str.strip()
    merged = w.merge(c[[ba_col, "ci_total_g_per_kwh", "ci_combustion_g_per_kwh"]], on=ba_col, how="left")
    if merged["ci_total_g_per_kwh"].isna().any():
        missing = sorted(merged.loc[merged["ci_total_g_per_kwh"].isna(), ba_col].unique())
        raise ValueError(f"Missing CI for BA codes: {missing}")
    weights_num = pd.to_numeric(merged[weight_col], errors="coerce")
    if weights_num.isna().any() or (weights_num <= 0).all():
        raise ValueError("BA weights must be numeric and positive")
    total_ci = (weights_num * merged["ci_total_g_per_kwh"]).sum() / weights_num.sum()
    combust_ci = (weights_num * merged["ci_combustion_g_per_kwh"]).sum() / weights_num.sum()
    return {
        "ci_total_g_per_kwh": float(total_ci),
        "ci_combustion_g_per_kwh": float(combust_ci),
    }


def build_denominator_audit(weighted_ci: dict[str, float], central_twh: float, us_total_ci: float = 348.00014859533) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"basis": "total_output_default", "ci_g_per_kwh": weighted_ci["ci_total_g_per_kwh"], "central_emissions_mt": central_twh * weighted_ci["ci_total_g_per_kwh"] / 1000},
            {"basis": "combustion_output_diagnostic", "ci_g_per_kwh": weighted_ci["ci_combustion_g_per_kwh"], "central_emissions_mt": central_twh * weighted_ci["ci_combustion_g_per_kwh"] / 1000},
            {"basis": "us_egrid_total_output_reference", "ci_g_per_kwh": us_total_ci, "central_emissions_mt": None},
        ]
    )
