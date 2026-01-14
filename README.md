# hyperscale-emissions

Code for the paper:

> **Assessing the carbon emissions of United States hyperscale data centers**  
> Guidi G., Dominici F., Sprinkle C., Gilmour J., Butler K., Bell E., Delaney S., Bargagli-Stoffi F.J.  
> (submitted to *Nature Sustainability*).

This repository contains:

- A fully specified **scikit-learn pipeline** for estimating data-center power capacity (`current_mw`),
- Code to compute **electricity use and emissions** for U.S. hyperscale data centers,
- Scripts to reproduce the **key figures** (maps, fuel-mix chart) from synthetic/aggregated data,
- A structure that supports reproducibility under a **data use agreement (DUA)**.

Because the underlying facility-level dataset is subject to a DUA, we do **not** release raw facility identifiers or exact locations. Instead, we provide:

- Synthetic / anonymized datasets (to be placed under `data/processed/`),
- Aggregated tables at state / balancing authority level,
- All analysis and plotting code.

---

## Repository structure

- `src/hyperscale_emissions/`
  - `data_io.py` – helpers to load raw and processed data.
  - `capacity_model.py` – estimation of facility power capacity (`current_mw`) with a Gradient Boosting model + preprocessing pipeline.
  - `fuel_mix.py` – computation of national and regional fuel mix for hyperscale load.
  - `plotting_fuel_mix.py` – final Figure 4 fuel-mix plot (grouped fossil / nuclear / renewables).
  - `plotting_maps.py` – Figure 1a (hyperscale facilities) and Figure 1b (power plants by fuel).
  - `utils.py` – small shared utilities.
- `scripts/`
  - `run_capacity_model.py` – trains the capacity model, prints metrics, saves predicted capacities and diagnostics.
  - `make_figure1_maps.py` – generates Figure 1a and 1b from GeoDataFrames or prepared files.
  - `make_figure4_fuel_mix.py` – generates Figure 4 fuel-mix chart.
- `data/`
  - `raw/` – **not tracked** in git; place DUA-protected facility-level dataset, EPA eGRID, EIA inputs here.
  - `processed/` – synthetic, anonymized, or aggregated datasets used in the scripts.
- `results/`
  - `figures/` – PDFs of all figures (e.g., `figure1a_hyperscalers.pdf`, `figure1b_power_plants.pdf`, `figure4_fuel_mix_GROUPED_final.pdf`).
  - `tables/` – CSV tables used in the paper / SI.
- `notebooks/`
  - `NEW_clean_datacenters_datamerge_model.ipynb` – original development notebook (not included in this archive).

---

## Installation

We recommend a fresh conda environment:

```bash
conda env create -f environment.yml
conda activate hyperscale-emissions
```

Or with `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Reproducing the capacity model

The facility-level capacity model estimates `current_mw` for facilities missing reported power capacity.

From the repo root:

```bash
python scripts/run_capacity_model.py
```

This script:

1. Reads a facility dataset from `data/processed/all_facilities.csv` (you should create this from your own pipeline),
2. Splits rows into those **with** and **without** `current_mw`,
3. Trains a Gradient Boosting model with a full preprocessing pipeline (numeric + categorical),
4. Runs 5-fold cross-validation on the training set,
5. Evaluates on a 15% held-out test set and prints:

   - Cross-validated RMSE (MW)  
   - Test MSE  
   - Test R²  
   - Test MAE  
   - Test MAPE  
   - Test mean error (bias)

6. Produces a diagnostic plot: `results/figures/hyp_model_performance.pdf`,
7. Saves a combined dataset with observed and predicted capacity to  
   `data/processed/facilities_with_predicted_capacity.csv`.

In the manuscript, the reported metrics are:

- Cross-Validation RMSE: **21.50 MW**  
- Test MSE: **155.88**  
- Test R²: **0.807**  
- Test MAE: **8.13 MW**  
- Test MAPE: **0.424**  
- Test Mean Error (bias): **–1.33 MW**

---

## Reproducing key figures

### Figure 1a / 1b – Maps of data centers and power plants

Once you have prepared the GeoDataFrames (or equivalent files) for:

- `df_emissions_per_dc_SF` (hyperscale data centers),
- `gdf_EPA_totals` (balancing authority polygons),
- `plants_with_regions` (power plants with primary fuel),

use:

```bash
python scripts/make_figure1_maps.py
```

This will generate:

- `results/figures/figure1a_hyperscalers.pdf`
- `results/figures/figure1b_power_plants.pdf`

### Figure 4 – National + top BA fuel mix

Place a CSV like `fuel_mix_hyperscalers.csv` under `data/processed/`  
with columns:

- `region_B_1` – BA/region id  
- `Total_MW_scaled` – total load assigned to that region  
- fuel share columns: `COAL`, `GAS`, `OIL`, `OFSL`, `OTHF`, `NUCLEAR`, `BIOMASS`, `GEOTHERMAL`, `HYDRO`, `SOLAR`, `WIND` (fractions summing to ~1 per row)

Then run:

```bash
python scripts/make_figure4_fuel_mix.py
```

which produces:

- `results/figures/figure4_fuel_mix_GROUPED_final.pdf`

This is the grouped fossil/nuclear/renewables stacked chart, with per-region TWh labels, per-segment percentages, and group summaries above each bar.

---

## Data availability

The underlying facility-level dataset is covered by a DUA and cannot be shared. This repository is designed so that:

- Reviewers and researchers with access to similar data can reproduce the full pipeline by placing their inputs in `data/raw/` and creating intermediate `data/processed/` files following the documented schema.
- Others can still inspect:
  - The full model specification,
  - The preprocessing steps,
  - The figure-generation code,
  - Example synthetic and aggregated datasets (once added).
    
- The folder named "public" contains aggregated, non-sensitive outputs intended for public release and reproducibility:
    - State-level totals: electricity consumption (TWh) and CO2e emissions
    - Balancing authority totals: electricity consumption (TWh) and CO2e emissions

These files are aggregated summaries and do not include facility-level information.
EOF
---

## Citation

If you use this code, please cite:

> Guidi et al., *Assessing the carbon emissions of United States hyperscale data centers*, 2025.

A machine-readable citation file is provided in `CITATION.cff`.
