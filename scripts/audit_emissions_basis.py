#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from hyperscale_emissions.attribution import compute_weighted_ci, build_denominator_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit total-output versus combustion-output emissions bases.")
    parser.add_argument("--ba-weights", default="data/processed/ba_load_weights_public_u0663.csv")
    parser.add_argument("--ba-factors", default="data/processed/ba_effective_emission_factor_egrid2023_rev2.csv")
    parser.add_argument("--central-twh", type=float, default=81.76108111544468)
    parser.add_argument("--out", default="results/tables/denominator_audit_round3.csv")
    args = parser.parse_args()
    weights = pd.read_csv(args.ba_weights)
    factors = pd.read_csv(args.ba_factors)
    ci = compute_weighted_ci(weights, factors)
    audit = build_denominator_audit(ci, args.central_twh)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.out, index=False)
    print(audit.round(3).to_string(index=False))

if __name__ == "__main__":
    main()
