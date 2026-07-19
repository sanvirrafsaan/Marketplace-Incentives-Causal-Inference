# Olist Causal Inference — Interview Defense (Part 2 of 3)

> Tier 2 decisions (9–15). Assumes Part 1 context (project overview + danger-zone rules).

---

# TIER 2 — Strong DS signal, expect follow-ups

---

## Decision 9 — Aggregate `order_items` / `order_payments` before joining

**Decision:** Aggregate fanout tables to order level in CTEs, then left-join to the `orders` spine.

**One-line answer to own:** "`order_items` is line-item grain — 112,650 rows for 99,441 orders — so I aggregate to one row per order before joining, or the join fans out and corrupts every rate."

**Actual code (mart CTEs):**
```sql
WITH item_agg AS (
    SELECT order_id,
           COUNT(*) AS n_items,
           COUNT(DISTINCT seller_id) AS n_sellers,
           SUM(price) AS gross_revenue,
           SUM(freight_value) AS freight_total
    FROM order_items GROUP BY order_id
),
pay_agg AS (
    SELECT order_id, COUNT(*) AS n_payments, SUM(payment_value) AS payment_total
    FROM order_payments GROUP BY order_id
),
rev AS (
    SELECT order_id, AVG(review_score) AS review_score
    FROM order_reviews GROUP BY order_id
)
SELECT o.order_id, ...
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN item_agg i ON o.order_id = i.order_id
LEFT JOIN pay_agg  p ON o.order_id = p.order_id
LEFT JOIN rev      r ON o.order_id = r.order_id
```

**Why this choice:** A multi-item order joined raw would duplicate the order row once per item, so `AVG(on_time)` would silently weight orders by item count. Aggregating first preserves order grain (verified: median `n_items`=1, max 21) and keeps `gross_revenue`/`freight_total` as true per-order sums.

**Follow-ups:**
- *"How would fanout show up in results?"* → "On-time rate becomes an item-weighted average, biased toward big-basket orders; grain check `COUNT(*) = COUNT(DISTINCT order_id)` would also fail."
- *"Why LEFT JOIN not INNER?"* → "To keep every order even if it has no items/payments/reviews rows, so the mart stays at full 99,441 coverage."
- *"Reviews are averaged — why?"* → "Some orders have multiple review rows; averaging to order grain avoids re-introducing fanout, at the cost of treating review_score as secondary/missing-heavy."

**Danger zone:** Don't claim the mart is "clean" without citing the grain + fanout sanity checks.

---

## Decision 10 — Balance table vs parallel trends plot (what each checks)

**Decision:** Use a pre-period balance table for *levels* (δ) and a pre-period trend plot for *slopes* (λ) — two distinct validity checks.

**One-line answer to own:** "The balance table asks 'are the groups at similar levels before the policy?'; the parallel trends plot asks 'were they moving together before the policy?' — different questions, and DiD only needs the second."

**Actual code (balance table):**
```sql
SELECT
  CASE WHEN treated_region = 1 THEN 'treated' ELSE 'control' END AS arm,
  COUNT(*) AS n_orders,
  AVG(on_time) AS on_time_rate,
  AVG(delivery_days) AS avg_delivery_days,
  AVG(n_items) AS avg_n_items,
  AVG(gross_revenue) AS avg_gross_revenue,
  AVG(freight_total) AS avg_freight_total
FROM orders_treated
WHERE purchase_date < '2017-06-01' AND is_delivered = TRUE
GROUP BY 1;
-- treated: n=7,102 on_time=0.964 delivery_days=11.0 n_items=1.14 rev=135.4 freight=19.1
-- control: n=3,963 on_time=0.952 delivery_days=16.9 n_items=1.13 rev=155.0 freight=26.8
```

**Why this choice:** Students conflate these. The balance table shows treated and control have similar on-time *levels* (96.4% vs 95.2%) but a big *level* gap in delivery speed (11 vs 17 days) — evidence of the W infrastructure path. That gap is fine for DiD (differenced out) as long as *trends* were parallel — which only the plot can speak to (and only weakly).

**Follow-ups:**
- *"Biggest gap in the balance table — meaning?"* → "avg_delivery_days 11 vs 17: treated hubs deliver ~6 days faster pre-cutoff — the clearest signal of the state-infrastructure backdoor path W."
- *"On-time levels are close pre — doesn't that prove comparability?"* → "No. Similar levels ≠ parallel trends. Comparable levels are reassuring but neither necessary nor sufficient for DiD validity."
- *"Which balance covariates are safe to check?"* → "Pre-treatment ones only. Post-treatment variables would be bad controls."

**Danger zone:** Don't say "balance table confirms parallel trends" — it checks δ, not λ.

---

## Decision 11 — Hand DiD + OLS `treated×post` (same estimand two ways)

**Decision:** Compute τ̂ both as a 2×2 mean contrast and as the interaction coefficient in `on_time ~ treated_region * post`, and show they agree.

**One-line answer to own:** "The 2×2 hand calc and the OLS interaction term both give +0.013 — same estimand, but the regression also hands me a standard error and p-value."

**Actual code:**
```python
df["on_time"] = df["on_time"].astype(float)   # BooleanDtype breaks patsy
df["treated_region"] = df["treated_region"].astype(int)
model = smf.ols("on_time ~ treated_region * post", data=df).fit()
# treated_region:post coefficient = 0.0134, p ≈ 0.012, 95% CI ≈ [0.003, 0.024]
```

**Why this choice:** Doing it by hand proves I understand what DiD *is*; the regression gives inference and generalizes to controls/fixed effects. Their agreement is a correctness check. I use a linear probability model (OLS on a 0/1 outcome) so the interaction is directly in probability points and matches the hand number.

**Follow-ups:**
- *"Which coefficient is τ̂ and why?"* → "The `treated_region:post` interaction. Intercept = control pre mean; `treated_region` = pre-period level gap (δ); `post` = control's pre→post change (λ in control); interaction = the extra treated change = DiD."
- *"Why cast on_time to float?"* → "pandas BooleanDtype breaks patsy's formula parsing; casting to float makes it a clean 0/1 numeric LPM."
- *"Why OLS not logistic for a binary outcome?"* → "LPM gives an effect directly in percentage points that equals the hand DiD; logistic would give odds ratios that don't map 1:1 to the 2×2 difference. For a group-contrast estimand, LPM is cleaner. R²≈0.004 is expected — I'm estimating a contrast, not predicting orders."

**Danger zone:** Don't over-interpret R² or the non-interaction coefficients as effects.

---

## Decision 12 — Cutoff sensitivity (±7, ±14 days)

**Decision:** Re-estimate DiD at 5 cutoffs around 2017-06-01 to show the result isn't an artifact of one arbitrary date.

**One-line answer to own:** "Shifting the cutoff ±14 days keeps τ̂ between 0.88 and 1.51 pp, same sign and order of magnitude — so the effect isn't a knife-edge artifact of one date."

**Actual code:**
```python
cutoffs = ["2017-05-18", "2017-05-25", "2017-06-01", "2017-06-08", "2017-06-15"]
sensitivity = [{"cutoff": c, "did_estimate": did_estimate(df_boot, cutoff=c)} for c in cutoffs]
# 0.88, 1.15, 1.34, 1.38, 1.51 pp
```

**Why this choice:** The 2017-06-01 date is admittedly arbitrary (no real policy), so robustness to it is essential. Reusing the same `did_estimate(cutoff=...)` helper keeps it clean and reproducible.

**Follow-ups:**
- *"Why does moving the cutoff change τ̂ at all?"* → "It reassigns near-boundary months between pre and post, shifting each arm's means slightly — and seasonality (S) around summer volume moves with it."
- *"What would 'unstable' look like?"* → "Sign flips or estimates swinging by multiples across two weeks — that would mean the effect is an artifact of one date."
- *"Does stability prove causality?"* → "No — it's a robustness check on specification, not on the parallel-trends assumption."

**Danger zone:** Don't oversell — stability supports the *direction*, not the causal claim.

---

## Decision 13 — DAG with S, W, C confounders

**Decision:** Draw a DAG with three backdoor forks — Seasonality (S), State infrastructure (W), Order composition (C) — into treatment and outcome.

**One-line answer to own:** "My DAG names three things that could confound the treatment–outcome link: seasonality, state logistics infrastructure, and order composition — and DiD is my strategy to neutralize the time-invariant parts."

**Actual code (DAG arrows defined explicitly):**
```python
arrows = [
    ("seasonality", "incentive_flag"), ("seasonality", "on_time"),
    ("state_infra", "incentive_flag"), ("state_infra", "on_time"),
    ("order_comp", "incentive_flag"), ("order_comp", "on_time"),
    ("incentive_flag", "on_time"),
]
# nodes: seasonality=purchase_month, state_infra=customer_state, order_comp=(n_items, freight_total)
```

**Why this choice:** Making threats explicit disciplines the analysis. W is the strongest (I chose treated states *because* they're hubs — the balance table's 6-day delivery gap is its fingerprint). S and C matter more as *trend* threats (λ) because they can move differently across arms over time.

**Follow-ups:**
- *"Is seasonality a confounder of treatment or a trends threat?"* → "Nuance: `post` is pure calendar time, so seasonality doesn't really *select* who's treated — it mainly threatens parallel trends if treated/control have different seasonal patterns. W is the true selection confounder."
- *"Name a bad control you excluded."* → "`delivery_days` or `review_score` measured post-cutoff — they're outcomes of the treatment, so conditioning on them would induce post-treatment bias."
- *"How does DiD handle these?"* → "It differences out any time-invariant level differences (δ) from W; it does *not* fix differential trends (λ) from S or C — that's the residual risk."

**Danger zone:** Don't claim the DAG is exhaustive or that DiD closes all three paths — it only removes time-invariant components.

---

## Decision 14 — Recommend NOT launching on DiD alone → propose a pilot

**Decision:** Recommend against a national launch based on the DiD; propose a cluster-randomized state-week pilot instead.

**One-line answer to own:** "The DiD is a signal, not proof — it rests on untestable parallel trends and treated states still declined absolutely — so I recommend a randomized state-week pilot before any rollout."

**Actual code / docs:** decision logic lives in `docs/05_decision_memo.md` and the Week 3 Limitations cell (8 numbered limitations). The recommendation flows from: no randomization + parallel trends unproven + absolute decline + (Part 3) fragile CI under clustering.

**Why this choice:** Recommending a launch off +1.3 pp observational would be exactly the overclaim the honesty rules forbid. A pilot converts an assumption-dependent association into a randomized causal test with pre-specified metrics and guardrails.

**Follow-ups:**
- *"CI excludes zero — why not launch?"* → "The order-level CI excludes zero but assumes independent orders; the state-clustered CI (Part 3) includes zero. Statistical significance under the wrong error model isn't a launch case."
- *"One-sentence ask to a PM?"* → "Fund a ~7-week state-week randomized pilot powered to detect 2 pp, with cost and gaming guardrails, before committing to a national incentive program."
- *"What guardrails?"* → "Incentive cost per order, review score, and estimated-date drift (a gaming proxy)."

**Danger zone:** Don't frame the pilot as something already run — it's designed, not executed.

---

## Decision 15 — State-week randomization + power for 2 pp MDE

**Decision:** Design the pilot to randomize at the state-week level and size it via a cluster-adjusted power analysis for a 2 pp MDE.

**One-line answer to own:** "I randomize state-weeks — not orders — because incentives deploy regionally and orders within a region interfere; then I power for a 2 pp business-meaningful lift with a design-effect adjustment for clustering."

**Actual code (`scripts/power_analysis.py`):**
```python
def cohens_h(p1, p2):
    return 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))

h = cohens_h(0.911, 0.931)                 # = 0.0743
n_per_arm_simple = NormalIndPower().solve_power(
    effect_size=h, alpha=0.05, power=0.80, ratio=1.0, alternative="two-sided")  # ~2,844
deff = 1 + (44.8 - 1) * 0.01               # = 1.44  (m=44.8 orders/cluster, ICC=0.01)
n_per_arm_adjusted = n_per_arm_simple * deff          # ~4,090
clusters_per_arm = math.ceil(n_per_arm_adjusted / 44.8)  # 92 → 184 total, ~8,180 orders, ~7 weeks
```

**Why this choice:** Order-level randomization violates SUTVA (shared sellers/carriers within a region) and doesn't match how ops toggles incentives; state-week is the real policy lever. MDE=2 pp (not the observed 1.34 pp) because MDE is the *minimum effect worth detecting* for a costly program, not a guess at the truth — and the bootstrap lower bound allows effects as small as 0.4 pp. DEFF inflates the naive sample to account for within-cluster correlation.

**Follow-ups:**
- *"Explain Cohen's h in one sentence."* → "It's an effect-size measure for two proportions using an arcsine-square-root transform so variance is stabilized — here h≈0.074 for 91.1%→93.1%."
- *"What is DEFF and ICC?"* → "ICC is the share of variance due to between-cluster differences; DEFF = 1+(m−1)·ICC is the factor by which clustering inflates required sample. At m=44.8, ICC=0.01 → DEFF=1.44."
- *"What if ICC is 0.05, not 0.01?"* → "DEFF jumps to 1+(43.8)(0.05)=3.19, more than doubling required clusters — so I flag ICC as the key assumption to pin down before launch."
- *"Why 2 pp when DiD was 1.34 pp?"* → "Business detectability bar vs observational point estimate; powering for the smaller number would balloon sample size and detect effects too small to justify program cost."

**Danger zone:** Don't present power outputs (184 clusters, ~7 weeks) as results of a run experiment — they're design targets from assumed inputs (ICC especially).

---

*Continue to Part 3 (`INTERVIEW_DEFENSE_PART3.md`) for Tier 3 decisions 16–20, including the real state-clustered bootstrap result.*
