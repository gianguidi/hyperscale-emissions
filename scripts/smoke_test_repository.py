#!/usr/bin/env python
from pathlib import Path
import importlib
import subprocess
import sys
import os


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    for rel in ["data/processed", "results/tables", "scripts", "src/hyperscale_emissions"]:
        p = root / rel
        if not p.exists():
            raise SystemExit(f"Missing expected path: {p}")
    sys.path.insert(0, str(root / "src"))
    importlib.import_module("hyperscale_emissions")
    print("Package import OK")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    subprocess.run([sys.executable, str(root / "scripts" / "run_emissions_total_output.py"), "--outdir", str(root / "results" / "tables")], check=True, cwd=root, env=env)
    subprocess.run([sys.executable, str(root / "scripts" / "check_paper_outputs.py")], check=True, cwd=root, env=env)
    print("Smoke test passed")

if __name__ == "__main__":
    main()
