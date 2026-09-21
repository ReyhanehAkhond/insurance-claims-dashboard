# Tableau Dashboard Build Guide

This guide gives the exact steps to rebuild the 3-page executive dashboard in
Tableau Desktop or Tableau Public, using the CSVs in `data/processed/`.
An interactive HTML reference/preview of the finished dashboard (built from the
same numbers) is in `figures/dashboard_preview.html` — open it to see the target
layout before building in Tableau.

## 1. Connect data sources

Connect all of these as separate text-file connections (or a single Excel/Google
Sheet with one tab each), then relate them on `IDpol` / segment columns as noted:

| File | Use |
|---|---|
| `tableau_portfolio.csv` | Primary source — policy grain, drives live filters & drill-down |
| `kpi_portfolio_summary.csv` | Page 1 KPI cards |
| `kpi_region_summary.csv` | Page 1 & 2 region chart |
| `kpi_segment_driver_age.csv`, `kpi_segment_vehicle_age.csv`, `kpi_segment_vehicle_power.csv`, `kpi_segment_fuel_type.csv`, `kpi_segment_bonus_malus.csv` | Page 2 segment charts |
| `kpi_frequency_severity_quadrant.csv` | Page 2 scatter/quadrant |
| `pareto_claim_cost_curve.csv` | Page 3 Pareto curve |
| `extreme_claims_for_review.csv` | Page 3 large-claims table |
| `unusual_region_area_cells.csv` | Page 3 highlight table |

For the primary source (`tableau_portfolio.csv`), most dashboard charts can also
be built by aggregating this single table live in Tableau (Tableau will compute
Frequency = SUM(ClaimNb)/SUM(Exposure) on the fly for whatever filter context is
active) — this is the most flexible approach and is what the calculated fields
below assume.

## 2. Calculated fields (create these once, reuse everywhere)

```
Claim Frequency
SUM([ClaimNb]) / SUM([Exposure])

Average Claim Severity
SUM([ClaimAmount]) / SUM([ClaimAmount_count])

Total Claim Cost
SUM([ClaimAmount])

Cost per Exposure Year
SUM([ClaimAmount]) / SUM([Exposure])

Policy Count
COUNTD([IDpol])
```

Format `Claim Frequency` as a percentage; format the two cost fields as currency
(EUR, 0 decimals).

## 3. Filters / Parameters

Add these as dashboard-level filters (apply to all worksheets using the primary
source): `Region`, `DrivAgeBand`, `VehAgeBand`, `VehPowerBand`, `VehGas`,
`BonusMalusBand`. Set each as a multi-select filter card.

## 4. Page 1 — Executive Portfolio Overview

- **6 KPI cards** (text tables formatted as big numbers): Policy Count, SUM(Exposure),
  SUM(ClaimNb), Claim Frequency, Total Claim Cost, Average Claim Severity — each its
  own worksheet, placed in a horizontal container at the top.
- **Horizontal bar chart**: Region on rows (sorted descending by Total Claim Cost),
  Total Claim Cost on columns; add Claim Frequency as a second measure via a
  dual-axis or as color saturation, so both KPIs are visible at once (avoids the
  "ranked by claim count alone" trap called out in the brief).
- **Filters**: the dashboard-level filters from §3, placed on the right side.
- *What we see → why it matters → what decision it supports*: overall portfolio
  size/health at a glance; which regions carry the most cost vs. the most
  frequency; supports monthly portfolio review and regional resource allocation.

## 5. Page 2 — Claims & Risk Segments

- **Bar charts** (small multiples or a parameter-driven single chart): Claim
  Frequency and Average Claim Severity by DrivAgeBand, VehAgeBand, VehPowerBand,
  BonusMalusBand — use a parameter ("Select segment dimension") so one chart can
  switch between the four, keeping the page uncluttered.
- **Scatter plot** from `kpi_frequency_severity_quadrant.csv`: Claim Frequency on
  X, Average Claim Severity on Y, one mark per DrivAgeBand x VehPowerBand cell,
  size = ClaimCount, color = Quadrant. Add reference lines at the median X and
  median Y to visually split the four quadrants.
- **Dashboard action**: clicking a region on Page 1's bar chart filters Page 2
  (Filter Action, source = Page 1 region chart, target = all Page 2 sheets).
- *What we see → why it matters → what decision it supports*: which driver/vehicle
  segments are frequent vs. expensive, and whether the two coincide — supports
  underwriting-review targeting (Q3/Q4/Recommendation 1).

## 6. Page 3 — Claim Cost Concentration

- **Pareto / cumulative-cost line chart** from `pareto_claim_cost_curve.csv`:
  `ClaimRankShare` on X (format as %), `CumulativeCostShare` on Y (format as %).
  Add reference lines at X=0.05 and X=0.10 with annotations showing the
  corresponding Y value (52% and 60%).
- **Highlight table** from `extreme_claims_for_review.csv`: top claims by
  `ClaimAmount`, columns for Region, VehBrand, DrivAge, BonusMalus — sorted
  descending, top 20-30 rows.
- **Highlight table** from `unusual_region_area_cells.csv`: Region x Area cells
  sorted by `FreqVsPortfolio` descending.
- **Text panel**: the three Evidence → Action → KPI recommendations from
  `report/business_summary.md`.
- *What we see → why it matters → what decision it supports*: how concentrated
  claim cost is, exactly which claims/segments are driving it, and the concrete
  actions management should take — supports claims-handling resourcing
  (Recommendation 2) and closes the dashboard with clear next steps.

## 7. Publishing

Save as `insurance_claims_dashboard.twb` (or `.twbx` to package the data files
together), or publish to Tableau Public and link the URL in the README.
