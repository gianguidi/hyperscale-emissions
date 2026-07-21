#!/usr/bin/env python3
"""Build Figure-4 input from clean BA fuel shares and Round-3 central BA loads."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

FUELS = [
    "COAL", "GAS", "OIL", "OFSL", "OTHF", "NUCLEAR",
    "BIOMASS", "GEOTHERMAL", "HYDRO", "SOLAR", "WIND",
]

FUEL_CANDIDATES = [
    Path("results/tables/ba_fuel_share.csv"),
    Path("results/tables/ba_fuel_share_egrid2023_rev2.csv"),
]
LOAD_CANDIDATES = [
    Path("results/tables/ba_summary_central_total_output.csv"),
    Path("results/tables/dashboard_ba_export_round3_total_output.csv"),
]
OUT = Path("data/processed/fuel_mix_hyperscalers.csv")


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("None of these files exists: " + ", ".join(map(str, paths)))


def main() -> None:
    fuel_path = first_existing(FUEL_CANDIDATES)
    load_path = first_existing(LOAD_CANDIDATES)
    fuel = pd.read_csv(fuel_path)
    load = pd.read_csv(load_path)

    fuel_key = "BACODE" if "BACODE" in fuel.columns else "region_B_1"
    load_key = "region_B_1" if "region_B_1" in load.columns else "BACODE"

    missing_fuels = [col for col in FUELS if col not in fuel.columns]
    if missing_fuels:
        raise ValueError(f"{fuel_path}: missing fuel columns {missing_fuels}")
    if "electricity_twh" not in load.columns:
        raise ValueError(f"{load_path}: missing electricity_twh")
    if not fuel[fuel_key].is_unique:
        raise ValueError(f"{fuel_path}: duplicate BA codes")
    if not load[load_key].is_unique:
        raise ValueError(f"{load_path}: duplicate BA codes")

    shares = fuel[[fuel_key] + FUELS].copy()
    max_value = float(shares[FUELS].max().max())
    if max_value > 1.5:
        shares[FUELS] = shares[FUELS] / 100.0

    row_sums = shares[FUELS].sum(axis=1)
    if not row_sums.between(0.985, 1.015).all():
        bad = shares.loc[~row_sums.between(0.985, 1.015), [fuel_key] + FUELS]
        raise ValueError(f"Fuel shares do not sum to 1 for some BAs:\n{bad.head()}")

    out = load[[load_key, "electricity_twh"]].merge(
        shares,
        left_on=load_key,
        right_on=fuel_key,
        how="left",
        validate="one_to_one",
    )
    if out[FUELS].isna().any().any():
        missing = out.loc[out[FUELS].isna().any(axis=1), load_key].tolist()
        raise ValueError(f"Missing fuel shares for BAs: {missing}")

    out["region_B_1"] = out[load_key].astype(str)
    # plotting code divides this field by 1e6 to label TWh, so store annual MWh.
    out["Total_MW_scaled"] = out["electricity_twh"] * 1_000_000.0
    out = out[["region_B_1", "Total_MW_scaled"] + FUELS]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {OUT} from {fuel_path} and {load_path}")
    print(f"National central electricity: {out['Total_MW_scaled'].sum()/1e6:.6f} TWh")


if __name__ == "__main__":
    main()
