# Motor Insurance Claims & Portfolio Risk Analysis (Python + Tableau)

## Overview
This project explores third-party liability motor insurance claims using the well-known French **freMTPL2** dataset[cite: 14]. The goal was to step into the shoes of an insurance analytics team and answer practical portfolio questions:
* Which driver and vehicle segments generate the most frequent or costly claims[cite: 14]?
* How heavily are total losses concentrated among a small fraction of policies[cite: 14]?
* Where should underwriting and claims teams direct their attention to reduce overall risk[cite: 14]?

> **Methodology Note:** Since freMTPL2 does not contain premium data, **Loss Ratio is deliberately not calculated**[cite: 14]. The analysis evaluates risk objectively by pairing claim frequency and claim severity with policy exposure[cite: 14].

---

## Interactive Tableau Dashboards

### 1. Executive Portfolio Overview
A high-level view of core portfolio health, tracking overall exposure, claim volumes, and regional distributions with live interactive filters[cite: 14].

![Page 1 Overview](figures/page1_overview.png)[cite: 14]

---

### 2. Risk Segmentation & Quadrant Analysis
Deep dive into driver demographics, vehicle power bands, and bonus-malus ratings[cite: 14]. Includes a four-quadrant scatter matrix separating high-frequency risks from severe single-event losses[cite: 14, 18].

![Page 2 Segments](figures/page2_segments.png)[cite: 14]

---

### 3. Claim Cost Concentration & Extreme Losses
Pareto distribution analysis highlighting loss concentration, alongside a review table of catastrophic individual claims and strategic recommendations[cite: 14, 18].

![Page 3 Concentration](figures/page3_concentration.png)[cite: 14]

---

## Key Business Insights

* **Young Drivers Carry Compounded Risk:** Drivers aged 18–25 show both double the portfolio claim frequency (~14.8% vs. 7.4%) and more than double the average claim severity (~€5,122 vs. €2,266)[cite: 17]. They are the single highest-risk cohort in the portfolio[cite: 17].
* **Extreme Pareto Concentration:** Barely **5% of claims drive over 52% of total portfolio costs**, and the top 1% accounts for 38%[cite: 14, 17]. Active early intervention on large claims yields far greater financial leverage than general processing improvements[cite: 17].
* **Regional Risk vs. Portfolio Size:** While the **Centre** region accounts for the largest absolute payout due to pure policy volume, **Rhône-Alpes** shows genuine risk escalation with both the highest frequency (9.3%) and the highest cost per exposure-year (~€226.8 vs. €167.2 baseline)[cite: 17].
* **Bonus-Malus Validity:** Claims history reliably scales with risk; frequency rises sharply from 5.1% in the claim-free tier (score 50) to 34.6% (score 101–150) and 56.8% for scores above 150[cite: 17].

---

## Data Pipeline & Integrity Rules

The raw dataset contains **677,991 policy records** and **26,444 individual claims** from the CASdatasets library (Dutang & Charpentier)[cite: 14]. The data pipeline was designed to handle real-world actuarial quirks without silently discarding records[cite: 14]:

1. **Policy-Level Granularity:** `freMTPL2sev` claims were aggregated by `IDpol` first (total cost + claim count) and then left-joined with `freMTPL2freq`[cite: 14]. This keeps exactly one row per policy while conserving 100% of the claim amounts (verified by parity checks)[cite: 14, 18].
2. **Exposure Capping:** Exposure was capped at 1.0 year to correct entry anomalies exceeding the annual window[cite: 14].
3. **Claim Count Normalization:** Implausibly high counts (e.g., 8–16 claims in fractional policy years within a single reporting cell) were capped at 4 rather than dropped, preserving policy exposure while dampening data-entry artifacts[cite: 14, 18].
4. **Outlier Flagging Over Deletion:** Catastrophic losses (such as a €4.08M bodily-injury claim) were retained in the portfolio KPIs and isolated via an IQR threshold on log-cost for explicit executive review[cite: 17, 18].

---

## Core Metrics Defined

* **Exposure:** Observed duration of a policy in fractional years[cite: 14].
* **Claim Frequency:** $\frac{\text{Total Claim Count}}{\text{Total Exposure}}$ (Claims per policy-year; allows fair comparison across groups of different sizes)[cite: 14, 18].
* **Average Claim Severity:** $\frac{\text{Total Claim Amount}}{\text{Total Claim Records}}$ (Average cost per incident, not per policy)[cite: 14, 18].
* **Total Claim Cost:** Cumulative gross incurred losses across the portfolio[cite: 14, 18].

---

## Project Structure

```text
├── README.md
├── requirements.txt
├── notebooks/
│   ├── insurance_analysis.ipynb          # End-to-end executed workflow
│   └── insurance_analysis_pipeline.py    # Production-ready Python script
├── tableau/
│   └── insurance_claims_dashboard.twbx   # Full interactive Tableau workbook
├── figures/
│   ├── page1_overview.png
│   ├── page2_segments.png
│   └── page3_concentration.png
├── report/
│   └── business_summary.md               # Detailed management memo & recommendations
└── data/
    ├── raw/                              # Original frequency and severity tables
    └── processed/                        # Processed CSVs feeding the dashboards
```[cite: 14]

---

## Running Locally

To reproduce the data transformations and extract files:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the analysis notebook
jupyter nbconvert --to notebook --execute --inplace notebooks/insurance_analysis.ipynb
```[cite: 14]

You can open `tableau/insurance_claims_dashboard.twbx` directly in **Tableau Desktop** or **Tableau Public** to explore the interactive filters and parameters[cite: 14].