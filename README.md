# Insurance Claims & Portfolio Risk Analytics — Python + Tableau

Descriptive analytics / BI project for a motor-insurance company's analytics team.
Prepares the **freMTPL2** French Motor Third-Party Liability dataset in Python and
builds an executive Tableau dashboard that supports portfolio-risk discussion.

> This is a **descriptive** BI project, not a pricing or underwriting model.
> No group is labeled "high risk" from claim counts alone — exposure and
> portfolio size are always considered together.

---

## 1. Business problem

Management wants a clear view of the motor-insurance portfolio: where claims occur
most frequently, where claim costs are highest, which policy segments deserve closer
attention, and what should be monitored in the next reporting cycle.

## 2. Data source

- **Dataset:** freMTPL2 (French Motor Third-Party Liability), `freMTPL2freq` +
  `freMTPL2sev`, from the **CASdatasets** R package (Dutang & Charpentier).
- **Official documentation:** https://dutangc.github.io/CASdatasets/reference/freMTPL.html
- **Raw files used in this project:** downloaded directly from the package's public
  GitHub repository (`github.com/dutangc/CASdatasets`, files
  `data/freMTPL2freq.rda` and `data/freMTPL2sev.rda`) and converted to CSV with the
  Python `rdata` library. **Full dataset, no sampling:** 677,991 policies and
  26,444 individual claims, observed mainly during 2011–2013.
- **Citation:** Dutang, C. and Charpentier, A., *CASdatasets: Insurance datasets*,
  R package. The original insurer is anonymous/unknown, as stated in the package
  documentation.
- **Known constraint:** freMTPL2 does **not** include written premium. **Loss Ratio
  is therefore never calculated anywhere in this project.** The core KPIs are claim
  frequency, claim severity and total claim cost.

## 3. Data dictionary

| Column | Table | Description |
|---|---|---|
| `IDpol` | freq, sev | Policy ID (join key) |
| `ClaimNb` | freq | Number of claims during the observed exposure (capped at 4, see §4) |
| `Exposure` | freq | Duration of observation, in years (capped at 1.0, see §4) |
| `VehPower` | freq | Vehicle power, ordinal (4 = lowest ... 15 = highest) |
| `VehAge` | freq | Vehicle age in years |
| `DrivAge` | freq | Driver age in years |
| `BonusMalus` | freq | French bonus-malus score (50 = base/no-claims discount level; higher = worse claims history) |
| `VehBrand` | freq | Vehicle brand, coded `B1`–`B14` |
| `VehGas` | freq | Fuel type: `Diesel` / `Regular` |
| `Area` | freq | Density category, `A` (rural) to `F` (urban) |
| `Density` | freq | Population density of the policyholder's town |
| `Region` | freq | French administrative region (pre-2016 naming) |
| `ClaimAmount` | sev | Cost of one individual claim, in EUR |

## 4. Cleaning & merge logic (see `notebooks/insurance_analysis.ipynb` for full detail)

1. **Quality checks first:** no missing values in either table, no duplicate policy
   IDs, and every `ClaimNb` matches the actual number of severity rows for that
   policy exactly (0 mismatches across 677,991 policies) — the two tables are
   internally consistent.
2. **Two documented data-entry artefacts are corrected, not deleted:**
   - `Exposure` cannot exceed 1.0 (one observation year). 1,224 rows had values up
     to ~2.01 → **capped at 1.0**.
   - 5 policies (same region/density cell) reported 8–16 claims within a fraction
     of a year of exposure — an encoding artefact rather than genuine claims
     behaviour → `ClaimNb` **capped at 4**.
   - 48 rows carry a `VehAge` of 99 or 100 — a placeholder "unknown" code, not a
     99-year-old car. Rows are **kept** and simply fall into the open-ended
     "16+ years" vehicle-age band.
3. **Merge:** `sev` is aggregated to one row per `IDpol` first (`sum(ClaimAmount)`,
   `count(claims)`), **then** left-joined onto `freq`. This guarantees the final
   analysis table has exactly one row per policy (677,991 rows) — the correct grain
   for portfolio KPIs — while a sanity check confirms no claim cost is lost or
   duplicated in the join.
4. **Segmentation:** driver-age, vehicle-age, vehicle-power and bonus-malus bands
   are built with business-sensible cut points (legal driving age, new/old vehicle
   thresholds, the bonus-malus "50" baseline), not arbitrary quantiles.

## 5. KPI definitions

| KPI | Formula | Why |
|---|---|---|
| Policy Count | count of unique `IDpol` | portfolio size |
| Total Exposure | Σ `Exposure` | policy-years actually observed |
| Claim Count | Σ `ClaimNb` | raw claim volume |
| **Claim Frequency** | Claim Count / Total Exposure | claims *per policy-year* — comparable across segments of different sizes |
| Total Claim Cost | Σ `ClaimAmount` | overall cost burden |
| **Average Claim Severity** | Total Claim Cost / number of claim records | average cost *per claim* (not per policy) |

`Loss Ratio` is intentionally **not** part of this KPI set (no premium data available).

## 6. Python analysis steps

1. Load `freMTPL2freq_raw.csv` / `freMTPL2sev_raw.csv`.
2. Quality checks (missing values, duplicates, cross-table consistency).
3. Cap the two documented data-entry artefacts (§4).
4. Aggregate claim cost to policy level, merge onto `freq`.
5. Build driver-age / vehicle-age / vehicle-power / bonus-malus segments.
6. Compute portfolio, region and segment KPI tables (one shared `kpi_table()`
   function used everywhere, so every number in every table is consistent).
7. Frequency-vs-severity quadrant analysis, Pareto analysis, outlier review.
8. Export all Tableau-ready CSV tables to `data/processed/`.

Full runnable notebook: `notebooks/insurance_analysis.ipynb`
(equivalent plain script: `notebooks/insurance_analysis_pipeline.py`).

## 7. Tableau dashboard structure

Three pages, built from the CSVs in `data/processed/` — see
`tableau/dashboard_build_guide.md` for exact calculated-field formulas, chart
types and the filter/action wiring for each page:

- **Page 1 — Executive Portfolio Overview:** KPI cards (policy count, exposure,
  claim count, frequency, total cost, avg. severity), a region comparison bar
  chart, and region/segment filters.
- **Page 2 — Claims & Risk Segments:** driver-age / vehicle-age / vehicle-power /
  bonus-malus comparisons and a frequency-vs-severity scatter/quadrant, with
  highlight/filter actions.
- **Page 3 — Claim Cost Concentration:** Pareto (cumulative cost) curve, top
  extreme claims table, unusual segment cells, and the three business
  recommendations.

## 8. Key findings (see `report/business_summary.md` for full detail)

- Portfolio-wide claim frequency is **~7 claims per 100 policy-years**, with an
  average severity of **~€2,266** per claim and **~€59.9M** total claim cost across
  the observed period.
- **Centre** and **Rhône-Alpes** carry the largest absolute claim cost, but
  **Rhône-Alpes** and **Île-de-France** stand out on frequency once exposure is
  accounted for — a very different picture than ranking by raw claim count.
- **Young drivers (18–25)** are both the highest-frequency *and* highest-severity
  segment by a wide margin.
- Claim cost is heavily concentrated: the **top 5% of claims generate ~52%** of
  total claim cost, and the **top 1% alone generate ~38%**.

## 9. Limitations

- The insurer is anonymous and the data is historical (2011–2013); patterns may
  not reflect the current market.
- No premium data → no Loss Ratio, no profitability conclusion, only frequency /
  severity / cost.
- Only the risk features present in the dataset are used; real underwriting uses
  many more factors.
- All patterns described are **associations**, not causal effects.

## 10. Repository structure

```
insurance-claims-dashboard/
  README.md
  requirements.txt
  build_notebook.py                      # (dev script that generated the .ipynb)
  notebooks/
    insurance_analysis.ipynb             # main, executed notebook
    insurance_analysis_pipeline.py       # equivalent plain .py script
  data/
    raw/freMTPL2freq_raw.csv
    raw/freMTPL2sev_raw.csv
    processed/tableau_portfolio.csv      # main Tableau data source
    processed/kpi_*.csv                  # pre-aggregated KPI tables
    processed/pareto_claim_cost_curve.csv
    processed/extreme_claims_for_review.csv
    processed/unusual_region_area_cells.csv
    README.md
  tableau/
    dashboard_build_guide.md             # exact calculated fields & layout
  figures/
    dashboard_preview.html               # interactive HTML reference build
  report/
    business_summary.md                  # Q1-Q8 answers + 3 recommendations
```

## 11. Reproducing the analysis

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace notebooks/insurance_analysis.ipynb
```

This regenerates every CSV in `data/processed/`, ready to be plugged into Tableau
by following `tableau/dashboard_build_guide.md`.
