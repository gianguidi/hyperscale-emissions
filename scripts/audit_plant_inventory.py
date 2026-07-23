#!/usr/bin/env python3
"""Audit the public figure layer and full eGRID attribution plant counts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DISPLAY_GENERATION_COLUMNS = [
    "Plant annual net generation (MWh)",
    "PLNGENAN",
    "annual_net_generation_mwh",
]


def normalise_codes(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.upper()
    )


def find_column(
    columns: list[str],
    candidates: list[str],
    label: str,
) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    raise KeyError(
        f"Could not find {label}. Columns: {columns}"
    )


def display_metrics(path: Path) -> list[dict[str, object]]:
    df = pd.read_csv(path)
    generation_col = find_column(
        list(df.columns),
        DISPLAY_GENERATION_COLUMNS,
        "display generation column",
    )

    generation = pd.to_numeric(
        df[generation_col],
        errors="coerce",
    )

    return [
        {
            "scope": "public_figure_source",
            "metric": "rows",
            "value": len(df),
        },
        {
            "scope": "public_figure_source",
            "metric": "positive_generation_rows",
            "value": int((generation > 0).sum()),
        },
        {
            "scope": "public_figure_source",
            "metric": "zero_generation_rows",
            "value": int((generation == 0).sum()),
        },
        {
            "scope": "public_figure_source",
            "metric": "negative_generation_rows",
            "value": int((generation < 0).sum()),
        },
        {
            "scope": "public_figure_source",
            "metric": "missing_generation_rows",
            "value": int(generation.isna().sum()),
        },
    ]


def attribution_metrics(
    workbook: Path,
    weights_path: Path,
) -> list[dict[str, object]]:
    sheets = pd.ExcelFile(workbook).sheet_names
    plant_sheet = next(
        (
            sheet
            for sheet in sheets
            if sheet.upper().startswith("PLNT")
        ),
        None,
    )
    if plant_sheet is None:
        raise ValueError(
            f"No PLNT sheet found. Sheets: {sheets}"
        )

    plants = pd.read_excel(
        workbook,
        sheet_name=plant_sheet,
        header=1,
    )

    required = {"BACODE", "PLNGENAN"}
    missing = sorted(required.difference(plants.columns))
    if missing:
        raise KeyError(
            f"Plant sheet missing columns: {missing}"
        )

    weights = pd.read_csv(weights_path)
    weight_ba_col = find_column(
        list(weights.columns),
        ["BACODE", "region_B_1"],
        "BA column in public weight file",
    )

    hdc_bas = set(
        normalise_codes(weights[weight_ba_col])
        .dropna()
        .loc[lambda x: x.ne("")]
        .tolist()
    )

    plant_ba = normalise_codes(plants["BACODE"])
    generation = pd.to_numeric(
        plants["PLNGENAN"],
        errors="coerce",
    )

    positive = generation.gt(0)
    assignable_ba = (
        plant_ba.notna()
        & plant_ba.ne("")
    )
    in_hdc_ba = plant_ba.isin(hdc_bas)

    attribution_mask = (
        positive
        & assignable_ba
        & in_hdc_ba
    )

    metrics = [
        {
            "scope": "raw_egrid_plant_sheet",
            "metric": "rows",
            "value": len(plants),
        },
        {
            "scope": "raw_egrid_plant_sheet",
            "metric": "positive_generation_assignable_ba",
            "value": int(
                (positive & assignable_ba).sum()
            ),
        },
        {
            "scope": "hdc_ba_attribution_layer",
            "metric": "represented_ba_codes",
            "value": len(hdc_bas),
        },
        {
            "scope": "hdc_ba_attribution_layer",
            "metric": "positive_generation_assignable_ba_rows",
            "value": int(attribution_mask.sum()),
        },
    ]

    if "ORISPL" in plants.columns:
        metrics.append(
            {
                "scope": "hdc_ba_attribution_layer",
                "metric": "unique_plant_ids",
                "value": int(
                    plants.loc[
                        attribution_mask,
                        "ORISPL",
                    ].nunique(dropna=True)
                ),
            }
        )

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--display-csv",
        type=Path,
        default=Path(
            "data/processed/plants_with_regions.csv"
        ),
    )
    parser.add_argument(
        "--ba-weights",
        type=Path,
        default=Path(
            "data/processed/"
            "ba_load_weights_public_u0663.csv"
        ),
    )
    parser.add_argument(
        "--egrid-xlsx",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--expected-attribution-count",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "results/tables/"
            "plant_inventory_audit.csv"
        ),
    )
    args = parser.parse_args()

    rows = display_metrics(args.display_csv)

    if args.egrid_xlsx is not None:
        rows.extend(
            attribution_metrics(
                args.egrid_xlsx,
                args.ba_weights,
            )
        )

    output = pd.DataFrame(rows)
    args.out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.to_csv(args.out, index=False)

    print(output.to_string(index=False))
    print(f"\nWrote {args.out}")

    if args.expected_attribution_count is not None:
        matches = output.loc[
            (
                output["scope"]
                == "hdc_ba_attribution_layer"
            )
            & (
                output["metric"]
                == "positive_generation_assignable_ba_rows"
            ),
            "value",
        ]

        if matches.empty:
            raise SystemExit(
                "Expected-count validation requires "
                "--egrid-xlsx."
            )

        observed = int(matches.iloc[0])
        expected = args.expected_attribution_count

        if observed != expected:
            raise SystemExit(
                "Plant-count validation FAILED: "
                f"expected {expected:,}, "
                f"observed {observed:,}."
            )

        print(
            "Plant-count validation passed: "
            f"{observed:,} attribution-layer rows."
        )


if __name__ == "__main__":
    main()
