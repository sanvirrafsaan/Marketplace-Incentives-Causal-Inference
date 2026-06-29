# Marketplace Incentives & Causal Inference

**Would regional surge incentives improve on-time delivery — and how would we know?**

Using ~100K orders from the Olist Brazilian e-commerce dataset, I built an end-to-end analytics pipeline, evaluated a simulated regional incentive rollout with difference-in-differences, and scoped a cluster-randomized experiment to validate the result. The analysis estimates a **+1.3 pp** associational lift in on-time delivery (95% CI: **0.4–2.2 pp**) — a signal worth testing, not proof of causation.

**Rafsaan Sanvir** · Statistics, University of Toronto · [GitHub](https://github.com/sanvirrafsaan)

---

## Problem

Marketplace operations teams frequently deploy **regional logistics incentives** — surge bonuses, priority routing, carrier subsidies — before running formal experiments. That creates a recurring analytics question:

> *Did on-time delivery improve because of the incentive, or because treated regions were already different?*

The Olist dataset has no recorded A/B test for this policy. I treated it as a realistic ops scenario: build a trustworthy data foundation, estimate impact under explicit causal assumptions, quantify uncertainty, and recommend how to validate the finding with a proper experiment.

---

## Approach

```text
9 raw tables (DuckDB)
  → order-level analytical mart (grain-validated)
  → simulated regional rollout (SP / RJ / MG from Jun 2017)
  → difference-in-differences + bootstrap CI
  → parallel-trends diagnostics + cutoff sensitivity
  → prospective cluster-randomized experiment design + power analysis
```

| Stage | What I did |
|-------|------------|
| **Data engineering** | Joined 9 tables into `orders_analytical` (one row per order); aggregated fanout tables before joining; defined `on_time` for delivered orders only |
| **Treatment design** | Simulated treated states (SP, RJ, MG) vs all other Brazilian states; documented causal DAG and pre-period balance |
| **Impact estimation** | DiD via 2×2 means and OLS (`treated × post`); bootstrap 95% CI (1,000 resamples); cutoff sensitivity ±14 days |
| **Experiment planning** | Proposed state-week cluster randomization; power analysis for 2 pp MDE with design-effect adjustment ([`scripts/power_analysis.py`](scripts/power_analysis.py)) |

**Identification:** DiD under parallel trends. I report pre-period trajectories, balance checks, and sensitivity — and state clearly that observational DiD is association, not causal proof.

---

## Results

**Setup:** Treated = SP, RJ, MG from 2017-06-01. Control = remaining states. Outcome = on-time rate among **delivered** orders. Sample = **96,470** orders.

| | Estimate |
|--|----------|
| **DiD effect (τ̂)** | **+1.34 pp** (2×2 and regression agree) |
| **Bootstrap 95% CI** | **[0.40, 2.17] pp** |
| **Cutoff sensitivity** | **0.88–1.51 pp** across ±14 days — stable sign and magnitude |

**On-time rates among delivered orders:**

| | Pre-period | Post-period | Change |
|--|------------|-------------|--------|
| **Treated (SP/RJ/MG)** | 96.4% | 93.7% | −2.7 pp |
| **Control** | 95.2% | 91.1% | −4.0 pp |

**How to read this:** Both regions got worse after the cutoff — consistent with a platform-wide decline. Treated states **fell less**, yielding a positive DiD. That is a *relative* difference, not evidence that treated states improved in absolute terms.

**Parallel trends:** Partially plausible. A level gap between arms is expected and handled by DiD; a synchronized late-2017 drop in both arms suggests a common shock unrelated to the simulated rollout.

---

## Recommendation

**Do not launch incentives based on this analysis alone.** The DiD result is observational and depends on untestable parallel-trends assumptions.

**Proposed validation:** A cluster-randomized pilot randomizing at the **state-week** level, powered to detect a **2 pp** absolute lift (conservative vs the ~1.3 pp DiD estimate):

| Parameter | Value |
|-----------|-------|
| Baseline on-time (control) | 91.1% |
| Minimum detectable effect | 2 pp |
| Required sample | ~184 state-weeks · ~8,180 delivered orders |
| Estimated duration | ~7 weeks (27 states) |
| Feasibility | Supported at Olist-scale historical volume |

Full design in [`docs/04_experiment_design.md`](docs/04_experiment_design.md). Executive summary and ask in [`docs/05_decision_memo.md`](docs/05_decision_memo.md).

---

## Limitations

- **Observational design** — treated hub states differ in volume and infrastructure; no randomization
- **Parallel trends assumed** — pre-period is ~8 months; not definitively verified
- **Heterogeneous treated arm** — RJ underperforms SP/MG; τ̂ is a weighted average
- **Delivered orders only** — on-time is undefined for non-delivered orders
- **Bootstrap resampling** — order-level resamples may yield optimistic CIs vs cluster bootstrap

These are documented explicitly in the analysis notebooks.

---

## Repository

| Artifact | Description |
|----------|-------------|
| [`notebooks/01_data_ingestion.ipynb`](notebooks/01_data_ingestion.ipynb) | Multi-table pipeline, mart build, EDA |
| [`notebooks/02_treatment_definition.ipynb`](notebooks/02_treatment_definition.ipynb) | Treatment flags, DAG, balance table |
| [`notebooks/03_diff_in_diff_analysis.ipynb`](notebooks/03_diff_in_diff_analysis.ipynb) | DiD, parallel trends, bootstrap, sensitivity |
| [`docs/04_experiment_design.md`](docs/04_experiment_design.md) | Prospective experiment design + power analysis |
| [`docs/05_decision_memo.md`](docs/05_decision_memo.md) | PM-facing recommendation and ask |
| [`docs/DATA_MODEL.md`](docs/DATA_MODEL.md) | Schema, grains, join rules |
| [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md) | Local setup |
| [`scripts/power_analysis.py`](scripts/power_analysis.py) | Rerunnable sample-size calculator |

**Stack:** Python · DuckDB · pandas · statsmodels · scipy · Jupyter · Matplotlib · Seaborn

---

## Reproduce

```bash
git clone https://github.com/sanvirrafsaan/Marketplace-Incentives-Causal-Inference.git
cd Marketplace-Incentives-Causal-Inference
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

1. Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) to `data/raw/olist/` ([instructions](docs/ENVIRONMENT.md))
2. Run notebooks `01` → `02` → `03` in order
3. `python scripts/power_analysis.py`

Raw data and DuckDB files are gitignored (Kaggle license / size).

---

## Data

[Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — ~99K orders, Sep 2016 – Oct 2018, 9 tables. Used under Kaggle terms; not redistributed in this repo.

---

## Resume summary

- Built a multi-table SQL/Python analytics pipeline on ~100K marketplace orders (DuckDB), with order-level grain validation and delivery outcome definitions.
- Evaluated a simulated regional incentive rollout via difference-in-differences; estimated **+1.3 pp** on on-time delivery (bootstrap 95% CI: 0.4–2.2 pp) with parallel-trends checks and cutoff sensitivity.
- Scoped a cluster-randomized state-week experiment with power analysis (2 pp MDE, ~184 clusters, ~7 weeks) to validate observational findings.
