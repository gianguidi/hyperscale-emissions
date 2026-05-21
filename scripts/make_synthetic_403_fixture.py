from pathlib import Path
import numpy as np
import pandas as pd

DATA_PATH = Path("data/processed/df_emissions_per_dc_SF.csv")

TARGET_ROWS = 403
TARGET_LOW_TWH = 67.7
LOW_U = 0.48
CENTRAL_U = 0.58
REFERENCE_CI_G_PER_KWH = 545.0  # paper central weighted carbon intensity

POWER_DENSITY_KW_PER_M2 = 1.60
SQM_TO_SQFT = 10.7639

if not DATA_PATH.exists():
    raise FileNotFoundError(f"Missing {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# Remove prior synthetic fixture rows if script is rerun
if "is_synthetic_fixture" in df.columns:
    df = df[df["is_synthetic_fixture"] != True].copy()

required = ["current_mw", "region_B_1"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise KeyError(f"Missing required columns: {missing}")

current_rows = len(df)
rows_to_add = TARGET_ROWS - current_rows

if rows_to_add < 0:
    raise ValueError(f"Current file has {current_rows} rows, more than target {TARGET_ROWS}.")
if rows_to_add == 0:
    print(f"File already has {TARGET_ROWS} non-synthetic rows. Recomputing reference columns only.")

target_total_mw = TARGET_LOW_TWH * 1_000_000 / (8760 * LOW_U)
current_total_mw = df["current_mw"].sum()
missing_mw = target_total_mw - current_total_mw

if rows_to_add > 0 and missing_mw <= 0:
    raise ValueError(
        f"Need to add {rows_to_add} rows, but current total MW already exceeds target. "
        f"Current MW={current_total_mw:.3f}, target MW={target_total_mw:.3f}"
    )

if rows_to_add > 0:
    # Smooth synthetic capacities that sum exactly to missing_mw
    weights = np.linspace(0.85, 1.15, rows_to_add)
    weights = weights / weights.sum()
    synthetic_mw = missing_mw * weights

    # Use common BAs from the synthetic file so rows pass schema checks
    ba_values = (
        df["region_B_1"]
        .dropna()
        .astype(str)
        .value_counts()
        .index
        .tolist()
    )
    if not ba_values:
        ba_values = ["PJM"]

    climate_values = (
        df["climate_category"].dropna().astype(str).unique().tolist()
        if "climate_category" in df.columns
        else ["synthetic_mixed_climate"]
    )
    if not climate_values:
        climate_values = ["synthetic_mixed_climate"]

    new_rows = []
    for i, mw in enumerate(synthetic_mw, start=1):
        row = {c: np.nan for c in df.columns}

        row["current_mw"] = float(mw)
        row["region_B_1"] = ba_values[(i - 1) % len(ba_values)]

        if "FILLED_baxtel_total_building_sqft" in df.columns:
            sqm = mw * 1000 / POWER_DENSITY_KW_PER_M2
            row["FILLED_baxtel_total_building_sqft"] = float(sqm * SQM_TO_SQFT)

        if "climate_category" in df.columns:
            row["climate_category"] = climate_values[(i - 1) % len(climate_values)]

        if "company_name" in df.columns:
            row["company_name"] = "Synthetic reproducibility fixture"

        if "facility_id" in df.columns:
            row["facility_id"] = f"SYNTHETIC_FIXTURE_{i:02d}"

        row["is_synthetic_fixture"] = True
        new_rows.append(row)

    synth = pd.DataFrame(new_rows)

    if "is_synthetic_fixture" not in df.columns:
        df["is_synthetic_fixture"] = False

    df = pd.concat([df, synth], ignore_index=True)

else:
    if "is_synthetic_fixture" not in df.columns:
        df["is_synthetic_fixture"] = False

# Add reference columns used by scenario_analysis.py to infer CI
df["annual_energy_twh"] = df["current_mw"] * 8760 * CENTRAL_U / 1_000_000
df["annual_co2_mt"] = df["annual_energy_twh"] * (REFERENCE_CI_G_PER_KWH / 1000)

# Save backup once
backup = DATA_PATH.with_suffix(".before_synthetic_403.csv")
if not backup.exists():
    pd.read_csv(DATA_PATH).to_csv(backup, index=False)
    print(f"Wrote backup: {backup}")

df.to_csv(DATA_PATH, index=False)

print(f"Wrote {DATA_PATH}")
print(f"Rows: {len(df)}")
print(f"Synthetic rows: {int(df['is_synthetic_fixture'].sum())}")
print(f"Total current_mw: {df['current_mw'].sum():.3f}")

for u in [0.48, 0.58, 0.663, 0.70]:
    twh = df["current_mw"].sum() * 8760 * u / 1_000_000
    mt = twh * (REFERENCE_CI_G_PER_KWH / 1000)
    print(f"u={u}: {twh:.3f} TWh, {mt:.3f} Mt CO2")
