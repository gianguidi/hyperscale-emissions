# Manuscript alignment checklist

Before submitting the revision, verify these items in the repository and manuscript.

## Repository issues to avoid

- Python files must contain real line breaks. A raw file beginning with `import os import sys` will fail immediately.
- `README.md`, `environment.yml`, and `requirements.txt` must contain real line breaks and valid markdown/YAML/text formatting.
- The README must not claim 5-fold CV as the primary method. The revision uses grouped validation and explicit under-/over-prediction metrics.
- The README and scripts must use the central scenario `u=0.58`, not `u=0.663`, for manuscript-facing central figures and tables.
- All public-facing text should say CO2, not CO2e, unless the specific eGRID column used is CO2e.
- If a script cannot run without DUA-protected data, it should fail with a clear message that points to `REPRO.md`.

## Manuscript-facing values

| Quantity | Current paper value |
|---|---:|
| Facilities | 403 |
| Scenarios | 0.48, 0.58, 0.663, 0.70 |
| Central scenario | 0.58 |
| Electricity range | 68--99 TWh |
| CO2 range | 37--54 Mt |
| Central electricity | 81.8 TWh |
| Central CO2 | 44.6 Mt |
| Weighted CI | 545 gCO2/kWh |
| Fossil share | 53.9% |
| Nuclear share | 20.9% |
| Renewable share | 25.3% |

## Required artifacts for reviewers

- `splits.json`
- `REPRO.md`
- `national_utilization_scenarios.csv`
- `state_utilization_scenarios_long.csv`
- `validation_*_metrics.csv`
- figure-generation scripts for Figures 1, 2/3 if applicable, and 4
- a smoke test or GitHub Action demonstrating that the public code imports cleanly
