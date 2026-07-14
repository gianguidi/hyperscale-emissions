# Reproducibility notes

## Public aggregate reproduction

The public aggregate workflow does not require DUA-protected facility data. It uses:

- `data/processed/ba_load_weights_public_u0663.csv` — aggregate BA load weights from the `u=0.663` scenario.
- `data/processed/ba_effective_emission_factor_egrid2023_rev2.csv` — eGRID2023 Revision 2 BA carbon-intensity factors in gCO2/kWh.

Run:

```bash
python scripts/run_emissions_total_output.py
python scripts/check_paper_outputs.py
```

The key check is that the default total-output denominator reproduces:

- HDC-weighted total-output CI: approximately 314 gCO2/kWh.
- Central/reference scenario: approximately 81.8 TWh and 25.7 Mt CO2.
- Scenario range: approximately 68--99 TWh and 21--31 Mt CO2.

## Total-output versus combustion-output basis

The headline basis is total-output:

```text
BACO2RTA * 0.45359237 = gCO2/kWh
```

The combustion-output diagnostic is:

```text
BACO2CRT * 0.45359237 = gCO2/kWh
```

The diagnostic is not used for headline emissions because it excludes non-combustion generation from the denominator.

## Restricted full reproduction

To run the full facility workflow, place restricted files locally:

```text
data/restricted/analytical_sample_403.csv
data/restricted/baxtel_universe_675.csv
data/raw/egrid2023_data_rev2.xlsx
data/raw/ba_boundaries.*
data/raw/state_boundaries.*
```

Expected facility-level columns include, where available:

```text
company_name
full_address
latitude
longitude
current_mw
FILLED_baxtel_total_building_sqft
region_B_1
STUSPS
climate_type_long
company_type
```

Do not commit restricted facility-level files or outputs.

## Coverage diagnostics

Reviewer-requested 675-to-403 coverage diagnostics can be generated locally as aggregate-only tables:

```bash
python scripts/diagnose_inventory_coverage.py \
  --universe data/restricted/baxtel_universe_675.csv \
  --analytical data/restricted/analytical_sample_403.csv \
  --capacity-col current_mw
```

Outputs are written to `results/tables/restricted_coverage/`, which is gitignored by default.

## Notebook

The notebook under `notebooks/` is output-cleared for public release. It should be run only in a local environment with restricted data available.
