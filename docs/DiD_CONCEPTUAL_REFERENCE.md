# DiD Conceptual Reference — Backdoor Paths, do-calculus, and Parallel Trends

Paste this into Cursor when you need the conceptual grounding for the Olist DiD project.
This is a reference document, not a task prompt. Use it to check your understanding
or ask the mentor to drill you on specific parts.

---

## My DAG for this project

```
W (State_Infrastructure) → T (incentive_flag)
W (State_Infrastructure) → O (on_time)
T (incentive_flag) → O (on_time)
```

### Joint distribution factorization (from DAG structure)

```
P(O, T, W) = P(O | T, W) · P(T | W) · P(W)
```

- **O's parents:** T and W
- **T's parent:** W
- **W's parents:** none

---

## Why P(O | T) ≠ P(O | do(T))

### The observational quantity P(O | T)

Marginalize out W using total probability:

```
P(O | T) = Σ_w P(O | T, W=w) · P(W=w | T)
```

The problem is **P(W | T)**. Because W causes T in the DAG, W and T are NOT independent.
`P(W | T=1) ≠ P(W)` — the infrastructure distribution among treated states (SP, RJ, MG)
is different from the infrastructure distribution across all states.

So `P(O | T=1)` mixes the true causal effect of T with the W differences that come
along with being in a treated state. The backdoor path is doing damage.

### The interventional quantity P(O | do(T))

`do(T=1)` means: intervene and SET T=1 for everyone, regardless of W.

Formally: delete all arrows INTO T in the DAG. The mutilated DAG becomes:

```
W → O          (W still affects outcome directly)
T → O          (T is now set externally, not caused by W)
W → T  ← DELETED
```

Now W and T are independent. The interventional distribution is:

```
P(O | do(T=1)) = Σ_w P(O | T=1, W=w) · P(W=w)
```

**Key difference from observational:** the last term is `P(W)` not `P(W | T)`.
You average over the NATURAL distribution of W, not the distribution of W
among treated units.

### Why they differ

| Quantity | Weight on W | Interpretation |
|---|---|---|
| `P(O \| T=1)` | `P(W \| T=1)` | Infrastructure distribution of treated states only (biased) |
| `P(O \| do(T=1))` | `P(W)` | Infrastructure distribution across ALL states (unbiased) |

The gap between them is the **backdoor bias** — the part of the observed T–O association
that comes from W causing both T and O, not from T actually causing O.

---

## What a backdoor path is

A backdoor path is any path from T to O that starts with an arrow **INTO** T —
i.e., goes against the causal direction at T.

In this DAG: **T ← W → O** is the backdoor path.

It's the **fork structure** (common cause): W causes both T and O.
This is exactly what you learned as the "common cause" DAG structure.
In causal inference it's just called a backdoor path because it enters T from behind.

---

## The backdoor criterion and adjustment formula

To recover `P(O | do(T))` from observational data, block all backdoor paths by
conditioning on a set of variables Z such that:

1. No variable in Z is a descendant of T
2. Z blocks every path between T and O that has an arrow pointing INTO T

In this DAG: conditioning on W blocks the backdoor path T ← W → O
(it's a fork — conditioning on the common cause W blocks the T–O association through W).

This gives the **adjustment formula**:

```
P(O | do(T)) = Σ_w P(O | T, W=w) · P(W=w)
```

Condition on W within strata, then re-weight by the marginal distribution of W.
This is what matching and regression adjustment do.

---

## How DiD recovers the causal effect WITHOUT conditioning on W

DiD exploits a specific structure: **W is TIME-INVARIANT**.

Write W's effect on O as a fixed additive term δ (the infrastructure effect).

Write out the four DiD cells:

```
E[O | T=1, post] = τ + δ_treated + λ_treated
E[O | T=1, pre]  =     δ_treated
E[O | T=0, post] =     δ_control + λ_control
E[O | T=0, pre]  =     δ_control
```

Where:

- **τ** = true causal effect of the incentive (what we want)
- **δ_treated** = time-invariant infrastructure baseline of treated states (SP, RJ, MG)
- **δ_control** = time-invariant infrastructure baseline of control states
- **λ** = time trend (seasonality, platform-wide changes) — assumed equal across groups

DiD estimate:

```
= (E[O|T=1,post] − E[O|T=1,pre]) − (E[O|T=0,post] − E[O|T=0,pre])
```

Substituting:

```
= (τ + δ_treated + λ − δ_treated) − (δ_control + λ − δ_control)
= (τ + λ) − (λ)
= τ
```

The infrastructure terms δ cancel **within** each group's difference.
The time trend λ cancels **across** groups.
What's left is τ — the causal effect.

DiD recovers `P(O | do(T))` not by conditioning on W (adjustment formula route)
but by using the **TIME DIMENSION** to difference W out.
It works BECAUSE W is time-invariant — its contribution to the backdoor path
is identical in pre and post periods, so it cancels.

---

## Why the RJ baseline gap (87.9% vs 95.5%) is NOT a parallel trends problem

RJ having 87.9% on-time vs SP/MG at ~95.5% is a **LEVEL difference** — a difference in δ.

DiD differences that out automatically. The δ_treated term captures this level difference
and it cancels when you subtract pre from post within the treated group.

What **WOULD** threaten parallel trends: if RJ's on-time rate was **TRENDING DIFFERENTLY**
from control states before June 2017 — declining while control states were stable.
That's a **trajectory problem** (λ_treated ≠ λ_control), not a level problem.

| Check | What it captures |
|---|---|
| **Balance table (Phase 3)** | Level differences (δ) |
| **Parallel trends plot (Week 3)** | Trajectory differences (λ) |

These are two different checks. Don't conflate them.

---

## Parallel trends in do-calculus language

Parallel trends is the assumption that no **TIME-VARYING** backdoor path opened up
at the cutoff. Formally: **λ_treated = λ_control**.

If a new confounder hits only the treated states at June 2017 — e.g., SP gets a
separate government logistics investment at the exact same time as the simulated
incentive — then λ_treated ≠ λ_control and the cancellation breaks:

```
DiD = τ + (λ_treated − λ_control)  ← biased, not just τ
```

You cannot observe the counterfactual. But showing that pre-period trajectories
ran parallel is evidence that λ was historically the same for both groups,
making it plausible it would have continued absent the incentive.

**You CAN'T PROVE parallel trends. You can only provide supporting evidence.**
Always say this in interviews.

---

## One-sentence summary for interviews

> "DiD recovers the causal effect by differencing out time-invariant backdoor paths —
> the infrastructure level difference between treated and control states cancels when
> you subtract each group's pre-period from its post-period. Parallel trends is the
> assumption that no time-varying confounder opened a new backdoor path exactly at
> the cutoff, which I check by plotting pre-period trajectories."

---

## Interview trap: "why not just condition on W instead of doing DiD?"

Two reasons:

1. You may not be able to measure W fully — state infrastructure is a latent variable
   with many components you can't all observe and condition on.
2. Even if you could, DiD also removes time trends λ that affect both groups equally,
   which pure conditioning doesn't handle.

DiD is more powerful when W is time-invariant because it handles both the level
confounder AND the common time trend in one step.

---

*Generated June 23, 2026. Numbers (87.9%, 95.5%, 99,441 orders) are from
`notebooks/01_data_ingestion.ipynb` — do not use any other numbers.*
