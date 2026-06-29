# Master Plan (Canonical) — Marketplace Incentives & Causal Inference (Olist)

This is the **single canonical plan** for the portfolio project.

- **Audience**: future-you, reviewers, and “other chats” that need a stable reference
- **Style**: you-build-it mentoring (driving questions + acceptance checks), not a finished implementation
- **Scope**: one end-to-end project (Olist) focused on **Difference-in-Differences (DiD)** + **bootstrap confidence intervals** + **experiment design**

---

## North-star story (what you’ll say in interviews)

You built a 9-table analytics pipeline (DuckDB + SQL), created an **order-level analytical mart**, simulated a **regional incentive rollout**, and evaluated its impact on **on-time delivery** using **DiD**, including **parallel trends checks**, **bootstrap CIs**, and **cutoff sensitivity**. Then you wrote a **prospective experiment design doc** with a **power analysis** for a real randomized rollout.

---

## End-goal artifacts (final repo deliverables)

### Analysis pipeline (reproducible)
- **Notebook 01**: `notebooks/01_data_ingestion.ipynb`
  - Loads 9 tables, validates keys/grains, builds `orders_analytical` in DuckDB
  - Outcome-focused EDA that supports causal design choices
- **Notebook 02**: `notebooks/02_treatment_definition.ipynb`
  - Treatment definition + DAG + pre-period balance
- **Notebook 03**: `notebooks/03_diff_in_diff_analysis.ipynb`
  - DiD estimate, parallel trends plot, bootstrap 95% CI, cutoff sensitivity

### Writing artifacts (high resume signal)
- `docs/04_experiment_design.md`: prospective experiment design + power analysis assumptions
- `docs/05_decision_memo.md`: decision memo communicating recommendation + risks
- `README.md`: one-page portfolio narrative (problem → method → result + CI → limitations → next steps)

### Optional but strong signal
- `sql/`: stabilized SQL queries extracted from notebooks (mart build, balance tables)
- `scripts/power_analysis.py`: small, rerunnable script mirroring the experiment power section

---

## Strategic constraints (what to optimize for)

### Portfolio signal
- **SQL**: joins + aggregation to stable analytical grain, plus sanity checks
- **Causal maturity**: identification assumptions, parallel trends, sensitivity checks
- **Uncertainty**: bootstrap CI and clear interpretation
- **Communication**: experiment design + memo writing

### Reusable frameworks (repeat across projects)
You’ll explicitly practice two repeatable frameworks:

#### Data cleaning framework (your template)
**Conceptualize → Locate solvable issues → Evaluate unsolvable issues → Augment → Note/Document**

#### EDA framework (your template)
**Requirements gathering → time/seasonality → dimensionality → summaries → distributions → data quality**

You’ll implement these as structured markdown sections + acceptance checks in notebooks.

---

## Causal chain (keep everything anchored to this)

Before any modeling, you must lock:

1. **Unit**: one row per `order_id` (analytical grain)
2. **Time**: what defines “order time” (recommend `order_purchase_timestamp`)
3. **Region**: what defines “regional rollout” (recommend `customer_state` first)
4. **Outcome**: what is “on-time” (recommend “delivered on/before estimated date”)

Only after those are stable do you define treatment and run DiD.

---

## Week-by-week plan with definition of done

### Week 1 — Ingestion → analytical mart → outcome-focused EDA (~7 hrs)

**Primary deliverable**: `data/olist.db` + `orders_analytical` (one row per order) + EDA that supports causal choices.

#### Phase 1: Load all 9 tables into DuckDB
**Driving questions**
- What is each table’s **grain** and **primary key**?
- Which columns must be parsed as timestamps / numeric?
- Where are missing values “structural” (e.g., non-delivered orders) vs data errors?

**Acceptance checks**
- `information_schema.tables` shows 9 tables (or views)
- Row counts match expectations (orders ~100k)
- You can state (in markdown) the grain of each table in one line

#### Phase 2: Build `orders_analytical` (order grain)
**Required**: all fanout tables must be **aggregated to order level before joining**.

**Recommended columns (minimum viable mart)**
- IDs/dimensions: `order_id`, `customer_id`, `customer_state`
- Time: `purchase_ts`, `purchase_date`, `purchase_week` (or month)
- Status/timestamps: `order_status`, `delivered_customer_ts`, `estimated_delivery_date`
- Item aggregates: `n_items`, `n_sellers`, `gross_revenue`, `freight_total`
- Payments: `payment_total`, `n_payments`
- Reviews: `review_score` (expect missingness)
- Outcomes:
  - `is_delivered`
  - `delivery_days` (delivered-only)
  - `on_time` (delivered-only)

**Outcome definition (recommended)**
- `on_time = 1` iff `order_delivered_customer_date::date <= order_estimated_delivery_date::date`
- Define `on_time` as **NULL** for not-delivered orders (don’t force 0/1)

**Acceptance checks (non-negotiable)**
- **Grain**: `COUNT(*) = COUNT(DISTINCT order_id)` on `orders_analytical`
- **No accidental fanout**: `n_items` distribution looks plausible (median ~1; max not insane)
- **Null logic**: delivered timestamps are missing primarily when `order_status != 'delivered'`
- **Outcome sanity**:
  - `delivery_days` is mostly non-negative
  - `on_time` rate among delivered is plausible (not 0%/100%)

#### Phase 3: EDA that supports DiD (not “random plots”)
**Required plots/tables**
- Orders over time (weekly or monthly), overall + treated-candidate states
- On-time rate over time (weekly or monthly), overall + by state
- Delivery-days distribution (delivered only), plus tail summary (p90/p95)

**Acceptance checks**
- You can name a **candidate cutoff window** that has enough pre/post volume
- You can name **candidate treated states** by baseline volume (table)

**Week 1 done when**
- `orders_analytical` exists in DuckDB and passes grain checks
- You have the 3 required EDA outputs + markdown decisions recorded

---

### Week 2 — Treatment definition + DAG + pre-period balance (~7 hrs)

**Primary deliverable**: treatment indicator + causal framing + balance evidence that motivates DiD.

#### Phase 1: Define treatment and comparison
**Driving questions**
- What is the “policy rollout” you’re simulating (states + cutoff)?
- Why are those states treated (volume? operational justification)?
- What is your control group (all other states vs matched subset)?

**Acceptance checks**
- A single markdown cell states:
  - treated regions list
  - cutoff date
  - pre/post windows
  - inclusion/exclusion rules (e.g., delivered-only for on_time)

#### Phase 2: Draw a DAG (even if simple)
**Driving questions**
- What could violate parallel trends (seasonality, composition shifts, regional shocks)?
- Which variables are “bad controls” (post-treatment)?

**Acceptance checks**
- A DAG exists (image, mermaid, or hand-drawn photo committed) with a short explanation of threats

#### Phase 3: Pre-period balance table(s)
**Goal**: establish the groups are comparable *enough* pre, and document where they are not.

**Acceptance checks**
- Pre-period-only table by group (treated vs control):
  - `n_orders`
  - baseline on-time rate (delivered-only)
  - avg delivery days (delivered-only)
  - avg `n_items`, `gross_revenue`, `freight_total`

**Week 2 done when**
- Treatment is fully defined and reproducible
- Balance evidence exists (even if imperfect) and you’ve documented implications

---

### Week 3 — DiD estimate + parallel trends + bootstrap CI + sensitivity (~8 hrs)

**Primary deliverable**: defensible DiD estimate with uncertainty + assumption checks.

#### Step A: 2×2 DiD “by hand”
**Acceptance checks**
- You compute DiD via:
  - a 2×2 mean table, and
  - a regression specification
- Both methods match (within rounding)

#### Step B: Parallel trends check (highest priority)
**Acceptance checks**
- Plot weekly outcome (on_time rate among delivered) for treated vs control
- Show **pre period only** plot and a full window plot
- You explicitly write whether pre trends look plausible and what you’ll do if not

#### Step C: Bootstrap 95% CI
**Acceptance checks**
- You state resampling unit (orders initially; optionally clustered)
- You report point estimate + 95% CI + interpretation in plain language

#### Step D: Cutoff sensitivity
**Acceptance checks**
- Table of DiD estimates for cutoff ±7 and ±14 days
- You interpret stability/instability

**Week 3 done when**
- You have a DiD estimate + CI + parallel trends plot + sensitivity table, and a short limitations section

---

### Week 4 — Prospective experiment design + power analysis (~6 hrs)

**Primary deliverable**: a PM-facing experiment plan that could follow the quasi-experiment.

**Acceptance checks**
- `docs/04_experiment_design.md` includes:
  - hypothesis, unit of randomization, metrics, duration
  - power analysis assumptions (baseline, MDE, alpha, power)
  - feasibility discussion + failure modes (spillover, gaming)

---

### Week 5 — Polish + narrative + resume bullets (~7 hrs)

**Acceptance checks**
- `README.md` has: problem → method → finding + CI → limitations → experiment next step
- `docs/05_decision_memo.md` exists and is coherent
- Repo runs end-to-end from fresh clone (minus Kaggle data download)
- 2–3 resume bullets drafted and consistent with what’s in repo

---

## Global acceptance checks (use throughout)

### Mart health checks (run after any change)
- **Grain**: `COUNT(*) == COUNT(DISTINCT order_id)`
- **Key coverage**: percent missing for `customer_state`, timestamps, estimated date
- **Duplicates**: no duplicate `order_id` rows after joins

### Outcome checks
- on_time only defined for delivered orders (others NULL)
- negative delivery days investigated and either fixed or documented

### Causal-design checks
- pre-period volume exists for each week (avoid sparse-week noise)
- parallel trends assessed and documented before trusting DiD

---

## Olist gotchas (practical)

- Delivered timestamps missing for non-delivered statuses (structural missingness)
- `geolocation` has many rows per zip prefix; aggregate before join if you use it
- `order_items` fans out; aggregate to order level first
- Reviews are missing for many orders; treat satisfaction as secondary outcome

---

## “Paste back for feedback” contract (how mentoring works)

When you finish any major step, paste:
- the query/output table(s) for acceptance checks (row counts, grain check, null rates)
- 1–2 plots (screenshot or description + summary stats)
- the exact code cell(s) you wrote (10–30 lines), not the whole notebook

This keeps you driving and lets feedback be surgical.

