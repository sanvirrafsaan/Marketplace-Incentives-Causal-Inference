# Olist Causal Inference — Interview Defense (Part 3 of 3)

> Tier 3 decisions (16–20): the deeper "gaps I need to reason through live." Decision 18 contains a **real, freshly-run** state-clustered bootstrap result (not a caveat).

---

# TIER 3 — Deeper reasoning / gaps to own

---

## Decision 16 — Why THIS intervention (a regional delivery/logistics incentive)?

**Decision:** Simulate a regional surge/logistics incentive whose causal target is on-time delivery.

**One-line answer to own:** "A regional logistics incentive — surge pay or priority routing for carriers in high-demand states — is a real lever marketplaces pull, and it plausibly moves on-time delivery by adding capacity exactly where congestion causes lateness."

**Business logic (the lever → outcome mechanism):**
- On-time misses are largely a **capacity/congestion** problem: in high-volume regions, carriers and fulfillment are stretched, so orders slip past the estimated date.
- A **surge incentive** (bonus pay, priority handling, subsidized freight) increases effective delivery capacity / prioritization in the targeted region.
- More capacity where congestion binds → fewer late deliveries → higher on-time rate.
- It's **regional** because ops budgets and carrier contracts are managed by geography, and demand hot-spots are regional (SP/RJ/MG).

**Why it's a plausible real-world policy:** Uber/DoorDash/Lyft use geo-temporal surge to rebalance supply; an e-commerce marketplace subsidizing carriers in congested states is the logistics analog. It's operationally deployable (toggle by region), measurable (on-time rate), and has a clear cost lever (incentive spend).

**Follow-ups:**
- *"Why would an incentive change delivery speed at all?"* → "It reallocates scarce carrier capacity toward the incentivized region and raises prioritization of those shipments; the binding constraint in hubs is capacity, not distance."
- *"Could it backfire?"* → "Yes — cost blowout, or gaming (widening estimated windows instead of delivering faster). Both are guardrails in the design."
- *"Why on-time and not delivery_days?"* → "On-time maps to the customer promise and to an ops SLA; delivery_days is a noisier continuous companion."

**Danger zone:** Don't assert the mechanism is proven in the data — it's the *hypothesized* causal pathway motivating the (simulated) treatment.

---

## Decision 17 — The honest limitation of SP/RJ/MG as "treated" (hub-state structural confounding)

**Decision:** Acknowledge that treated = the three largest hub states risks capturing "being a hub" rather than a clean treatment effect — beyond the common-shock risk already flagged.

**One-line answer to own:** "My treated group is the three biggest economic hubs, so there's a real risk the DiD partly reflects hub-specific dynamics — different growth, infrastructure investment, or seasonality — rather than the simulated incentive; that's the deepest threat and the main reason I want randomization."

**Grounding in my actual data:**
- Balance table: treated deliver ~11 days vs control ~17 days pre-cutoff — treated states are structurally faster/better-resourced (the **W** path), not just different by noise.
- RJ is heterogeneous within the treated arm (~88% on-time vs SP/MG ~95%), so τ̂ is a **volume-weighted average** dominated by SP (41.7K orders).
- Post-period is when Olist scaled fastest; hub states may have absorbed that growth differently than smaller states.

**Is the risk beyond the common-shock (S) issue?** Yes. Common shocks hit both arms and are partly differenced out. Hub-structural confounding is worse because it can create **differential trends** (λ) — e.g., hubs getting logistics investment or scaling capacity on a different slope than rural states — which DiD does *not* remove and parallel-trends plots can't fully rule out over just ~8 months.

**Follow-ups:**
- *"So is your DiD just measuring 'hub-ness'?"* → "Partly possibly, yes. DiD removes the constant hub advantage, but if hubs were on a *different trajectory*, that leaks into τ̂. I can't fully exclude it — which is exactly why I don't recommend launching on it."
- *"How would you reduce this threat without an experiment?"* → "Restrict control to a matched subset of mid-size states with similar pre-trends, add an event-study to inspect pre-trend slopes, or use synthetic control weights (limited by only 3 treated units)."
- *"Does weighting by volume bother you?"* → "Yes — τ̂ is really 'the effect in SP, mostly.' I'd report state-level estimates if powered, and the pilot stratifies by volume tier."

**Danger zone:** Don't wave this away as 'handled by DiD.' DiD handles the *level* gap, not differential hub *trends*.

---

## Decision 18 — Clustering by STATE instead of resampling orders (REAL RESULT)

**Decision:** Test how the CI changes when the resampling/error unit is the **state** (cluster) rather than the individual order. **This was run — real numbers below, not a caveat.**

**One-line answer to own:** "When I honor within-state correlation by bootstrapping whole states, the 95% CI explodes from ~1.6 pp wide to ~9 pp wide and now *includes zero* — because I effectively have only 3 treated clusters, so my order-level CI was overconfident."

**Actual code (run against `data/olist.db`, N=2,000, seed=42):**
```python
# Stratified pairs cluster bootstrap: resample states WITH replacement
# within each arm (3 treated, 24 control), recompute DiD each rep.
treated_states = ['MG','RJ','SP']            # only 3 clusters
control_states = [...]                        # 24 clusters
for _ in range(N):
    tt = rng.choice(treated_states, size=3,  replace=True)
    cc = rng.choice(control_states, size=24, replace=True)
    samp = pd.concat([groups[s] for s in list(tt)+list(cc)])
    dids.append(did_estimate(samp))
```

**Real results:**

| Method | Resampling unit | 95% CI (pp) | Width | Excludes 0? |
|---|---|---|---|---|
| Week 3 (reported) | order | [0.40, 2.17] | ~1.8 pp | Yes |
| Re-run order bootstrap | order | [0.53, 2.16] | 1.63 pp | Yes |
| Pairs cluster (all 27) | state | [−5.47, 4.27] | 9.74 pp | **No** |
| Stratified cluster (3 vs 24) | state | [−4.70, 4.20] | 8.90 pp | **No** |

Point estimate stays ~1.3 pp (stratified median 1.36 pp); it's the **uncertainty** that changes.

**Why this happens:** Orders within a state share logistics infrastructure (the W path), so they're not independent. Treating 96,470 orders as independent overstates the effective sample. Once you resample at the state level, the treated arm has only **3 clusters** — so a couple of states (especially SP) drive everything, and the DiD swings wildly across resamples. This is the classic **"few treated clusters"** problem in DiD inference (Cameron & Miller; wild cluster bootstrap is the recommended fix for so few clusters).

**Follow-ups:**
- *"Which CI is 'right'?"* → "Neither is perfect. Order-level is too optimistic (ignores clustering); naive state-cluster is too unstable (only 3 treated clusters). The honest statement: with 3 treated states I cannot make a precise cluster-robust claim — that's a core motivation for the randomized pilot with many state-weeks."
- *"Does this kill your result?"* → "It kills any claim of statistical significance at the *state* level. The +1.3 pp direction survives; the certainty does not. I'd rather say that than hide behind the narrow order-level CI."
- *"What's the proper method here?"* → "Wild cluster bootstrap-t (Cameron–Gelbach–Miller), or designing for more clusters — which is exactly what state-week randomization buys."

**Danger zone:** Do NOT quote only the order-level [0.40, 2.17] CI as if uncertainty is settled. Lead with: order-level is optimistic; state-clustered includes zero; few-treated-clusters limits inference.

---

## Decision 19 — Why DiD and not synthetic control or regression discontinuity?

**Decision:** Choose DiD over synthetic control (SCM) and regression discontinuity (RDD) given the setup.

**One-line answer to own:** "DiD fits because I have a clear before/after and a treated/control split with panel structure; RDD doesn't apply (no running-variable threshold), and synthetic control is shaky with 3 treated units and only ~8 pre-months."

**Comparison grounded in my setup:**

| Method | Needs | My setup | Verdict |
|---|---|---|---|
| **DiD** | Pre/post + treated/control panel, parallel trends | Yes: cutoff + 3 treated / 24 control | **Best fit** |
| **RDD** | A continuous running variable with a treatment threshold | My cutoff is a *date*, not a per-unit score; treatment is regional, not threshold-assigned | Doesn't apply |
| **Synthetic control** | Long, stable pre-period to build a weighted donor control; few treated units OK (usually 1) | Only ~8 pre-months (thin, noisy); 3 treated states, not 1 | Poor fit / fragile |

**Why specifically DiD given group sizes:** DiD is transparent and stable with a modest pre-period and a multi-unit treated group. SCM shines for *one* treated unit with a *long* pre-period to fit donor weights — I have the opposite (3 treated units, short pre-window), so donor-weight fitting would be unstable. RDD needs assignment based on crossing a cutoff in a continuous score, which my design doesn't have.

**Follow-ups:**
- *"Could you frame a date cutoff as RDD in time?"* → "Regression-discontinuity-in-time exists, but it identifies effects *at the boundary* under smoothness assumptions and is very sensitive to bandwidth; with monthly seasonality and a platform-wide shock, it's weaker than DiD here."
- *"When would you switch to synthetic control?"* → "If I had one treated state and 2–3 years of clean pre-period, SCM would build a better counterfactual than a raw control average."
- *"Staggered adoption?"* → "If states adopted at different times, I'd use Callaway–Sant'Anna or Sun–Abraham instead of two-way fixed effects."

**Danger zone:** Don't claim DiD is universally superior — it's the best *fit for this setup*; name the specific reasons (panel + short pre-period + multi-unit treated).

---

## Decision 20 — SUTVA / spillover risk in the ORIGINAL DiD (not just the pilot)

**Decision:** Acknowledge that cross-region spillover could violate SUTVA in the observational DiD itself, not only in the proposed experiment.

**One-line answer to own:** "SUTVA assumes control states are unaffected by treated-state treatment — but sellers ship across states and carriers share national capacity, so a simulated incentive in SP/RJ/MG could plausibly move control outcomes too, which would bias my DiD."

**Mechanism specific to a two-sided marketplace:**
- **Seller-side:** many sellers are physically in SP and ship *nationwide*. An incentive that changes SP seller/carrier behavior affects orders delivered to control states → control is "partially treated."
- **Carrier-side:** national logistics providers have finite capacity. Prioritizing treated regions can **pull capacity away** from control regions (negative spillover) — making control look worse and *inflating* the DiD.
- Either way, the control arm is no longer a clean counterfactual, violating the "no interference between units" part of SUTVA.

**Does it bias the ORIGINAL analysis?** Potentially yes. This isn't only a pilot-design risk. If treated incentives degrade control on-time (capacity reallocation), the treated−control gap widens for a reason unrelated to the treated units' own improvement — so τ̂ could be **overstated**. In this project the treatment is *simulated*, so there's no literal mechanism operating in the historical data — but the point is that **if** this were a real rollout structured this way, SUTVA would be a live threat, and I should not assume clean non-interference.

**Follow-ups:**
- *"Direction of the bias?"* → "If treated pulls capacity from control (negative spillover to control), the DiD is biased upward — treated looks better partly because control got worse."
- *"How would you detect it?"* → "Look at control states bordering/served-by treated hubs vs distant control states; differential control degradation near treated regions signals spillover. Monitor cross-state seller mix."
- *"How does the pilot handle it?"* → "State-week clustering, buffer/border-state monitoring, and cross-state seller-mix tracking — but spillover is fundamentally hard to eliminate in a shared national network, which I state as a limitation."

**Danger zone:** Don't claim SUTVA holds. Say the simulated design *assumes* no interference, but a real version would risk cross-region spillover that could bias τ̂ upward.

---

## Quick-reference: numbers to never get wrong

| Quantity | Value |
|---|---|
| Total orders / mart grain | 99,441 / 1 row per order_id |
| DiD sample (delivered, non-null) | 96,470 |
| τ̂ (DiD) | +1.34 pp (hand = OLS interaction) |
| Order-level bootstrap 95% CI | [0.40, 2.17] pp (excludes 0) |
| **State-clustered 95% CI (real, run)** | **~[−4.7, 4.3] pp (includes 0), ~9 pp wide** |
| Pre/post treated | 96.4% → 93.7% (−2.7 pp) |
| Pre/post control | 95.2% → 91.1% (−4.0 pp) |
| Cutoff sensitivity ±14d | 0.88–1.51 pp |
| Balance delivery_days | treated 11.0 vs control 16.9 |
| Treated clusters | only 3 (SP, RJ, MG) |
| Power design | state-week, 2 pp MDE, Cohen's h=0.074, DEFF=1.44, 184 clusters, ~8,180 orders, ~7 weeks |

**The single most impressive honest line you can deliver:** "My order-level bootstrap said [0.40, 2.17] pp, but when I re-ran it clustering by state the interval widened to about 9 points and crossed zero — because I really only have three treated clusters. So I trust the *direction*, not the precision, and that's exactly why my recommendation is a randomized pilot, not a launch."
