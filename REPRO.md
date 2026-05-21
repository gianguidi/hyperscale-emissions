# Reproducibility guide

This file documents the exact workflow used to reproduce the manuscript-facing outputs. The workflow is designed for two settings:

1. **Public smoke test**: checks that the repository is internally consistent and importable.
2. **Full reproduction**: requires the DUA-protected facility-level inputs and local geospatial inputs.

## Software

Use the conda environment:

```bash
conda env create -f environment.yml
conda activate hyperscale-emissions
pip install -e .
```

Then verify imports:

```bash
python scripts/smoke_test_repository.py
```

## Required local inputs

### `data/processed/all_facilities.csv`

Used by the capacity model and grouped validation scripts.

Required columns:

| Column | Meaning |
|---|---|
| `current_mw` | observed or imputed total facility electrical capacity in MW |
| `FILLED_baxtel_total_building_sqft` | facility building area in square feet |
| `region_B_1` | balancing-authority code used for the facility |
| `state` or `STUSPS` | state abbreviation |
| `climate_category` | aggregated climate category |

Optional columns: `company_name`, `id`, `capacity_imputed`, `sqft_imputed`.

### `data/processed/df_emissions_per_dc_SF.csv`

Used by scenario analysis.

Required columns:

| Column | Meaning |
|---|---|
| `current_mw` | total facility electrical capacity in MW |
| `region_B_1` | balancing-authority code |
| `state` or `STUSPS` | state abbreviation |

If the file contains `annual_energy_twh` and `annual_co2_mt`, the code can infer BA intensity from the reference table. Otherwise provide `ba_carbon_intensity.csv`.

### `data/processed/ba_carbon_intensity.csv`

Required if BA carbon intensity cannot be inferred from the facility table.

Required columns:

| Column | Meaning |
|---|---|
| `region_B_1` | balancing-authority code |
| `ba_ci_gco2_per_kwh` | BA carbon intensity in gCO2/kWh |

### `data/processed/fuel_mix_hyperscalers.csv`

Used by Figure 4.

Required columns:

| Column | Meaning |
|---|---|
| `region_B_1` | BA code |
| `Total_MW_scaled` | BA-level annual HDC electricity in MWh or load-proportional energy units, as used in the paper workflow |
| `COAL`, `GAS`, `OIL`, `OFSL`, `OTHF`, `NUCLEAR`, `BIOMASS`, `GEOTHERMAL`, `HYDRO`, `SOLAR`, `WIND` | fuel shares that sum to approximately 1 by BA |

### `data/processed/gdf_EPA_totals.geojson`

Balancing-authority geometry used for maps.

### `data/processed/df_emissions_per_dc_SF.geojson`

Facility point layer used for Figure 1a. Public versions should be synthetic or anonymized.

### `data/processed/plants_with_regions.csv`

Power-plant layer used for Figure 1b.

Required columns, using either eGRID-style or friendly names:

| eGRID-style | Friendly fallback |
|---|---|
| `LAT` | `Plant latitude` |
| `LON` | `Plant longitude` |
| `PLNGENAN` | `Plant annual net generation (MWh)` |
| `PLFUELCT` | `Plant primary fuel category` |
| `OPRCODE` | optional; used to aggregate plants by operator and fuel when available |

## Workflow

```bash
python scripts/run_spatial_validation.py
python scripts/run_utilization_scenarios.py
python scripts/make_figure1_maps.py
python scripts/make_figure4_fuel_mix.py
python scripts/check_paper_outputs.py
```

## Expected outputs

Validation outputs:

- `results/tables/validation_random_metrics.csv`
- `results/tables/validation_ba_metrics.csv`
- `results/tables/validation_state_metrics.csv`
- `results/tables/validation_climate_metrics.csv`
- `results/tables/splits.json`

Scenario outputs:

- `results/tables/national_utilization_scenarios.csv`
- `results/tables/state_utilization_scenarios_long.csv`
- `results/tables/ba_utilization_scenarios_long.csv`

Figures:

- `results/figures/figure1a_hyperscalers.pdf`
- `results/figures/figure1b_power_plants.pdf`
- `results/figures/figure4_fuel_mix_GROUPED_final.pdf`

## Manuscript-facing checks

The paper currently reports:

| Quantity | Expected value |
|---|---:|
| HDC count | 403 |
| Low-load electricity | 67.7 TWh |
| Central electricity | 81.8 TWh |
| Continuity scenario electricity | 93.5 TWh |
| AI-weighted high electricity | 98.6 TWh |
| Low-load CO2 | 36.9 Mt |
| Central CO2 | 44.6 Mt |
| Continuity scenario CO2 | 51.0 Mt |
| AI-weighted high CO2 | 53.8 Mt |
| Weighted carbon intensity | 545 gCO2/kWh |
| Fossil share | 53.9% |
| Nuclear share | 20.9% |
| Renewable share | 25.3% |

Run `python scripts/check_paper_outputs.py` after producing the tables to confirm alignment.
