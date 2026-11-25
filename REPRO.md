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
data/processed/all_facilities.csv
data/processed/df_emissions_per_dc_SF.geojson
```

The notebook reads its inputs from its working directory (`BASE = Path(os.getcwd())`),
not from `data/`. When running it from `notebooks/`, place these next to it:

```text
notebooks/NEW_hyperscalers_UPDATED_FINAL_df_datacenters_for_analysis.csv   # DUA-protected 403-facility sample
notebooks/egrid2023_data_rev2.xlsx                                          # public EPA eGRID2023 Rev. 2
notebooks/balancing_authorities_polygons/balancing_authorities_EPA.shp     # optional, BA map underlay
```

What each local-only file is used for:

| Local path | Used by | Contents | Public alternative |
|---|---|---|---|
| `data/restricted/analytical_sample_403.csv` | `diagnose_inventory_coverage.py` | DUA-protected 403-facility analytical sample | aggregate exports in `public/` |
| `data/restricted/baxtel_universe_675.csv` | `diagnose_inventory_coverage.py` | DUA-protected 675-facility initial universe | none |
| `NEW_hyperscalers_UPDATED_FINAL_df_datacenters_for_analysis.csv` (notebook folder) | notebook | DUA-protected 403-facility analytical sample | aggregate exports in `public/` |
| `data/processed/all_facilities.csv` | `run_capacity_model.py`, `run_spatial_validation.py` | DUA-protected capacity-model input, one row per facility | `data/synthetic/all_facilities.csv` from `make_synthetic_403_fixture.py`; both scripts fall back to it automatically, or set `HYPERSCALE_FACILITIES_PATH` |
| `data/processed/df_emissions_per_dc_SF.geojson` | `make_figure1_maps.py` (Figure 1a) | DUA-protected facility point geometry | none; Source Data Fig. 1 gives state-level counts |
| `egrid2023_data_rev2.xlsx` (`data/raw/` or notebook folder) | notebook, `audit_plant_inventory.py` | Public EPA eGRID2023 Revision 2 workbook, not committed because of size. Download from https://www.epa.gov/egrid/download-data | BA factors in `data/processed/ba_*_egrid2023_rev2.csv` |
| `data/raw/ba_boundaries.*`, `data/raw/state_boundaries.*`, `balancing_authorities_polygons/` | notebook | Balancing-authority and US Census state boundaries | `data/processed/gdf_EPA_totals.geojson` |

Facility-level outputs are also local-only and gitignored:
`clean_outputs_v6*/` (including `facility_central_total_output.csv` and
`facility_central_combustion_diagnostic.csv`), `imputation_audit.csv` and
`data/processed/facilities_with_predicted_capacity.csv`.
`scripts/check_no_restricted_data.py` runs in CI and fails on tracked files with
facility location columns, point geometry or restricted filename patterns; it does
not inspect other facility attributes, so rely on `.gitignore` and review
`git status` before committing.

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

## Restricted facility-point data

The facility-level point geometry used to prepare manuscript Figure 1a is
protected by the facility-data DUA and is not included in the public
repository. Public reproduction uses synthetic facility records for capacity
model and validation checks, together with aggregated state- and
balancing-authority outputs for the emissions results. No individual facility
coordinates are distributed in the public package.

## Capacity-model specification

The public capacity model uses
`sklearn.ensemble.GradientBoostingRegressor` under scikit-learn 1.9.0.
Every effective, non-deprecated estimator parameter used by the analysis is
specified explicitly in `src/hyperscale_emissions/capacity_model.py`,
including values that coincide with scikit-learn defaults. The deprecated
`criterion` parameter is intentionally omitted because it has no effect in
scikit-learn 1.9.0. The model uses 100 estimators, learning rate 0.1,
squared-error loss, subsample 1.0, maximum tree depth 3, and random seed 42.
The preprocessing pipeline mean-imputes and standardizes building area,
most-frequent-imputes categorical predictors, and one-hot encodes categories
with unknown-category handling enabled.

## Validation split artifact

Running:

```bash
python scripts/make_synthetic_403_fixture.py
python scripts/reproduce_model.py
```

generates the deterministic public artifact:

`results/tables/synthetic_validation/splits.json`

The committed artifact records the fixed random 85/15 split and grouped
validation folds for the public synthetic fixture. Its indices refer only to
synthetic rows and do not identify restricted analytical facilities. Applying
the same scripts to an authorized facility dataset regenerates the
corresponding dataset-specific split metadata.

## Combustion-output diagnostic convention

The combustion-output rate is retained only as a diagnostic. For a balancing
authority with an undefined combustion-output rate, zero reported annual CO2
emissions, and a valid total-output rate, the diagnostic rate is set to that
BA's total-output rate, ordinarily zero. The output flag
`combustion_ci_filled_noncombustion` records each such replacement.
Undefined combustion-output rates associated with positive or unknown annual
CO2 emissions are not silently filled and instead cause validation to fail.

## Plant inventory audit

The official EPA eGRID2023 Revision 2 plant sheet contains 12,612 records.
Of these, 11,545 have positive reported annual net generation and an
assignable balancing-authority code. Restricting the inventory to the
23 balancing authorities represented by the public HDC load weights yields
8,802 unique positive-generation plant records.

`data/processed/plants_with_regions.csv` is a separate cartographic source
file used for figure preparation. It contains 3,318 rows: 3,214 with positive
generation, 22 with zero generation, and 82 with negative net generation.
It is not the full attributional inventory.

The distinction is reproduced with:

```bash
python scripts/audit_plant_inventory.py \
  --egrid-xlsx /path/to/egrid2023_data_rev2.xlsx \
  --expected-attribution-count 8802
```

The resulting audit table is stored at
`results/tables/plant_inventory_audit.csv`.
