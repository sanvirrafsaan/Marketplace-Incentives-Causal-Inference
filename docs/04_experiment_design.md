# Prospective Experiment Design — Regional Surge Incentives

**Status:** Week 4 complete (quasi-experiment done; this doc describes a **proposed** randomized rollout — not something run on Olist).

---

## 1. Context

We used the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) dataset to **simulate** a regional surge-incentive rollout: treated states (SP, RJ, MG) from 2017-06-01 onward vs all other Brazilian states as control. Outcome: **on-time delivery rate** among delivered orders only.

**Quasi-experimental finding (Week 3, locked):**

| Result | Value |
|--------|-------|
| DiD estimate (τ̂) | **+1.34 pp** (hand calculation and OLS `treated × post` agree) |
| Bootstrap 95% CI | **[0.40, 2.17] pp** (order-level resampling, N = 1,000) |
| Substantive read | Both arms' on-time rates **fell** post-cutoff; treated states saw a **smaller decline** (~−2.7 pp vs ~−4.0 pp control) |

The CI excludes zero, so the associational effect is statistically distinguishable from no difference — but the magnitude is modest and the design is **observational**.

**What the quasi-experiment cannot prove:**

- **Causality** — treatment was not randomized; hub states (SP/RJ/MG) differ from control states in infrastructure and volume.
- **Parallel trends** — partially plausible at best; a synchronized late-2017 drop in both arms suggests a common platform shock.
- **Absolute improvement** — treated on-time rate still **declined** post-cutoff; DiD captures a *relative* difference, not proof that incentives raised on-time in levels.

**Why a prospective experiment:** DiD gives a signal worth testing (~1.3 pp under stated assumptions). A **cluster-randomized** A/B rollout would validate whether regional incentives **cause** improved on-time performance — without relying on untestable parallel trends.

---

## 2. Hypothesis

**Primary (pre-registered):** Regional surge incentives increase on-time delivery rate by **≥ 2 percentage points (absolute)** in treated state-weeks compared to control state-weeks, among delivered orders.

**Rationale for 2 pp (not 1.34 pp):** The DiD point estimate (~1.3 pp) is observational evidence, not a launch threshold. We power for **2 pp** because (a) the bootstrap lower bound (0.4 pp) allows a smaller true effect, (b) ops cost and complexity require a **minimum business-meaningful lift**, and (c) MDE is the smallest effect we want to **reliably detect**, not our best guess of the truth.

**Null:** No difference in on-time rate between treated and control state-weeks (two-sided α = 0.05).

---

## 3. Unit of randomization

**Unit:** **state-week** — one `customer_state` × one calendar week.

**Randomization:** Each state-week is assigned to treatment (incentive active) or control (no incentive) with probability 0.5. Optional: stratify by baseline weekly order volume (high / medium / low) so arms are balanced on throughput.

**Why not order-level?**

- **Interference (SUTVA):** Orders in the same state-week share sellers, freight routes, and regional fulfillment capacity. Randomizing individual orders within the same geography would violate independence — treated and control orders would compete for the same logistics network.
- **Operational reality:** Surge incentives are deployed **regionally over time**, not toggled per checkout. The policy lever matches cluster randomization.

**Why not seller-level?**

- Sellers ship across multiple states; a seller-level assignment would **leak** treatment into control geographies and contaminate both arms.

**Why not driver-level?**

- Not applicable to Olist (e-commerce marketplace, not ride-hail). Included for completeness: even in ride-hail, drivers cross zone boundaries, causing spillover.

---

## 4. Metrics

### North star (primary)

| Metric | Definition | Aggregation |
|--------|------------|-------------|
| **On-time delivery rate** | `1` if `delivered_customer_date ≤ estimated_delivery_date`, else `0` | Mean among **delivered** orders per state-week; compare treated vs control clusters |

Same outcome as Week 3 DiD — keeps the experiment aligned with the quasi-experimental evidence.

### Guardrails (secondary — do not harm)

| Metric | Definition | Why it matters |
|--------|------------|----------------|
| **Incentive cost per order** | Total surge spend ÷ delivered orders in treated state-weeks | Ops need ROI; a 2 pp on-time lift is not worth unbounded cost |
| **Review score** | Mean `review_score` (1–5) per state-week | Faster delivery should not tank satisfaction (rushed handling, damaged goods) |
| **Cancellation / non-delivery rate** | Share of orders not delivered | Incentives might push acceptance of bad routes |
| **Gaming proxy: estimated-date drift** | Week-over-week change in mean `(estimated_delivery_date − purchase_date)` in treated clusters | Sellers/carriers might inflate estimated dates to make on-time easier without improving real speed |

### Analysis plan

- **Primary test:** Difference in on-time rate between treated and control state-weeks (cluster-robust SE or mixed model with state-week random effect).
- **Guardrails:** Pre-specify thresholds (e.g. cost/order ≤ $X, review_score drop ≤ 0.1 stars). Breach → pause or stop experiment regardless of on-time lift.

---

## 5. Duration & sample size (power analysis)

Computed by [`scripts/power_analysis.py`](../scripts/power_analysis.py) (rerunnable).

### Assumptions

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Baseline (p₀) | **0.911** | Week 3 control post on-time rate (delivered orders) |
| MDE (absolute) | **0.02** (2 pp) | Above DiD ~1.3 pp; minimum business-meaningful lift |
| Target treated rate (p₁) | **0.931** | p₀ + MDE |
| α (two-sided) | **0.05** | Standard false-positive rate |
| Power (1 − β) | **0.80** | Standard |
| Allocation | **1:1** treated : control | Equal cluster split |
| Cluster unit | **state-week** | §3 |
| Avg orders per cluster (m) | **44.8** | Notebook 03 feasibility Query B |
| ICC (assumed) | **0.01** | Conservative; orders within state-week correlated |
| Design effect (DEFF) | **1.44** | `1 + (m − 1) × ICC` |

### Power analysis output

```
============================================================
POWER ANALYSIS — Regional surge incentive experiment
============================================================
Baseline (control) on-time:      91.1%
MDE (absolute):                  91.1% → 93.1% (+2.0%)
α (two-sided):                   0.05
Power (1 - β):                   0.8
Cohen's h:                       0.0743
Avg orders per cluster (m):      44.8
ICC (assumed):                   0.01
Design effect (DEFF):            1.44
------------------------------------------------------------
n per arm (simple, independent): 2,844 orders
n per arm (cluster-adjusted):    4,090 orders
Clusters per arm:                92 state-weeks
Total clusters:                  184 state-weeks
Total orders (approx):           8,180
------------------------------------------------------------
Olist-scale sanity check (historical):
  State-weeks in ~2yr history:   2,808
  Weeks if all 27 states enroll: ~7
  Feasibility Query B clusters:  2,152 state-weeks total
============================================================
```

### Interpretation

- Ignoring clustering would require ~**2,844 orders/arm** — **underpowered** for a state-week design.
- After DEFF adjustment: ~**4,090 orders/arm**, **92 state-weeks/arm**, **184 total state-weeks**, ~**8,180 delivered orders** total.
- **Recommended duration:** ~**7 calendar weeks** if all 27 Brazilian states participate each week (184 ÷ 27 ≈ 7). Add 1–2 weeks burn-in if ops need ramp time.

---

## 6. Feasibility

### Historical Olist volume (from notebook 03 Query B)

| Stat | Value |
|------|-------|
| Total state-weeks (delivered orders) | **2,152** |
| Avg orders per state-week | **44.8** |
| Median orders per state-week | **11.0** |
| Min / max cluster size | **1 / 1,108** |

### Can Olist-scale volume support this?

**Yes — at order of magnitude.** The experiment needs **184 state-weeks** and ~**8K delivered orders**. Olist's historical panel has **2,152 state-weeks** and ~**96K delivered orders** over ~2 years — roughly **12×** the required clusters and **12×** the required orders.

**Caveats for a real rollout (not Olist-specific):**

1. **Sparse clusters:** Median cluster size (11) is much lower than mean (44.8) because hub states (SP) dominate. A live experiment should **exclude or stratify** state-weeks below a minimum volume threshold (e.g. ≥ 20 delivered orders/week) so cluster-level rates are stable.
2. **ICC uncertainty:** We assumed ICC = 0.01. If true ICC is higher, required clusters grow; sensitivity analysis (ICC = 0.05) would roughly 5× DEFF — rerun `power_analysis.py` with different ICC before launch.
3. **Seasonality:** Olist spans Sep 2016 – Oct 2018; a 7-week window should avoid major holiday shocks or pre-specify seasonal stratification.

**Bottom line:** Sample size is **feasible** on marketplace-scale volume; the harder constraint is **operational** (rolling out incentives cleanly by state-week without leakage), not raw order count.

---

## 7. Failure modes

| Failure mode | Mechanism | Bias direction | Mitigation |
|--------------|-----------|----------------|------------|
| **Spillover across regions** | Sellers in treated states fulfill orders shipped to control states (or vice versa); shared national carriers reallocate capacity | **Attenuates** treatment effect (control contaminated) | Cluster at state-week; monitor cross-state seller mix; buffer states at borders |
| **Gaming / metric distortion** | Carriers or sellers widen estimated delivery windows so on-time is easier without faster delivery | **Inflates** treated on-time without real improvement | Guardrail on estimated-date drift; audit sample of deliveries |
| **Novelty / decay** | Early surge response fades after carriers adapt; effect concentrated in week 1–2 | **Overestimates** steady-state lift if experiment is too short | Run ≥ 7 weeks; analyze week-by-week treatment effect |
| **Selection into treated zones** | High-volume sellers migrate fulfillment toward incentivized states | **Inflates** treated on-time (better sellers, not incentive) | Randomize at state-week; compare seller mix pre/post in each arm |
| **Cost blowout** | Surge pricing escalates in hub states without proportional on-time gain | N/A (guardrail, not bias) | Pre-specify cost/order ceiling; stop if exceeded |

---

## 8. Decision rule

Pre-specify before launch. Apply after ~7 weeks (or once 184 state-weeks accumulated).

### Primary outcome — on-time rate

| Result | Recommendation to PM |
|--------|------------------------|
| **Point estimate ≥ 2 pp AND 95% CI excludes 0** | **Launch** regional incentive program (or expand pilot), subject to guardrails |
| **Point estimate positive but < 2 pp AND CI excludes 0** | **Iterate** — effect real but below business threshold; tune incentive size or target higher-volume state-weeks only |
| **95% CI includes 0** | **Do not launch** on current design; revisit incentive mechanism or extend experiment if guardrails allow |
| **Point estimate ≤ 0** | **Stop** — no evidence of benefit; investigate failure modes |

### Guardrails — automatic stops

- **Cost per order** exceeds pre-specified ceiling → pause, regardless of on-time lift
- **Review score** drops > 0.1 stars in treated clusters → pause
- **Estimated-date gaming proxy** spikes in treated arm → pause and audit

### Honesty framing for stakeholders

> "The quasi-experiment suggested ~1.3 pp associatively. This A/B test is powered to **detect** 2 pp causally. Hitting 1.5 pp with a tight CI may be scientifically interesting but **insufficient to launch** if our MDE was 2 pp — that distinction should be agreed with PM before we start."

---

## References

- Week 3 analysis: [`notebooks/03_diff_in_diff_analysis.ipynb`](../notebooks/03_diff_in_diff_analysis.ipynb)
- Power script: [`scripts/power_analysis.py`](../scripts/power_analysis.py)
- Causal framing: [`docs/DiD_CONCEPTUAL_REFERENCE.md`](DiD_CONCEPTUAL_REFERENCE.md)
