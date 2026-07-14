# hyperscale-emissions

Code and reproducibility materials for:

> **Assessing the Carbon Emissions of United States Hyperscale Data Centers**  
> Guidi et al.  
> Submitted to *Nature Sustainability*.

This repository supports reproducibility under a data use agreement (DUA). The facility-level data used in the paper cannot be released publicly because it contains commercially sensitive facility identifiers and locations. The repository is therefore organized in two layers:

1. **Public/reviewer-reproducible layer**: all code, schemas, expected outputs, aggregated tables, figure-generation scripts, and validation artifacts.
2. **Restricted full-reproduction layer**: the same scripts can be run end-to-end when the DUA-protected facility-level and geospatial inputs are placed in the documented local folders.

## Headline results reproduced by the current workflow

Using the 403-facility analytical sample, EPA eGRID2023 Revision 2, and four facility-load scenarios:

| Scenario | Facility-load coefficient | Electricity (TWh) | CO2 (Mt) |
|---|---:|---:|---:|
| Low-load | 0.480 | 67.7 | 21.3 |
| Central/reference | 0.580 | 81.8 | 25.7 |
| Continuity sensitivity | 0.663 | 93.5 | 29.4 |
| AI-weighted high | 0.700 | 98.6 | 31.0 |

The central scenario is `u = 0.58`. The `u = 0.663` scenario is retained for continuity with earlier drafts and with server-level effective-utilization assumptions, but it is not treated as the central facility-level estimate.


## Carbon-intensity denominator

The default workflow uses total-output balancing-authority carbon intensity from EPA eGRID2023 Revision 2:

`total reported CO2 emissions / total reported net generation`

This total-output denominator includes nuclear, renewable, and other non-combustion generation. Combustion-output intensity is retained only as a diagnostic and is not used for headline HDC-attributable emissions.

The current workflow reproduces:
- HDC-weighted total-output CI: approximately 314 gCO2/kWh
- US eGRID total-output average: approximately 348 gCO2/kWh
- combustion-output diagnostic: approximately 543 gCO2/kWh

## Repository structure

```text
hyperscale-emissions/
  README.md
  REPRO.md
  environment.yml
  requirements.txt
  CITATION.cff
  data/
    raw/                 # local only; DUA/EPA/geospatial inputs; not tracked
    processed/           # synthetic/anonymized or aggregated inputs for public scripts
  results/
    tables/              # CSV outputs and validation artifacts
    figures/             # PDF/PNG figures
  scripts/
    run_capacity_model.py
    run_spatial_validation.py
    run_utilization_scenarios.py
    make_figure1_maps.py
    make_figure4_fuel_mix.py
    check_paper_outputs.py
    smoke_test_repository.py
  src/hyperscale_emissions/
    capacity_model.py
    scenario_analysis.py
    validation.py
    fuel_mix.py
    plotting_maps.py
    plotting_fuel_mix.py
    utils.py
  notebooks/
    README.md
```

## Installation

Recommended:

```bash
conda env create -f environment.yml
conda activate hyperscale-emissions
```

Alternative with pip:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Quick smoke test

After cloning the repository and installing dependencies, run:

```bash
python scripts/smoke_test_repository.py
```

This checks that Python files import correctly, the expected folders exist, and the package can be imported. It does not require DUA-protected data.

## Full reviewer reproduction workflow

Place the local input files in `data/processed/` using the schema documented in `REPRO.md`, then run:

```bash
python scripts/run_spatial_validation.py
python scripts/run_utilization_scenarios.py
python scripts/make_figure1_maps.py
python scripts/make_figure4_fuel_mix.py
python scripts/check_paper_outputs.py
```

The expected manuscript-facing outputs are written to `results/tables/` and `results/figures/`.

## Required input schemas

The scripts intentionally accept simple CSV/GeoJSON inputs so that reviewers with access to the restricted data can reproduce the results locally. Required columns are documented in `REPRO.md`.

## Data availability

The DUA-protected facility-level dataset is not publicly released. The public repository should include:

- all code used for capacity modeling, validation, scenario analysis, and figures;
- split artifacts (`splits.json`) and validation tables;
- aggregated state and balancing-authority outputs;
- synthetic or anonymized example inputs that allow scripts to run without exposing sensitive coordinates or facility identifiers.

## Revision analyses (Round 3)

Additional scripts used for the Round 3 total-output eGRID attribution revision:

- `scripts/run_utilization_scenarios.py`  
  Computes national, state, and balancing-authority electricity/emissions totals under multiple facility-load scenarios.

- `scripts/run_spatial_validation.py`  
  Re-runs the capacity-imputation model under grouped validation schemes (balancing authority, state, climate category) and exports split artifacts for reproducibility.

Outputs are written to `results/tables/`.


## Citation

If using this code, please cite the manuscript and the machine-readable `CITATION.cff` file.
