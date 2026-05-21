# Notebooks

The manuscript should be reproducible through the scripts in `scripts/` and the documented schemas in `REPRO.md`.

Development notebooks may be retained here for transparency, but they should not be the only way to reproduce the paper. If a notebook is included for review, it should:

1. have all absolute paths removed;
2. use EPA eGRID2023 Revision 2 as the current manuscript attribution layer;
3. report four facility-load scenarios: 0.48, 0.58, 0.663, and 0.70;
4. use `u=0.58` as the central manuscript scenario;
5. use CO2 terminology consistently, not CO2e, unless the corresponding eGRID columns are explicitly CO2e;
6. write outputs to `results/tables/` and `results/figures/` or clearly document any alternative output directory.
