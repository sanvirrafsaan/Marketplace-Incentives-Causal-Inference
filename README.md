# Marketplace Incentives & Causal Inference

**End-to-end causal analytics on ~100K e-commerce orders:** multi-table SQL mart → simulated regional rollout → difference-in-differences with bootstrap confidence intervals → identification checks and sensitivity analysis.

> **Headline result:** Simulated surge-incentive rollout in SP/RJ/MG is associated with **+1.3 pp** higher on-time delivery vs control states (bootstrap 95% CI: **0.4–2.2 pp**), conditional on partially plausible parallel trends. Observational quasi-experiment — not a randomized A/B test.

**Rafsaan Sanvir** · Stats undergrad, U of T · [GitHub](https://github.com/sanvirrafsaan)

---

## Why this project exists

Marketplace ops teams often roll out **regional logistics incentives** before running formal experiments. The hard question is not “did on-time rate change?” but **“would this policy have caused the change, and how big is the effect?”**

Olist has no real incentive experiment. I built a reproducible pipeline, defined a credible quasi-experiment on historical data, estimated a causal effect with DiD, quantified uncertainty with bootstrap CIs, and documented what a **prospective randomized trial** would need to validate the finding.

Relevant for **Uber · DoorDash · Lyft · Shopify · Capital One** — marketplace experimentation, ops analytics, and causal inference under messy real-world data.

---

## What I built

| Phase | Deliverable | What it shows |
|-------|-------------|---------------|
| **Data engineering** | [`notebooks/01_data_ingestion.ipynb`](notebooks/01_data_ingestion.ipynb) + [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | 9-table DuckDB pipeline; order-level mart with grain checks; outcome definitions |
| **Treatment design** | [`notebooks/02_treatment_definition.ipynb`](notebooks/02_treatment_definition.ipynb) | Simulated regional rollout (SP/RJ/MG from 2017-06-01); causal DAG; pre-period balance |
| **Causal inference** | [`notebooks/03_diff_in_diff_analysis.ipynb`](notebooks/03_diff_in_diff_analysis.ipynb) | DiD estimate, parallel-trends diagnostics, bootstrap 95% CI, cutoff sensitivity |
| **Conceptual grounding** | [`docs/DiD_CONCEPTUAL_REFERENCE.md`](docs/DiD_CONCEPTUAL_REFERENCE.md) | Backdoor paths, parallel trends as identifying assumption, honest limitations |

**In progress:** prospective experiment design + power analysis (Week 4), decision memo (Week 5).

---

## Key finding (Week 3 — locked)

**Design:** Treated = orders in SP, RJ, MG from 2017-06-01 onward. Outcome = `on_time` among **delivered** orders only. Control = all other Brazilian states.

| Metric | Value |
|--------|-------|
| **DiD estimate (τ̂)** | **+1.34 pp** (hand calculation and OLS `treated × post` agree) |
| **Bootstrap 95% CI** | **[0.40, 2.17] pp** (order-level resampling, N = 1,000) |
| **Sample** | 96,470 delivered orders in DiD window |
| **Substantive read** | Both arms' on-time rates **fell** post-cutoff; treated states saw a **smaller decline** (~−2.7 pp vs ~−4.0 pp control) |
| **Cutoff sensitivity** | τ̂ stable at **0.88–1.51 pp** across ±14 days from cutoff |

**Pre/post on-time rates (delivered orders):**

| Arm | Pre (Sep 2016 – May 2017) | Post (Jun 2017+) |
|-----|---------------------------|------------------|
| Treated (SP/RJ/MG) | 96.4% | 93.7% |
| Control (other states) | 95.2% | 91.1% |

**Interpretation:** The simulated rollout is consistent with treated hub states **holding up better** during a platform-wide post-period decline — not with treated states improving in absolute terms. Parallel trends are **partially plausible** (level gap OK; late-2017 synchronized drop suggests a common shock).

**Limitations (stated explicitly in notebooks):** observational data; ~8-month pre-period; RJ heterogeneity within treated arm; parallel trends not testable; delivered-only outcome scope.

---

## Methods at a glance

```text
Raw CSVs (9 tables)
    → DuckDB joins + aggregations (fanout-safe)
    → orders_analytical (1 row / order_id)
    → Treatment: customer_state ∈ {SP, RJ, MG} × post ≥ 2017-06-01
    → DiD: (T̄_post − T̄_pre) − (C̄_post − C̄_pre)
    → Inference: bootstrap CI + cutoff sensitivity
    → Next: prospective cluster-randomized experiment design
```

**Identification:** Difference-in-differences under parallel trends. I check pre-period outcome trajectories, report balance on delivery speed and on-time levels, and stress that DiD estimates association under assumptions — not proof of causation without randomization.

**Uncertainty:** Bootstrap resampling at order level (1,000 iterations) rather than relying on a single point estimate.

**Robustness:** DiD re-estimated at cutoffs ±7 and ±14 days from 2017-06-01; effect sign and magnitude hold.

---

## Skills demonstrated

- **SQL / data modeling:** Multi-table joins, aggregation before join (order_items fanout), grain validation, DuckDB analytics
- **Causal inference:** DiD setup, parallel-trends assessment, treatment definition, DAG reasoning, sensitivity analysis
- **Statistics:** Bootstrap confidence intervals, two-way fixed-effects regression, interpretation of interaction terms
- **Python:** pandas, statsmodels, scipy, Jupyter narrative analysis
- **Communication:** Structured notebooks with acceptance checks, limitations sections, and PM-readable framing

---

## Repo map

```text
├── notebooks/
│   ├── 01_data_ingestion.ipynb      # Mart build + EDA
│   ├── 02_treatment_definition.ipynb # DAG, balance, treatment flags
│   └── 03_diff_in_diff_analysis.ipynb # DiD, parallel trends, bootstrap, sensitivity
├── docs/
│   ├── DATA_MODEL.md                # Schema, grains, join rules
│   ├── ENVIRONMENT.md               # Setup + Kaggle download
│   └── DiD_CONCEPTUAL_REFERENCE.md  # Causal framing reference
├── MASTERPLAN.md                    # Canonical plan + acceptance checks
├── PROJECT_PLAN.md                  # 5-week roadmap
└── requirements.txt
```

Data (`data/olist.db`, raw CSVs) is **not committed** — see [Reproduce locally](#reproduce-locally).

---

## Reproduce locally

**Prerequisites:** Python 3.10+, Kaggle account for dataset download.

```bash
git clone https://github.com/sanvirrafsaan/Marketplace-Incentives-Causal-Inference.git
cd Marketplace-Incentives-Causal-Inference
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

1. Download [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) CSVs to `data/raw/olist/` — see [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md).
2. Run notebooks in order: `01` → `02` → `03`.

**Stack:** Python · DuckDB · pandas · statsmodels · scipy · Matplotlib · Seaborn · Jupyter

---

## Resume bullets (copy-ready)

- Built a multi-table SQL/Python analytics pipeline on ~100K marketplace orders (DuckDB), constructing an order-level mart with grain validation and delivery outcome definitions for causal analysis.
- Designed and evaluated a simulated regional incentive rollout using difference-in-differences; estimated **+1.3 pp** effect on on-time delivery (bootstrap 95% CI: 0.4–2.2 pp) with parallel-trends checks and cutoff sensitivity analysis.
- Documented identification assumptions, platform-wide confounding, and limitations; scoped a prospective cluster-randomized experiment to validate observational findings.

---

## Data

[Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — ~99K orders, Sep 2016 – Oct 2018, 9 tables. Used under Kaggle terms; not redistributed in this repo.

---

## Status

| Week | Focus | Status |
|------|--------|--------|
| 1 | Ingestion + mart + EDA | ✅ |
| 2 | Treatment definition + balance | ✅ |
| 3 | DiD + bootstrap CI + sensitivity | ✅ |
| 4 | Experiment design + power analysis | 🔄 |
| 5 | Decision memo + polish | ⬜ |
