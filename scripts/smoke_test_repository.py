#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REQUIRED_DIRS = [
    ROOT / "src" / "hyperscale_emissions",
    ROOT / "scripts",
    ROOT / "data" / "processed",
    ROOT / "results" / "tables",
    ROOT / "results" / "figures",
]


def main() -> None:
    print("Smoke testing repository structure...")
    for d in REQUIRED_DIRS:
        if not d.exists():
            raise SystemExit(f"Missing required directory: {d}")
        print(f"  OK directory: {d.relative_to(ROOT)}")

    py_files = list((ROOT / "src" / "hyperscale_emissions").glob("*.py")) + list((ROOT / "scripts").glob("*.py"))
    for path in py_files:
        py_compile.compile(str(path), doraise=True)
        print(f"  OK syntax: {path.relative_to(ROOT)}")

    import hyperscale_emissions  # noqa: F401
    from hyperscale_emissions.scenario_analysis import DEFAULT_SCENARIOS  # noqa: F401
    print("  OK import: hyperscale_emissions")
    print(f"  Scenarios: {DEFAULT_SCENARIOS}")
    print("Repository smoke test passed.")


if __name__ == "__main__":
    main()
