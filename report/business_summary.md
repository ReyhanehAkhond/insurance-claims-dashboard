# Business Summary — Insurance Claims & Portfolio Risk

All numbers below come from the real, full freMTPL2 dataset (677,991 policies,
26,444 claims), computed in `notebooks/insurance_analysis.ipynb`. No Loss Ratio
is used anywhere — freMTPL2 has no premium field.

---

## Q1 — Overall portfolio health

| KPI | Value |
|---|---|
| Policy Count | 677,991 |
| Total Exposure | 358,343 policy-years |
| Claim Count | 26,405 |
| **Claim Frequency** | **7.37 claims per 100 policy-years** |
| Total Claim Cost | **€59.9M** |
| **Average Claim Severity** | **€2,266 per claim** |

**Why raw claim counts alone are misleading:** the portfolio has 677,991 policies
but only 358,343 policy-years of actual observation (the average policy was only
observed for ~0.53 of a year), and policies with more exposure naturally
accumulate more claims. A region or segment with more claims is not necessarily
riskier — it may simply have more policies, or longer-observed policies. Claim
Frequency (claims ÷ exposure) is the KPI that removes this size effect and lets
management compare segments on a like-for-like basis.

---

## Q2 — Which regions generate the greatest claim burden?

Ranking by raw claim count would simply reward big regions. Instead:

| Region | Policies | Exposure | Frequency | Total Cost | Cost / Exposure-yr |
|---|---|---|---|---|---|
| Centre | 160,595 | 102,701 | 6.3% | €19.07M (31.8% of total) | €185.7 |
| Rhône-Alpes | 84,748 | 45,329 | **9.3%** (highest) | €10.28M (2nd highest) | **€226.8** (highest of the big regions) |
| PACA | 79,315 | 35,749 | 8.3% | €6.87M | €192.2 |
| Île-de-France | 69,789 | 30,197 | 8.6% | €4.56M | €151.1 |

**Region that deserves attention: Rhône-Alpes.** Centre has the largest *absolute*
cost simply because it is by far the largest region (30% of the whole portfolio's
exposure) — its frequency (6.3%) is actually below the portfolio average.
Rhône-Alpes, by contrast, is flagged by **two independent KPIs at once**: it has
the **highest claim frequency of any major region (9.3% vs. 7.4% portfolio
average)** and the **highest cost per exposure-year among large regions
(€226.8 vs. €167.2 portfolio average, ~36% above average)** — i.e. it is not just
big, it is genuinely generating more claims and more cost per policy-year than
its size alone would predict.

---

## Q3 — Driver and vehicle segment patterns

**Driver age — the strongest and clearest pattern in the whole dataset:**

| Age band | Frequency | Avg. Severity |
|---|---|---|
| **18–25** | **14.8%** (2x portfolio avg.) | **€5,122** (2.3x portfolio avg.) |
| 26–35 | 7.5% | €2,053 |
| 36–45 | 7.2% | €1,919 |
| 46–55 | 7.4% | €1,861 |
| 56–65 | 6.4% | €1,890 |
| 66–75 | 5.8% | €2,319 |
| 76+ | 6.3% | €2,559 |

Drivers aged 18–25 claim about twice as often **and** their claims cost more than
twice as much on average as the rest of the portfolio — this is the single
strongest pattern in the data (association, not a causal claim).

**Bonus-malus — a clean, monotonic frequency escalation:**
Frequency rises from **5.1%** at the base/no-claims level (score 50) to **10.5%**
(51–100), **34.6%** (101–150) and **56.8%** (151+). This is expected by design
(bonus-malus already reflects past claims history) but confirms the score is a
strong, consistent frequency signal in this data.

**Vehicle age:** frequency is fairly flat (5.5%–8.1%) across bands, but the
**11–15 year** band has the highest average severity (€3,135) — older-but-not-oldest
vehicles produce fewer but pricier claims.

**Vehicle power / fuel type:** high-power vehicles (10+) claim slightly more often
(8.1% vs. 7.3% for low-power) but not dramatically so; Diesel vehicles claim
somewhat more often (7.9% vs. 6.9%) while Regular-fuel claims run more expensive
on average (€2,487 vs. €2,052) — frequency and severity move in different
directions here, which is exactly why they must be looked at separately.

---

## Q4 — Frequency vs. severity: same segments, or different ones?

Cross-tabulating driver-age x vehicle-power (cells with fewer than 20 claims
dropped as too small to trust) shows all four quadrants are populated:

- **High frequency / High severity** (worst combination): young drivers (18–25)
  with mid-power vehicles — frequency 17.0% **and** severity €8,798, by far the
  most expensive cell in the whole grid.
- **High frequency / Low severity**: e.g. 26–35 with mid-power vehicles — claims
  often, but cheaply.
- **Low frequency / High severity**: e.g. 66–75 with any vehicle power — claims
  rarely, but each claim tends to be expensive.
- **Low frequency / Low severity**: the largest, calmest group — e.g. 46–55 with
  mid-power vehicles.

**Conclusion: frequent-claim segments are not automatically the expensive-claim
segments** — except for young drivers, where the two effects stack and compound
each other, which is exactly why that segment stood out so clearly in Q3.

---

## Q5 — Is claim cost concentrated in a few claims?

Pareto analysis on all 26,444 individual claims:

| Top X% of claims (by size) | Share of total claim cost |
|---|---|
| Top 1% | **38.0%** |
| Top 5% | **52.1%** |
| Top 10% | **59.9%** |
| Top 20% | **68.8%** |

Claim cost is **heavily concentrated**: barely 5% of claims already account for
more than half of all claim spending, and a single claim (€4.08M) alone represents
6.8% of total cost. **This matters for claims management** because it means
resources are best spent on early identification and active handling of a small
number of large/complex claims — a handful of well-managed large claims moves the
portfolio's cost far more than optimizing the handling of thousands of small ones.

---

## Q6 — Unusual claims and segments to investigate

**Individual claims:** a statistical rule (3x-IQR on log-claim-cost, chosen
because claim costs are heavily right-skewed) flags **878 claims (3.3% of all
claims)** representing **€28.7M — 48% of total claim cost**. These are **not
deleted**; the full list is in `data/processed/extreme_claims_for_review.csv` for
claims-handling review. The single largest is a **€4.08M** claim in the Centre
region (driver age 19, vehicle only 13 years old) — this kind of claim warrants
individual case review (potential large bodily-injury claim, data-entry error, or
genuinely catastrophic loss) rather than being folded into "average" severity.

**Segment combinations:** several thin Region x Area cells show frequency far
above the portfolio average even after requiring meaningful exposure (≥50
policy-years) — e.g. Picardie/Area-E (1.49x average), Rhône-Alpes/Area-E (1.47x),
Centre/Area-E (1.43x), Rhône-Alpes/Area-D (1.40x). Interestingly it is the
**second-most-urban** density band (E), not the most urban (F), that repeats
across several regions — worth a underwriting/claims review rather than assuming
"urban = risky" at face value, since these are relatively small cells and could
partly reflect sample noise.

---

## Q7 — What should management monitor monthly?

**Executive dashboard KPI set** (Page 1): Policy Count, Total Exposure, Claim
Count, **Claim Frequency**, Total Claim Cost, **Average Claim Severity** — the six
core, exposure-aware KPIs, each supporting a different management question
(portfolio size, claim volume normalized for exposure, and cost intensity).

**Why each belongs on the dashboard:**
- *Claim Frequency* — the primary early-warning KPI; a frequency uptick is the
  first sign of a deteriorating segment, well before it shows up in total cost.
- *Average Claim Severity* — tracks whether claims are becoming more expensive
  independent of how often they occur (separates "more claims" from "worse
  claims").
- *Total Claim Cost by region/segment* — the budgeting/reserving view.
- *Pareto / large-claims view* — supports claims-management resource allocation
  (Q5/Q6): monitoring the largest few claims each month has outsized impact.
- *Region and driver-age breakdowns with filters* — let management drill from the
  headline number into "which region/segment is driving this" without waiting for
  a new report.

---

## Q8 — Three data-driven recommendations

**1.**
**Evidence:** Drivers aged 18–25 have roughly double the claim frequency (14.8%
vs. 7.4% portfolio average) *and* more than double the average severity (€5,122
vs. €2,266) of the rest of the portfolio — the single strongest pattern in the
data, and the segment sits in the worst quadrant of the Q4 analysis when combined
with mid-power vehicles.
**Action:** Route this segment for dedicated underwriting review (e.g. targeted
telematics/black-box monitoring, or adjusted terms at renewal) rather than
treating it as an average-risk segment; combine with vehicle-power restrictions
for the highest-risk sub-segment.
**KPI to track:** Claim Frequency and Average Claim Severity for the 18–25
driver-age band, monitored monthly against the portfolio baseline.

**2.**
**Evidence:** Just 5% of individual claims generate 52% of total claim cost, and
878 statistically extreme claims (3.3% of claims) already account for 48% of all
claim spending.
**Action:** Establish a formal large-claims early-warning process — any claim
exceeding a defined threshold (e.g. €20,000, which currently covers 215 claims) is
escalated to senior claims handlers within days of being reported, rather than
processed through the standard queue.
**KPI to track:** Number and cumulative cost of claims above the large-claim
threshold, reviewed monthly (the Pareto/cumulative-cost view on the dashboard).

**3.**
**Evidence:** Rhône-Alpes combines the highest claim frequency among large regions
(9.3%) with the highest cost per exposure-year (€226.8, ~36% above the portfolio
average) — a pattern that raw claim-count ranking would have completely missed
(Centre has more total claims but a below-average frequency).
**Action:** Give Rhône-Alpes a dedicated regional review (claims patterns,
distribution/agent mix, local risk factors) rather than assuming its high total
cost is simply a function of its size.
**KPI to track:** Claim Frequency and Cost-per-Exposure-Year by region, tracked
monthly on the Page-1 region comparison chart, with Rhône-Alpes flagged as a
watch-list region.

---

*Limitations: the insurer is anonymous, data is historical (2011–2013), no
premium/profitability view is possible, and every pattern described here is an
association in the data, not a proven causal effect.*
