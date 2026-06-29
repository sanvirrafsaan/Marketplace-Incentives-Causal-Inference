# Decision Memo: Regional Surge Incentives & On-Time Delivery

| | |
|---|---|
| **To** | Product & Operations Leadership |
| **From** | Data Science / Marketplace Analytics |
| **Subject** | Should we launch regional surge incentives based on current evidence? |
| **Date** | June 2026 |
| **Recommendation** | **Do not launch nationally.** Approve a **~7-week cluster-randomized pilot** (state-week randomization) before any full rollout. |

---

## Bottom line

Observational analysis of a simulated regional incentive rollout suggests treated hub states (SP, RJ, MG) experienced a **~1.3 pp smaller decline** in on-time delivery vs control states after June 2017 (95% CI: 0.4–2.2 pp). That is a **signal worth testing**, not proof the incentive works. Both treated and control regions **got worse** in absolute terms post-cutoff.

**I recommend a randomized pilot**, not a launch. The pilot is powered to detect a **2 pp** lift — a conservative bar above the observational estimate — over **~7 weeks** at marketplace-scale volume.

---

## Context

### Business question

Would **regional surge incentives** for logistics partners improve **on-time delivery** in high-volume markets without harming customer satisfaction or unit economics?

### Why we analyzed observational data first

Ops teams often roll out incentives regionally before formal experimentation. We used historical e-commerce order data (~100K orders, Sep 2016 – Oct 2018) to:

1. Build a reliable order-level dataset and outcome definition
2. Simulate a regional rollout in SP, RJ, and MG starting June 2017
3. Estimate associational impact under difference-in-differences (DiD)
4. Scope a proper experiment if the signal merited further investment

**Important:** This was a **quasi-experiment on historical data**. We did **not** run a randomized A/B test. The experiment described below is a **proposal** for what should come next.

---

## Evidence

### Design

| Element | Definition |
|---------|------------|
| **Treated** | Orders in SP, RJ, MG from 2017-06-01 onward |
| **Control** | All other Brazilian states |
| **Outcome** | On-time delivery rate among **delivered** orders only |
| **Sample** | 96,470 delivered orders |

### Primary result

| Metric | Value |
|--------|-------|
| DiD estimate (τ̂) | **+1.34 pp** |
| Bootstrap 95% CI | **[0.40, 2.17] pp** |
| Cutoff sensitivity | **0.88–1.51 pp** across ±14 days — stable |

Hand-calculated 2×2 DiD and OLS regression (`treated × post`) agree.

### What actually happened to on-time rates

| Region | Pre-period | Post-period | Change |
|--------|------------|-------------|--------|
| Treated (SP/RJ/MG) | 96.4% | 93.7% | **−2.7 pp** |
| Control | 95.2% | 91.1% | **−4.0 pp** |

**Interpretation:** On-time delivery declined platform-wide after the cutoff. Treated states declined **less** than control — a relative gap of ~1.3 pp — not an absolute improvement in treated markets.

### Identification assessment

| Check | Finding |
|-------|---------|
| Pre-period balance | Treated hub states had similar on-time levels (~96% vs ~95%) but faster baseline delivery |
| Parallel trends | **Partially plausible** — level gap is OK for DiD; early-2017 slope differences and a synchronized late-2017 drop in both arms raise concern about confounding shocks |
| Robustness | Effect sign and order of magnitude hold across cutoff dates ±14 days |

### What this evidence supports — and what it does not

| Supports | Does not support |
|----------|------------------|
| Further investment in a randomized pilot | Full national launch |
| Incentive policy is plausibly associated with relative on-time resilience | Causal claim that incentives **caused** better delivery |
| ~1–2 pp effect size as a planning input | That treated regions improved in absolute terms |

---

## Recommendation

### Do not launch on DiD alone

Three reasons:

1. **No randomization** — SP/RJ/MG are high-volume hub states with different infrastructure; treated and control were never comparable by design.
2. **Parallel trends not verified** — the identifying assumption for DiD cannot be tested definitively with a short (~8 month) pre-period.
3. **Absolute performance still declined** — even treated states lost ~2.7 pp on-time post-cutoff; the policy case requires evidence of causal lift, not just slower decline.

### Do run a cluster-randomized pilot

Proceed with a **state-week randomized experiment** as specified in [`04_experiment_design.md`](04_experiment_design.md):

| Design parameter | Value |
|------------------|-------|
| Unit of randomization | `customer_state` × calendar week |
| Primary metric | On-time rate (delivered orders) |
| MDE | **2 pp** absolute (baseline control: 91.1%) |
| Power / α | 80% / 0.05 (two-sided) |
| Required sample | **184 state-weeks** · ~**8,180 delivered orders** |
| Duration | **~7 calendar weeks** (27 states enrolled) |
| Feasibility | Supported at historical marketplace volume (~2,152 state-weeks available) |

**Why 2 pp MDE when DiD showed ~1.3 pp?** The observational estimate is a prior, not a launch threshold. We should power for the **minimum effect worth the operational cost** of a national program — and the bootstrap CI allows true effects as low as 0.4 pp.

### Guardrails (pre-specified stops)

Monitor during the pilot regardless of primary metric:

- **Incentive cost per order** — pause if above pre-approved ceiling
- **Review score** — pause if treated clusters drop > 0.1 stars
- **Estimated-date drift** — pause if treated clusters show gaming (widening delivery windows without real speed gains)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Parallel trends violated** (observational phase) | DiD over- or under-states true effect | Randomized pilot removes this assumption |
| **Spillover across regions** | Attenuates measured treatment effect | State-week clustering; monitor cross-state seller mix |
| **Heterogeneous treated states** (RJ vs SP/MG) | Observational τ̂ averages unlike markets | Stratify pilot by volume tier; report subgroups if powered |
| **Common platform shocks** | Confound before/after comparisons | 7-week window; avoid major holiday periods; week-fixed effects in analysis |
| **Metric gaming** | Inflates on-time without real improvement | Estimated-date drift guardrail + delivery audit sample |
| **Pilot underpowered if ICC higher than assumed** | Miss real effects | Design-effect sensitivity; exclude ultra-sparse state-weeks (median cluster size = 11 orders) |

---

## Ask

Approve the following to move from observational analysis to causal validation:

1. **~7-week cluster-randomized pilot** — state-week assignment, 50/50 treated/control, powered for 2 pp MDE
2. **Budget for incentive spend** in treated clusters, with a pre-specified **cost-per-order ceiling**
3. **Analytics support** for weekly monitoring of primary metric + guardrails
4. **Pre-registered decision rule** — launch only if point estimate ≥ 2 pp and 95% CI excludes zero, with all guardrails intact; iterate if effect is positive but < 2 pp; stop if CI includes zero

**Not asking for:** National rollout, permanent policy change, or additional observational analysis without experimentation.

---

## Supporting materials

| Document | Contents |
|----------|----------|
| [`04_experiment_design.md`](04_experiment_design.md) | Full experiment spec — hypothesis, metrics, power analysis, failure modes, decision rules |
| [`../scripts/power_analysis.py`](../scripts/power_analysis.py) | Rerunnable sample-size calculator |
| [`../notebooks/03_diff_in_diff_analysis.ipynb`](../notebooks/03_diff_in_diff_analysis.ipynb) | DiD estimation, parallel trends, bootstrap CI, sensitivity |
| [`../README.md`](../README.md) | Project overview and reproduction steps |

---

*This memo summarizes observational findings from simulated historical data and proposes a prospective experiment. It does not claim that an incentive program was tested or launched on this dataset.*
