#!/usr/bin/env python3
"""Validate that public aggregate exports reproduce the Round-3 central result."""
from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

EXPECTED_TWH = 81.76108111544468
EXPECTED_MT = 25.67040935586744
EXPECTED_CI = 313.968565552863
TWH_TOL = 0.10
MT_TOL = 0.10
CI_TOL = 0.75

FILES = {
    "state": Path("public/data_state_level.csv"),
    "BA": Path("public/data_BA_level.csv"),
}


def validate(label: str, path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = {"electricity_twh", "co2_mt"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")

    twh = float(df["electricity_twh"].sum())
    mt = float(df["co2_mt"].sum())
    ci = mt / twh * 1000.0

    print(f"{label}: {twh:.6f} TWh, {mt:.6f} Mt CO2, {ci:.3f} gCO2/kWh")
    if abs(twh - EXPECTED_TWH) > TWH_TOL:
        raise AssertionError(f"{path}: electricity total is not Round-3 central")
    if abs(mt - EXPECTED_MT) > MT_TOL:
        raise AssertionError(f"{path}: emissions total is not Round-3 total-output central")
    if abs(ci - EXPECTED_CI) > CI_TOL:
        raise AssertionError(f"{path}: implied CI is not approximately 314 gCO2/kWh")

    if "emissions_basis" in df.columns:
        values = set(df["emissions_basis"].dropna().astype(str))
        if values != {"total_output_co2"}:
            raise AssertionError(f"{path}: unexpected emissions_basis values {values}")


if __name__ == "__main__":
    try:
        for label, path in FILES.items():
            validate(label, path)
    except Exception as exc:
        print(f"Public export validation FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print("Public export validation passed.")
