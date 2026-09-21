import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))

def code(text):
    cells.append(nbf.v4.new_code_cell(text))

# =====================================================================
md("""# Insurance Claims & Portfolio Risk Dashboard
### Python analysis notebook — freMTPL2 (French Motor Third-Party Liability)

**Business scenario.** We are analysts on a motor-insurer's analytics team. Management wants
a clear, descriptive (not pricing/underwriting) view of the portfolio: where claims happen,
where they cost the most, which segments deserve attention, and what to monitor going forward.

**Data.** Public `freMTPL2freq` / `freMTPL2sev` datasets from the CASdatasets R package
(Dutang & Charpentier), downloaded directly from the official GitHub mirror of the package
(`github.com/dutangc/CASdatasets`) and converted from `.rda` to CSV. This is the **real, full
dataset**: 677,991 policies and 26,444 individual claims — no sampling, no synthetic data.

Official docs: https://dutangc.github.io/CASdatasets/reference/freMTPL.html

**Important constraint.** freMTPL2 does **not** include written premium, so **Loss Ratio is
never calculated** in this notebook. The core KPIs are claim frequency, claim severity and
total claim cost, as required by the brief.
""")

# =====================================================================
md("## Step 0 — Imports & setup")
code("""import pandas as pd
import numpy as np

pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 160)

RAW_DIR = "../data/raw"
OUT_DIR = "../data/processed"
""")

# =====================================================================
md("""## Step 1 — Load the two raw tables

`freq` has **one row per policy** (risk features + claim count + exposure).
`sev` has **one row per individual claim**, linked back to a policy through `IDpol`.
A policy can appear zero, one, or several times in `sev` depending on how many claims it had.""")
code("""freq = pd.read_csv(f"{RAW_DIR}/freMTPL2freq_raw.csv")
sev = pd.read_csv(f"{RAW_DIR}/freMTPL2sev_raw.csv")

print(f"Frequency table : {freq.shape[0]:,} policies, {freq.shape[1]} columns")
print(f"Severity table  : {sev.shape[0]:,} individual claims, {sev.shape[1]} columns")
freq.head()
""")
code("""sev.head()""")

# =====================================================================
md("""## Step 2 — Data quality checks

Before touching a single number we check: missing values, duplicate policies, and whether the
two tables agree with each other (every `ClaimNb > 0` should have exactly that many rows in
`sev`, and every claim in `sev` should belong to a real policy).""")
code("""print("Missing values in freq:", freq.isna().sum().sum())
print("Missing values in sev :", sev.isna().sum().sum())
print("Duplicate policy IDs  :", freq["IDpol"].duplicated().sum())

sev_claim_counts = sev.groupby("IDpol").size().rename("sev_claim_count")
consistency = (
    freq.set_index("IDpol")[["ClaimNb"]]
    .join(sev_claim_counts, how="left")
    .fillna(0)
)
mismatches = (consistency["ClaimNb"] != consistency["sev_claim_count"]).sum()
print(f"Policies where ClaimNb disagrees with the severity-table row count: {mismatches}")
""")

md("""### 2.1 Known, documented data-entry issues

freMTPL2 is a widely studied public dataset, and two data-entry artefacts are well documented
in the actuarial literature (e.g. Wüthrich's case studies using this same data):

1. **`Exposure` should never exceed 1.0** — it is a fraction of the one-year observation
   window. A small number of rows (1,224) go up to ~2.01. We **cap** `Exposure` at 1.0.
2. **A handful of policies (5) report implausible claim counts** (8–16 claims within well
   under a year of exposure), all sharing the same region/density cell — a clear encoding
   artefact rather than genuine behaviour. We **cap** `ClaimNb` at 4 (a threshold also used in
   published work on this dataset).

Both are **corrections of extreme/implausible values, not deletion of rows** — in line with the
brief's instruction not to silently delete outliers.""")
code("""n_exposure_capped = (freq["Exposure"] > 1).sum()
n_claimnb_capped = (freq["ClaimNb"] > 4).sum()
print(f"Rows with Exposure > 1 (capped to 1.0): {n_exposure_capped}")
print(f"Rows with ClaimNb  > 4 (capped to 4)  : {n_claimnb_capped}")

freq["Exposure"] = freq["Exposure"].clip(upper=1.0)
freq["ClaimNb"] = freq["ClaimNb"].clip(upper=4)
""")

md("""### 2.2 VehAge placeholder codes

`VehAge` contains 48 rows with values 99 or 100 — almost certainly an "unknown" placeholder
code, not a 99-year-old car. We keep these rows and simply let the vehicle-age bucketing below
fold them into the open-ended "16+ years" segment, where they belong regardless of the exact
code.""")

# =====================================================================
md("""## Step 3 — Aggregate claim cost per policy, then merge

**This is the documented merge logic required by the brief.** A policy can have several
claims, so we first aggregate `sev` to one row per `IDpol` (sum of claim amounts, and a count
of how many claim records exist), and only then left-merge onto `freq`. This guarantees the
final table has exactly one row per policy — the correct grain for portfolio KPIs — while
still preserving every euro of claim cost.""")
code("""policy_claim_cost = (
    sev.groupby("IDpol", as_index=False)
    .agg(ClaimAmount_sum=("ClaimAmount", "sum"),
         ClaimAmount_count=("ClaimAmount", "count"))
)

df = freq.merge(policy_claim_cost, on="IDpol", how="left")
df["ClaimAmount_sum"] = df["ClaimAmount_sum"].fillna(0.0)
df["ClaimAmount_count"] = df["ClaimAmount_count"].fillna(0).astype(int)

# Sanity check: no cost lost or duplicated in the merge
assert np.isclose(df["ClaimAmount_sum"].sum(), sev["ClaimAmount"].sum())
print(f"Policy-level table after merge: {df.shape[0]:,} rows (1 row per policy)")
df.head()
""")

# =====================================================================
md("""## Step 4 — Build business segments

We turn continuous risk features into readable bands for segment comparison and for Tableau
filters. Bin edges are chosen to be business-sensible (e.g. legal driving age starts at 18,
new-vehicle vs. old-vehicle cutoffs, the bonus-malus "50" baseline for a claim-free driver in
the French system) rather than purely statistical quantiles.""")
code("""df["DrivAgeBand"] = pd.cut(
    df["DrivAge"], bins=[17, 25, 35, 45, 55, 65, 75, 101],
    labels=["18-25", "26-35", "36-45", "46-55", "56-65", "66-75", "76+"],
)
df["VehAgeBand"] = pd.cut(
    df["VehAge"], bins=[-1, 1, 5, 10, 15, 200],
    labels=["0-1", "2-5", "6-10", "11-15", "16+"],
)
df["VehPowerBand"] = pd.cut(
    df["VehPower"], bins=[0, 6, 9, 20],
    labels=["Low (<=6)", "Mid (7-9)", "High (10+)"],
)
df["BonusMalusBand"] = pd.cut(
    df["BonusMalus"], bins=[0, 50, 100, 150, 300],
    labels=["50 (base/no-claims)", "51-100", "101-150", "151+"],
)
df[["DrivAgeBand", "VehAgeBand", "VehPowerBand", "BonusMalusBand"]].describe()
""")

# =====================================================================
md("""## Step 5 — Core KPI function

One function, used everywhere below, so every table in this notebook (and every chart in
Tableau) uses **exactly the same KPI definitions** — no silent inconsistency between the
portfolio summary and the segment tables.

- **Claim Frequency = Claim Count / Exposure** (claims per policy-year — this is what makes
  segments with different amounts of exposure comparable).
- **Average Claim Severity = Total Claim Cost / number of claim records** (average cost
  *per claim*, not per policy).""")
code("""def kpi_table(frame: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    grouped = frame if group_cols is None else frame.groupby(group_cols, observed=True)

    def _agg(g):
        policy_count = len(g)
        exposure = g["Exposure"].sum()
        claim_count = g["ClaimNb"].sum()
        total_cost = g["ClaimAmount_sum"].sum()
        frequency = claim_count / exposure if exposure > 0 else np.nan
        n_claim_records = g["ClaimAmount_count"].sum()
        severity = total_cost / n_claim_records if n_claim_records > 0 else np.nan
        return pd.Series({
            "PolicyCount": policy_count, "Exposure": exposure, "ClaimCount": claim_count,
            "ClaimFrequency": frequency, "TotalClaimCost": total_cost,
            "AvgClaimSeverity": severity,
        })

    if group_cols is None:
        return _agg(frame).to_frame().T
    return grouped.apply(_agg, include_groups=False).reset_index()
""")

# =====================================================================
md("""## Q1 — What is the overall health of the insurance portfolio?

Raw claim counts alone are misleading because portfolios differ in size and in how long each
policy was observed (`Exposure`). Two portfolios with the same number of claims can have very
different underlying risk if one has twice the exposure. **Claim Frequency** (claims per
policy-year) fixes this by normalizing for exposure, which is why it — not the raw claim count
— is the headline risk KPI.""")
code("""q1_portfolio = kpi_table(df)
q1_portfolio.round(2)
""")

# =====================================================================
md("""## Q2 — Which regions generate the greatest claim burden?

We deliberately do **not** rank regions by raw claim count. A large region simply has more
policies, so of course it has more claims — that says nothing about risk. Instead we compare
**exposure, claim frequency, total claim cost and average severity together**.""")
code("""q2_region = kpi_table(df, "Region").sort_values("TotalClaimCost", ascending=False)
q2_region["CostPerPolicy"] = q2_region["TotalClaimCost"] / q2_region["PolicyCount"]
q2_region["CostPerExposureYear"] = q2_region["TotalClaimCost"] / q2_region["Exposure"]
q2_region.round(2)
""")

# =====================================================================
md("""## Q3 — Which driver and vehicle segments show different claim patterns?

We compare frequency and severity across driver-age band, vehicle-age band, vehicle-power
band, fuel type and bonus-malus band. Patterns are described, **not** interpreted causally —
these are portfolio associations, not proof that (say) being young *causes* more claims.""")
code("""q3_drivage = kpi_table(df, "DrivAgeBand")
q3_vehage = kpi_table(df, "VehAgeBand")
q3_vehpower = kpi_table(df, "VehPowerBand")
q3_vehgas = kpi_table(df, "VehGas")
q3_bonusmalus = kpi_table(df, "BonusMalusBand")
q3_drivage.round(3)
""")
code("""q3_vehage.round(3)""")
code("""q3_vehpower.round(3)""")
code("""q3_vehgas.round(3)""")
code("""q3_bonusmalus.round(3)""")

# =====================================================================
md("""## Q4 — Are frequent-claim segments also expensive-claim segments?

We build a driver-age x vehicle-power grid (dropping tiny cells with under 20 claims, which
would be too noisy to trust) and classify each cell into a frequency/severity quadrant relative
to the median of the grid. This distinguishes "claims often but cheaply" segments from
"claims rarely but expensively" segments — a distinction a single KPI can never show.""")
code("""q4_quadrant = kpi_table(df, ["DrivAgeBand", "VehPowerBand"])
q4_quadrant = q4_quadrant[q4_quadrant["ClaimCount"] >= 20]

freq_median = q4_quadrant["ClaimFrequency"].median()
sev_median = q4_quadrant["AvgClaimSeverity"].median()
q4_quadrant["FrequencyLevel"] = np.where(q4_quadrant["ClaimFrequency"] >= freq_median, "High", "Low")
q4_quadrant["SeverityLevel"] = np.where(q4_quadrant["AvgClaimSeverity"] >= sev_median, "High", "Low")
q4_quadrant["Quadrant"] = q4_quadrant["FrequencyLevel"] + " Frequency / " + q4_quadrant["SeverityLevel"] + " Severity"
q4_quadrant.round(3)
""")
code("""q4_quadrant["Quadrant"].value_counts()""")

# =====================================================================
md("""## Q5 — Is claim cost concentrated in a small number of claims?

A Pareto-style analysis on the raw, claim-level severity table (every one of the 26,444
individual claims, ranked by size).""")
code("""pareto = sev.sort_values("ClaimAmount", ascending=False).reset_index(drop=True)
pareto["ClaimRank"] = pareto.index + 1
pareto["CumulativeCost"] = pareto["ClaimAmount"].cumsum()
total_cost_all_claims = pareto["ClaimAmount"].sum()
pareto["CumulativeCostShare"] = pareto["CumulativeCost"] / total_cost_all_claims
pareto["ClaimRankShare"] = pareto["ClaimRank"] / len(pareto)

def share_of_cost_from_top_n_pct(pct):
    n = int(len(pareto) * pct)
    return pareto.iloc[:n]["ClaimAmount"].sum() / total_cost_all_claims

for pct in [0.01, 0.05, 0.10, 0.20]:
    print(f"Top {pct:>4.0%} of claims by size generate {share_of_cost_from_top_n_pct(pct):.1%} of total claim cost")
""")
code("""# Downsample to ~200 points so the Tableau file stays light without losing the curve's shape
step = max(1, len(pareto) // 200)
pareto_curve = pareto.iloc[::step][
    ["ClaimRank", "ClaimRankShare", "ClaimAmount", "CumulativeCost", "CumulativeCostShare"]
].copy()
pareto_curve.head()
""")
md("""This concentration matters for **claims management**: a small team focused on reviewing and
actively managing the largest ~5–10% of claims can influence the majority of total claim cost —
far more leverage than spreading effort evenly across all claims.""")

# =====================================================================
md("""## Q6 — What unusual claims or segments should management investigate?

**We never auto-delete large claims.** Instead we flag them for human review using an IQR rule
on log-cost (claim costs are heavily right-skewed, so raw-scale IQR would be meaningless), and
separately look for thin Region x Area cells with frequency far above the portfolio average.""")
code("""log_cost = np.log1p(sev["ClaimAmount"])
q1_, q3_ = log_cost.quantile([0.25, 0.75])
iqr = q3_ - q1_
upper_fence = q3_ + 3 * iqr
extreme_mask = log_cost > upper_fence

extreme_claims = sev.loc[extreme_mask].merge(
    df[["IDpol", "Region", "VehBrand", "VehPower", "VehAge", "DrivAge", "BonusMalus", "Area", "VehGas"]],
    on="IDpol", how="left",
).sort_values("ClaimAmount", ascending=False)

print(f"Claims flagged for review by the statistical rule: {len(extreme_claims)} "
      f"({len(extreme_claims)/len(sev):.1%} of all claims, "
      f"{extreme_claims['ClaimAmount'].sum()/sev['ClaimAmount'].sum():.1%} of total cost)")
extreme_claims.head(15)
""")
code("""region_area_cells = kpi_table(df, ["Region", "Area"])
region_area_cells = region_area_cells[region_area_cells["Exposure"] >= 50]
portfolio_freq = q1_portfolio["ClaimFrequency"].iloc[0]
region_area_cells["FreqVsPortfolio"] = region_area_cells["ClaimFrequency"] / portfolio_freq
unusual_cells = region_area_cells.sort_values("FreqVsPortfolio", ascending=False).head(10)
unusual_cells.round(3)
""")

# =====================================================================
md("""## Q7 & Q8 — Dashboard KPIs and recommendations

Answered in full in `report/business_summary.md` and in the Tableau build guide
(`tableau/dashboard_build_guide.md`), using the tables produced below.""")

# =====================================================================
md("""## Step 6 — Export clean, Tableau-ready tables

Everything above is exported as flat CSV files under `data/processed/`. The main file
(`tableau_portfolio.csv`) is policy-level (1 row per policy) so Tableau can filter, drill down
and re-aggregate live; the KPI tables are pre-aggregated for fast-loading dashboard cards.""")
code("""tableau_main_cols = [
    "IDpol", "Region", "Area", "Density", "VehBrand", "VehGas",
    "VehPower", "VehPowerBand", "VehAge", "VehAgeBand",
    "DrivAge", "DrivAgeBand", "BonusMalus", "BonusMalusBand",
    "Exposure", "ClaimNb", "ClaimAmount_sum", "ClaimAmount_count",
]
df[tableau_main_cols].rename(columns={"ClaimAmount_sum": "ClaimAmount"}).to_csv(
    f"{OUT_DIR}/tableau_portfolio.csv", index=False)

q1_portfolio.to_csv(f"{OUT_DIR}/kpi_portfolio_summary.csv", index=False)
q2_region.to_csv(f"{OUT_DIR}/kpi_region_summary.csv", index=False)
q3_drivage.to_csv(f"{OUT_DIR}/kpi_segment_driver_age.csv", index=False)
q3_vehage.to_csv(f"{OUT_DIR}/kpi_segment_vehicle_age.csv", index=False)
q3_vehpower.to_csv(f"{OUT_DIR}/kpi_segment_vehicle_power.csv", index=False)
q3_vehgas.to_csv(f"{OUT_DIR}/kpi_segment_fuel_type.csv", index=False)
q3_bonusmalus.to_csv(f"{OUT_DIR}/kpi_segment_bonus_malus.csv", index=False)
q4_quadrant.to_csv(f"{OUT_DIR}/kpi_frequency_severity_quadrant.csv", index=False)
pareto_curve.to_csv(f"{OUT_DIR}/pareto_claim_cost_curve.csv", index=False)
extreme_claims.to_csv(f"{OUT_DIR}/extreme_claims_for_review.csv", index=False)
unusual_cells.to_csv(f"{OUT_DIR}/unusual_region_area_cells.csv", index=False)

print("All Tableau-ready CSV files written to data/processed/")
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

with open("notebooks/insurance_analysis.ipynb", "w") as f:
    nbf.write(nb, f)

print("Notebook written.")
