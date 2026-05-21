from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results/tables/national_utilization_scenarios.csv"

EXPECTED = {
    "low_load": {"u": 0.48, "twh": 67.7, "mt": 36.9},
    "central": {"u": 0.58, "twh": 81.8, "mt": 44.6},
    "continuity_u0663": {"u": 0.663, "twh": 93.5, "mt": 51.0},
    "ai_weighted_high": {"u": 0.70, "twh": 98.6, "mt": 53.8},
}

TOL_TWH = 0.20
TOL_MT = 0.20


def get_value(row, candidates):
    for c in candidates:
        if c in row.index:
            return row[c]
    raise KeyError(f"None of these columns found: {candidates}")


def main():
    if not TABLE.exists():
        raise SystemExit(f"CHECK FAILED: Missing {TABLE}; run scripts/run_utilization_scenarios.py first.")

    print(f"Checking {TABLE}")
    df = pd.read_csv(TABLE)

    if "scenario" not in df.columns:
        raise SystemExit("CHECK FAILED: missing scenario column.")

    for scenario, exp in EXPECTED.items():
        sub = df[df["scenario"] == scenario]
        if sub.empty:
            raise SystemExit(f"CHECK FAILED: missing scenario {scenario}.")

        row = sub.iloc[0]

        u = get_value(row, ["utilization_u", "u"])
        twh = get_value(row, ["total_energy_twh", "electricity_twh"])
        mt = get_value(row, ["total_co2_mt", "co2_mt"])

        if abs(u - exp["u"]) > 1e-6:
            raise SystemExit(f"CHECK FAILED: Scenario {scenario}: u={u}, expected {exp['u']}")

        if abs(twh - exp["twh"]) > TOL_TWH:
            raise SystemExit(f"CHECK FAILED: Scenario {scenario}: TWh={twh:.3f}, expected {exp['twh']}")

        if abs(mt - exp["mt"]) > TOL_MT:
            raise SystemExit(f"CHECK FAILED: Scenario {scenario}: Mt={mt:.3f}, expected {exp['mt']}")

        print(f"  OK {scenario}: u={u}, TWh={twh:.3f}, Mt={mt:.3f}")

    print("Paper-output checks passed.")


if __name__ == "__main__":
    main()
