#!/usr/bin/env python3
"""Fail if tracked public data contain facility-level locations or point geometry."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

SCAN_PREFIXES = ("data/processed/", "public/", "results/tables/")
SYNTHETIC_PREFIXES = ("data/synthetic/", "tests/fixtures/")
ALLOWED_GEOJSON = {"data/processed/gdf_EPA_totals.geojson"}
RESTRICTED_HEADERS = {
    "full_address",
    "address",
    "street_address",
    "latitude",
    "longitude",
    "lat",
    "lon",
    "lng",
}
RESTRICTED_FILENAME_TOKENS = (
    "per_dc",
    "facility_central",
    "facility_level",
    "coordinates",
    "full_address",
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [Path(x.decode()) for x in result.stdout.split(b"\0") if x]


def walk_json(obj: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from walk_json(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk_json(value)


def inspect_csv(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"could not inspect CSV: {exc}"]
    lowered = {str(col).strip().lower() for col in header}
    bad = sorted(lowered & RESTRICTED_HEADERS)
    if bad:
        issues.append(f"restricted location columns: {', '.join(bad)}")
    return issues


def inspect_json(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"could not inspect JSON/GeoJSON: {exc}"]

    lowered_keys: set[str] = set()
    geometry_types: set[str] = set()
    for key, value in walk_json(data):
        lowered_keys.add(key.strip().lower())
        if key == "type" and isinstance(value, str) and value in {
            "Point",
            "MultiPoint",
            "LineString",
            "MultiLineString",
            "Polygon",
            "MultiPolygon",
            "GeometryCollection",
        }:
            geometry_types.add(value)

    bad = sorted(lowered_keys & RESTRICTED_HEADERS)
    if bad:
        issues.append(f"restricted location keys: {', '.join(bad)}")
    if geometry_types & {"Point", "MultiPoint"}:
        issues.append(
            "facility-like point geometry detected: "
            + ", ".join(sorted(geometry_types & {"Point", "MultiPoint"}))
        )
    return issues


def main() -> int:
    failures: list[str] = []
    for path in tracked_files():
        posix = path.as_posix()
        if posix.startswith(SYNTHETIC_PREFIXES):
            continue
        if not posix.startswith(SCAN_PREFIXES):
            continue
        if not path.exists():
            continue

        lower_name = path.name.lower()
        if any(token in lower_name for token in RESTRICTED_FILENAME_TOKENS):
            failures.append(f"{posix}: restricted filename pattern")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            failures.extend(f"{posix}: {msg}" for msg in inspect_csv(path))
        elif suffix in {".json", ".geojson"} and posix not in ALLOWED_GEOJSON:
            failures.extend(f"{posix}: {msg}" for msg in inspect_json(path))

    if failures:
        print("Restricted-data guard FAILED:\n", file=sys.stderr)
        for failure in failures:
            print(f" - {failure}", file=sys.stderr)
        return 1

    print("Restricted-data guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
