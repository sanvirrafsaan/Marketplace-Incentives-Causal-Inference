# Olist Causal Inference — Interview Defense (Part 1 of 3)

> Paste Parts 1–3 into a fresh Claude chat for interview drilling. This part = project overview, danger-zone rules, and Tier 1 decisions (1–8). Part 2 = Tier 2 (9–15). Part 3 = Tier 3 (16–20), including a **real** state-clustered bootstrap result.

---

## How to use this document

Give Claude this instruction: *"Drill me one decision at a time. Ask me the follow-up questions before showing the model answer. Stop me if I overclaim causality or say I ran a real experiment. Do not invent numbers — use only what's in this doc."*

Pass criteria per decision: explain it aloud in <90s, handle one follow-up, name the code location — no notes.

---

## DANGER ZONE — global honesty rules (never violate)

- This is a **SIMULATED quasi-experiment on observational data**, NOT a real A/B test.
- I did **not run or design a live experiment**; the cluster-randomized pilot is **DESIGNED, not executed**.
- DiD estimates an **association under assumptions** (parallel trends), not a proven causal effect.
- I recommend **NOT launching** based on DiD alone.
- Never say "incentives improved on-time delivery" without "**relative to control**" — both arms declined.
- Never present +1.34 pp as precise truth; it is conditional on untestable parallel trends and (see Part 3) fragile to how uncertainty is computed.

---

## Project Overview (context for a fresh chat)

**Business question:** Would regional surge/logistics incentives improve **on-time delivery** in high-volume Brazilian states — and how would we know?

**Dataset:** Olist Brazilian E-Commerce (Kaggle), 9 tables, **99,441 orders**, Sep 2016 – Oct 2018.

**Pipeline:** 9 CSVs → DuckDB (`data/olist.db`) → order-level mart `orders_analytical` (1 row per `order_id`) → `orders_treated` view (adds treatment flags) → DiD analysis → proposed experiment design.

**Causal design (locked):**
- **Treated:** `customer_state IN ('SP','RJ','MG')` → `treated_region = 1`
- **Cutoff:** `2017-06-01` → `post = 1`
- **Treatment:** `incentive_flag = treated_region AND post`
- **Control:** all other Brazilian states
- **Outcome:** `on_time` = delivered on/before estimated date, **delivered orders only** (NULL otherwise)
- **Grain:** one row per `order_id`

**Sample sizes:**
- Full mart: 99,441 orders; delivered ~96,478 (~97%); DiD sample = **96,470** delivered with non-null `on_time`
- 2×2 order counts (all orders): Control pre 4,188 / post 29,020; Treated pre 7,507 / post 58,726
- Balance table (delivered, pre-cutoff): treated 7,102 / control 3,963

**Headline result:**
- DiD τ̂ = **+1.34 pp** (hand 2×2 and OLS `treated_region:post` interaction agree)
- Order-level bootstrap 95% CI = **[0.40, 2.17] pp** (N=1,000)
- Pre/post on-time (delivered): Treated 96.4% → 93.7% (−2.7 pp); Control 95.2% → 91.1% (−4.0 pp)
- Cutoff sensitivity ±14 days: τ̂ 0.88–1.51 pp, stable sign
- Parallel trends: **partially plausible, not clean**

---

# TIER 1 — Will almost always ask

---

## Decision 1 — Simulated quasi-experiment, not a real A/B test

**Decision:** Frame the entire project as a simulated regional rollout evaluated with DiD on historical observational data.

**One-line answer to own:** "Olist never ran this incentive, so I simulated a regional rollout on historical data and used difference-in-differences to estimate its association with on-time delivery — it's a quasi-experiment, not a randomized test."

**Actual code (the treatment is defined by me, in SQL — there is no experiment table):**
```sql
CREATE OR REPLACE VIEW orders_treated AS
    SELECT *,
    CASE WHEN customer_state IN ('SP', 'RJ', 'MG') THEN 1 ELSE 0 END AS treated_region,
    CASE WHEN purchase_date >= '2017-06-01' THEN 1 ELSE 0 END AS post,
    CASE WHEN treated_region = 1 AND post = 1 THEN 1 ELSE 0 END AS incentive_flag
    FROM orders_analytical;
```

**Why this choice:** No column in Olist records an incentive policy. Marketplace ops teams routinely roll out incentives regionally *before* formal experiments, so simulating a regional rollout and estimating it with DiD mirrors a realistic analytics workflow — while being honest that assignment was not randomized.

**Follow-ups:**
- *"So this proves nothing?"* → "It gives a defensible directional signal under stated assumptions and, more importantly, demonstrates the full identification workflow. Proof of causality would require the randomized pilot I designed in Week 4."
- *"Why not just find a dataset with a real experiment?"* → "The skill I'm showing is exactly what ops analysts face: no clean experiment, messy observational data, and the judgment to frame a credible quasi-experiment and state its limits."
- *"What would make this causal?"* → "Random assignment of the incentive to state-weeks, which removes the backdoor paths my DAG identifies."

**Danger zone:** Never say "we ran an experiment on Olist" or "we proved incentives work." Say "simulated rollout / quasi-experiment / DiD."

---

## Decision 2 — Outcome = `on_time`, delivered orders only

**Decision:** Define `on_time = 1` if delivered on/before the estimated date, computed **only** for delivered orders; NULL otherwise. `delivery_days` is secondary.

**One-line answer to own:** "On-time is only defined for delivered orders — a non-delivered order has no meaningful on-time status, so I set it NULL rather than forcing a 0."

**Actual code (mart build):**
```sql
CASE
    WHEN o.order_status = 'delivered'
         AND o.order_delivered_customer_date IS NOT NULL
    THEN CASE
        WHEN CAST(o.order_delivered_customer_date AS DATE)
             <= CAST(o.order_estimated_delivery_date AS DATE)
        THEN 1 ELSE 0
    END
END AS on_time
```

**Why this choice:** Olist has no SLA field, so the platform's own `estimated_delivery_date` is the promise benchmark. Non-delivered orders have structurally missing delivery timestamps (2,965 nulls, almost all non-delivered statuses) — coding them 0 would conflate "late" with "cancelled/unavailable" and bias the rate. NULL keeps the outcome clean and the denominator honest.

**Follow-ups:**
- *"Why not code not-delivered as 0 (a failure)?"* → "That mixes two different failures — delivery lateness vs order non-completion. It would inflate the 'not on-time' count with cancellations and make the treatment effect uninterpretable."
- *"Isn't estimated date a weak benchmark?"* → "Yes — it's a platform-set target, not ground truth, and could itself be gamed. I flag that as a limitation and add an 'estimated-date drift' guardrail in the experiment design."
- *"Why is delivery_days only secondary?"* → "The business question is a binary service promise (on-time yes/no); delivery_days is a continuous companion metric but noisier and right-skewed."

**Danger zone:** Don't claim `on_time` measures overall order success — it's conditional on delivery.

---

## Decision 3 — Unit of analysis = one row per `order_id`

**Decision:** Build `orders_analytical` at order grain and verify `COUNT(*) = COUNT(DISTINCT order_id) = 99,441`.

**One-line answer to own:** "The policy question is about per-order delivery performance, so the mart is one row per order — and I verified the grain so joins didn't silently duplicate orders."

**Actual code (grain check):**
```sql
SELECT
    COUNT(*) AS n_rows,
    COUNT(DISTINCT order_id) AS n_distinct_orders,
    COUNT(*) = COUNT(DISTINCT order_id) AS grain_ok
FROM orders_analytical
```

**Why this choice:** `on_time` is defined per order, and DiD compares group×period on-time rates. If the grain were wrong (e.g., item-level), a multi-item order would count multiple times and distort every rate. `orders` is the clean spine (unique `order_id`, 0 dupes); fanout tables get aggregated before joining.

**Follow-ups:**
- *"What breaks if grain is wrong?"* → "Orders with more items get overweighted in the on-time rate, so the mean is no longer a per-order rate and the DiD contrast is biased by basket-size composition."
- *"Why order grain and not state-week?"* → "For the observational DiD, I resample and regress at order level; state-week becomes the unit in the *experiment design* because that's the operational randomization unit. Different purposes."
- *"How did you confirm no fanout?"* → "Grain check plus a fanout sanity check on `n_items` (median 1, max 21) — plausible, not exploded."

**Danger zone:** Don't conflate the order-level analysis grain with the state-week randomization unit in Week 4 — they're intentionally different.

---

## Decision 4 — Treated = SP/RJ/MG from 2017-06-01

**Decision:** Treat the three highest-volume states from a fixed cutoff of 2017-06-01; everyone else is control.

**One-line answer to own:** "I picked the top-three volume states to mimic an ops rollout in high-demand hubs, and a mid-2017 cutoff that leaves ~8 months of pre-period with real volume in both arms."

**Actual code:** see Decision 1 view. Verification:
```sql
SELECT treated_region, post, COUNT(*) AS n_orders
FROM orders_treated
GROUP BY treated_region, post
ORDER BY 1, 2;
-- control pre 4,188 / post 29,020 ; treated pre 7,507 / post 58,726
```

**Why this choice:** SP (41.7K), RJ (12.9K), MG (11.6K) are the top-3 by volume — a realistic "roll out in the biggest markets first" scenario. The cutoff sits where both arms have non-trivial pre volume; Olist scaled rapidly so post dominates. The date is admittedly somewhat arbitrary, which is exactly why I sensitivity-test it (Decision 12).

**Follow-ups:**
- *"Isn't picking the biggest states cherry-picking?"* → "It's a deliberate selection that mirrors ops reality, but it's also the project's main threat: hub states differ structurally, so I document it via the DAG (W path) and balance table, and it motivates randomization." (See Part 3, Decision 17.)
- *"Why does `treated_region` matter pre-cutoff if `incentive_flag`=0 for everyone then?"* → "Because DiD needs both arms to exist in the pre-period to estimate each arm's baseline trend; `treated_region` labels the arm, `incentive_flag` marks when the simulated policy switches on."
- *"Why one cutoff and not a staggered rollout?"* → "Single cutoff keeps the 2×2 clean for a portfolio piece; staggered adoption (e.g., Callaway–Sant'Anna) is a natural extension I'd mention."

**Danger zone:** Don't defend the states/cutoff as "optimal" — defend them as realistic and sensitivity-tested.

---

## Decision 5 — DiD as the estimand

**Decision:** Identify the effect with difference-in-differences: (treated post − treated pre) − (control post − control pre).

**One-line answer to own:** "DiD differences out any time-invariant gap between hub and non-hub states and any common time shock, isolating the *extra* change in treated states after the cutoff — valid if parallel trends hold."

**Actual code (hand DiD):**
```python
did_hand = (T_post - T_pre) - (C_post - C_pre)
# Treated: pre=0.964 post=0.937 ; Control: pre=0.952 post=0.911 ; DiD = +0.013
```

**Why this choice:** The setup is a panel with a before/after policy date and a treated/control split — the textbook DiD structure. Treated states have a persistent level advantage (the W backdoor path), and DiD's double-difference removes any *constant* level gap (δ) and any *common* time trend (λ_shared), leaving τ̂. It's more honest than a raw post-only comparison and simpler/more transparent than synthetic control given only 3 treated units (see Part 3, Decision 19).

**Follow-ups:**
- *"What exactly does DiD assume?"* → "Parallel trends: absent the rollout, treated and control on-time rates would have moved in parallel. Level differences are fine; differential *trends* are not."
- *"Plug in your numbers."* → "(0.937−0.964) − (0.911−0.952) = (−0.027) − (−0.041) = +0.013."
- *"Why is a level gap OK but a trend gap not?"* → "The first difference within each arm removes any constant gap; only a difference in *slopes* survives differencing and biases τ̂."

**Danger zone:** Don't call DiD causal unconditionally — it's causal *only if* parallel trends hold, which is untestable.

---

## Decision 6 — Substantive read of τ̂ = +1.3 pp (relative, not absolute)

**Decision:** Interpret the positive DiD as treated states declining *less*, not improving.

**One-line answer to own:** "Both arms got worse after the cutoff — control fell ~4 pp, treated ~2.7 pp — so the +1.3 pp is a smaller decline in treated states, not an absolute improvement."

**Actual code (2×2 means):**
```python
# pivot of AVG(on_time) by treated_region × post (delivered only)
#            pre     post
# control  0.9515  0.9114
# treated  0.9641  0.9373
```

**Why this choice:** Reading DiD as "treated improved" is the most common and most damaging misinterpretation. Treated on-time went 96.4% → 93.7% — that's *down*. DiD captures the treated–control gap in *changes*, which is positive only because control fell further. Honest framing is what an ops PM actually needs.

**Follow-ups:**
- *"Should we launch? First sentence?"* → "No — not on this alone. The signal is that incentives are associated with *resilience* (smaller decline), but treated states still got worse and the design is observational."
- *"Treated went 96.4→93.7 — is that a win?"* → "In absolute terms, no. Relative to a control that fell more, it's a positive contrast worth testing."
- *"+1.3 pp sounds tiny."* → "It's modest and I say so; whether it's worth the incentive cost is a business call, which is why the experiment powers for a 2 pp *business-meaningful* bar."

**Danger zone:** Never say "incentives improved on-time" without "relative to control / smaller decline."

---

## Decision 7 — Parallel trends judgment: "partially plausible"

**Decision:** Assess parallel trends with pre-period monthly on-time plots and call them partially plausible, not clean.

**One-line answer to own:** "Pre-cutoff, treated sits slightly above control (a level gap, which is fine), but the slopes are shaky in thin early months, so I call parallel trends partially plausible and report τ̂ with that caveat."

**Actual code (monthly series):**
```python
monthly = con.sql("""
    SELECT purchase_month,
    CASE WHEN treated_region = 1 THEN 'treated' ELSE 'control' END AS arm,
    COUNT(*) AS n, ROUND(AVG(on_time), 3) AS on_time_rate
    FROM orders_treated
    WHERE is_delivered = TRUE
    GROUP BY 1, 2 ORDER BY 1, 2;
""").df()
# then pre-only plot (month <= cutoff) and full-window plot with cutoff line
```

**Why this choice:** Parallel trends is the identifying assumption, so it deserves an explicit, honest verdict. The pre-only plot shows a stable level gap (δ, expected from W) but wobbly slopes — control drops sharply Jan–Mar 2017 while treated is flatter, and some months have tiny n (Sep 2016 treated n=1). No sustained one-directional divergence, but not clean parallelism either.

**Follow-ups:**
- *"Balance table looked fine — why isn't that parallel trends?"* → "Balance checks *levels* at a point in time (δ); parallel trends checks *slopes* over time (λ). You can be balanced on levels and still trend differently." (See Part 2, Decision 10.)
- *"Your pre-trends look bad — why trust the DiD?"* → "I don't claim they're clean. I report the caveat, show cutoff robustness, and use it to argue for the randomized pilot that removes the assumption."
- *"What would you do if trends clearly diverged?"* → "Down-weight the DiD, consider an event-study/pre-trend test, or restrict to a matched control subset — and lean harder on the experiment."

**Danger zone:** Don't say "parallel trends holds/is proven." Say "partially plausible; cannot be proven from pre-period alone."

---

## Decision 8 — Bootstrap 95% CI, resampling orders (N=1,000)

**Decision:** Quantify uncertainty on τ̂ by resampling orders with replacement 1,000 times and taking the 2.5/97.5 percentiles.

**One-line answer to own:** "I bootstrapped at the order level, 1,000 reps, to get a non-parametric 95% CI on the DiD — [0.40, 2.17] pp — which excludes zero and matches the OLS interaction CI."

**Actual code:**
```python
def did_estimate(data, cutoff=None):
    d = data.copy()
    if cutoff is not None:
        d["post"] = (pd.to_datetime(d["purchase_date"]) >= pd.Timestamp(cutoff)).astype(int)
    means = d.groupby(["treated_region", "post"])["on_time"].mean().unstack()
    return (means.loc[1,1] - means.loc[1,0]) - (means.loc[0,1] - means.loc[0,0])

N_BOOT = 1000
rng = np.random.default_rng(42)
boot_dids = [did_estimate(df_boot.sample(n=len(df_boot), replace=True, random_state=rng))
             for _ in range(N_BOOT)]
ci_low, ci_high = np.percentile(boot_dids, [2.5, 97.5])
```

**Why this choice:** Bootstrap makes no normality assumption and directly reflects sampling variability of the DiD statistic. It's a good complement to OLS SEs and reinforces the result when both agree.

**Follow-ups:**
- *"What is being resampled?"* → "Individual delivered orders, with replacement; each resample recomputes the full 2×2 DiD."
- *"Why bootstrap if OLS gives a p-value?"* → "Cross-check with fewer assumptions; agreement builds confidence. But both assume independent orders — which is the weak point."
- *"Would clustering change it?"* → "Yes, and I actually tested it — see Part 3, Decision 18: clustering by state widens the CI dramatically and it stops excluding zero, because there are only 3 treated clusters."

**Danger zone:** Don't present the order-level CI as the final word on uncertainty — flag that it assumes i.i.d. orders and is optimistic (Part 3 quantifies how much).

---

*Continue to Part 2 (`INTERVIEW_DEFENSE_PART2.md`) for Tier 2 decisions 9–15.*
