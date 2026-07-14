# hyperscale-emissions

Code and reproducibility materials for:

> **Assessing the Carbon Emissions of United States Hyperscale Data Centers**  
> Guidi et al.  
> Round 3 revision for *Nature Sustainability*.

This repository supports reproducibility under a data-use agreement (DUA). The facility-level data used in the paper cannot be released publicly because it contains commercially sensitive facility identifiers, addresses, coordinates, and facility attributes. The repository is therefore organized in two layers:

1. **Public/reviewer-reproducible layer:** code, aggregate BA/state outputs, figure exports, denominator-audit tables, schemas, and smoke tests that do not expose facility-level data.
2. **Restricted full-reproduction layer:** the same scripts and notebook can be run end-to-end when the DUA-protected facility-level and geospatial inputs are placed in the documented local folders.

## Round 3 headline results

Using the 403-facility analytical sample, EPA eGRID2023 Revision 2, and the **total-output balancing-authority attribution basis**:

| Scenario | Facility-load coefficient | Electricity (TWh) | CO2 (Mt), total-output basis |
|---|---:|---:|---:|
| Low-load | 0.480 | 67.7 | 21.3 |
| Central/reference | 0.580 | 81.8 | 25.7 |
| Continuity sensitivity | 0.663 | 93.5 | 29.4 |
| AI-weighted high | 0.700 | 98.6 | 31.0 |

The central scenario is `u = 0.58`. The `u = 0.663` scenario is retained for continuity with earlier server-level utilization framing and is not treated as the central facility-level estimate.

## Emissions basis

The Round 3 headline emissions use total-output balancing-authority carbon intensity:

\[
CI_b^{total} = \frac{\sum_{p \in b} CO2_p}{\sum_{p \in b} G_p}
\]

where the denominator includes all reported net generation in the balancing authority, including nuclear, renewable, and other non-combustion generation. The combustion-output intensity is retained only as a diagnostic.

| Metric | HDC-weighted BA CI (gCO2/kWh) | Use in manuscript |
|---|---:|---|
| Total-output CI | 314 | Headline basis |
| Combustion-output CI | 543 | Diagnostic only |
| US eGRID total-output average | 348 | Reference value |

The HDC-weighted attributed fuel mix is approximately **53.9% fossil**, **20.9% nuclear**, and **25.3% renewable**.


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
  MANUSCRIPT_ALIGNMENT.md
  environment.yml
  requirements.txt
  pyproject.toml
  CITATION.cff
  data/
    processed/          # public aggregate inputs and eGRID-derived BA factors
    raw/                # local only; EPA/geospatial inputs; not tracked
    restricted/         # local only; DUA-protected facility inputs; not tracked
  results/
    tables/             # public aggregate output tables used in manuscript checks
    figures/            # manuscript-facing figure PDFs
  scripts/
    run_emissions_total_output.py
    run_utilization_scenarios.py
    audit_emissions_basis.py
    diagnose_inventory_coverage.py
    check_paper_outputs.py
    smoke_test_repository.py
  src/hyperscale_emissions/
    attribution.py
    scenario_analysis.py
    coverage.py
  notebooks/
    FINAL_REVIEW_clean_hyperscale_emissions_v6_ROUND3_TOTAL_OUTPUT.ipynb
  tests/
    test_attribution_basis.py
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

```bash
python scripts/smoke_test_repository.py
```

This imports the package, regenerates the public aggregate Round 3 scenario totals, and checks that the manuscript-facing outputs match the revised paper values.

## Reproduce public aggregate outputs

```bash
python scripts/run_emissions_total_output.py
python scripts/audit_emissions_basis.py
python scripts/check_paper_outputs.py
```

Expected outputs are written to `results/tables/`.

## Restricted full-reproduction workflow

The full notebook and map-generation workflow requires the DUA-protected 403-facility analytical sample, the 675-facility initial universe, and local BA/state geospatial files. Place those files locally under `data/restricted/` and `data/raw/` following `REPRO.md`, then run the notebook:

```text
notebooks/FINAL_REVIEW_clean_hyperscale_emissions_v6_ROUND3_TOTAL_OUTPUT.ipynb
```
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

The notebook outputs the manuscript-facing figures and aggregate tables. Facility-level outputs should **not** be committed.

## Data availability

The DUA-protected facility-level dataset is not publicly released. Public files in this repository are aggregate tables, eGRID-derived BA factors, smoke-test inputs, and figure exports. These materials are sufficient to verify the Round 3 emissions denominator, headline scenario totals, fuel-mix alignment, and manuscript-output checks without exposing sensitive facility-level records.

## Citation

If using this code, please cite the manuscript and the machine-readable `CITATION.cff` file.
