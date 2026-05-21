from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT = DATA_DIR / "df_emissions_per_dc_SF.csv"
BA_OUT = DATA_DIR / "ba_carbon_intensity_reference.csv"
ALL_FACILITIES = DATA_DIR / "all_facilities.csv"

N_TARGET = 403
TARGET_TOTAL_MW = 81.804e6 / (8760 * 0.58)  # reproduces central 81.804 TWh
TARGET_CI = 545.0  # gCO2/kWh, manuscript central weighted CI

rng = np.random.default_rng(42)

if ALL_FACILITIES.exists():
    df = pd.read_csv(ALL_FACILITIES)
else:
    df = pd.DataFrame()

required_defaults = {
    "current_mw": rng.lognormal(mean=np.log(36), sigma=0.65, size=max(len(df), N_TARGET)),
    "FILLED_baxtel_total_building_sqft": rng.lognormal(mean=np.log(220000), sigma=0.55, size=max(len(df), N_TARGET)),
    "climate_category": rng.choice(["hot summer", "cold (all year long)", "hot (all year long)"], size=max(len(df), N_TARGET)),
    "company_name": [f"Synthetic operator {i+1}" for i in range(max(len(df), N_TARGET))],
    "region_B_1": rng.choice(
        ["PJM", "MISO", "SWPP", "PACW", "BPAT", "ERCO", "TVA", "CISO", "DUK", "SRP"],
        size=max(len(df), N_TARGET),
        p=[0.36, 0.12, 0.10, 0.09, 0.08, 0.07, 0.05, 0.03, 0.05, 0.05],
    ),
}

if df.empty:
    df = pd.DataFrame({k: v[:N_TARGET] for k, v in required_defaults.items()})
else:
    for col, values in required_defaults.items():
        if col not in df.columns:
            df[col] = values[:len(df)]

    # Keep only needed columns for public synthetic reproducibility.
    keep = [
        "current_mw",
        "FILLED_baxtel_total_building_sqft",
        "climate_category",
        "company_name",
        "region_B_1",
    ]
    df = df[keep].copy()

    # Expand or trim to exactly 403 synthetic facilities.
    if len(df) < N_TARGET:
        extra = df.sample(N_TARGET - len(df), replace=True, random_state=42).copy()
        extra["company_name"] = [f"Synthetic added facility {i+1}" for i in range(len(extra))]
        # perturb copied capacities slightly so synthetic rows are not duplicates
        extra["current_mw"] = extra["current_mw"].astype(float) * rng.uniform(0.85, 1.15, size=len(extra))
        df = pd.concat([df, extra], ignore_index=True)
    elif len(df) > N_TARGET:
        df = df.sample(N_TARGET, random_state=42).reset_index(drop=True)

# Coerce and fill.
df["current_mw"] = pd.to_numeric(df["current_mw"], errors="coerce")
df["current_mw"] = df["current_mw"].fillna(df["current_mw"].median())
df.loc[df["current_mw"] <= 0, "current_mw"] = df["current_mw"].median()

# Rescale synthetic capacities so manuscript scenario totals reproduce.
df["current_mw"] = df["current_mw"] * (TARGET_TOTAL_MW / df["current_mw"].sum())

# Clean required columns.
df["region_B_1"] = df["region_B_1"].fillna("PJM").astype(str)
df["climate_category"] = df["climate_category"].fillna("hot summer").astype(str)
df["company_name"] = df["company_name"].fillna("Synthetic operator").astype(str)
df["FILLED_baxtel_total_building_sqft"] = pd.to_numeric(
    df["FILLED_baxtel_total_building_sqft"], errors="coerce"
).fillna(220000)

df.to_csv(OUT, index=False)

# BA carbon intensity reference. Constant CI makes the synthetic fixture reproduce
# the manuscript national CI exactly while avoiding disclosure of facility-level data.
bas = sorted(df["region_B_1"].dropna().unique())
ba_ref = pd.DataFrame(
    {
        "region_B_1": bas,
        "weighted_ci_g_per_kwh": [TARGET_CI] * len(bas),
    }
)
ba_ref.to_csv(BA_OUT, index=False)

print(f"Wrote {OUT}")
print(f"Wrote {BA_OUT}")
print(f"n_facilities: {len(df)}")
print(f"total_current_mw: {df['current_mw'].sum():.6f}")
print(f"central_twh_check: {df['current_mw'].sum() * 8760 * 0.58 / 1e6:.3f}")
print(df.head())
