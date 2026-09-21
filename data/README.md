# Data folder

## `raw/`
Direct CSV conversion of the original `.rda` files from the CASdatasets R package
(`freMTPL2freq.rda`, `freMTPL2sev.rda`), downloaded from
https://github.com/dutangc/CASdatasets. No rows removed, no values changed.

- `freMTPL2freq_raw.csv` — 677,991 policies, 12 columns.
- `freMTPL2sev_raw.csv` — 26,444 individual claims, 2 columns.

## `processed/`
Output of `notebooks/insurance_analysis.ipynb`. All cleaning, capping, merging and
KPI logic is documented in the notebook and in the main `README.md` (§4-5).

| File | Grain | Purpose |
|---|---|---|
| `tableau_portfolio.csv` | 1 row per policy | Main Tableau data source (filters/drill-down) |
| `kpi_portfolio_summary.csv` | 1 row | Q1 — portfolio-wide KPIs |
| `kpi_region_summary.csv` | 1 row per region | Q2 — region comparison |
| `kpi_segment_driver_age.csv` | 1 row per driver-age band | Q3 |
| `kpi_segment_vehicle_age.csv` | 1 row per vehicle-age band | Q3 |
| `kpi_segment_vehicle_power.csv` | 1 row per vehicle-power band | Q3 |
| `kpi_segment_fuel_type.csv` | 1 row per fuel type | Q3 |
| `kpi_segment_bonus_malus.csv` | 1 row per bonus-malus band | Q3 |
| `kpi_frequency_severity_quadrant.csv` | 1 row per driver-age x vehicle-power cell | Q4 — quadrant view |
| `pareto_claim_cost_curve.csv` | ~200 points (downsampled) | Q5 — Pareto / cumulative-cost curve |
| `extreme_claims_for_review.csv` | 1 row per flagged claim | Q6 — claims for manual review (never deleted) |
| `unusual_region_area_cells.csv` | 1 row per flagged Region x Area cell | Q6 — unusual segment combinations |
