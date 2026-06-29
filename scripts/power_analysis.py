"""Power analysis for cluster-randomized state-week incentive experiment.

Assumptions documented in docs/04_experiment_design.md §5.
Cluster size (m) from notebook 03 feasibility Query B.
"""

from __future__ import annotations
import math

import numpy as np
from statsmodels.stats.power import NormalIndPower

# --- Assumptions ---
P0 = 0.911  # Week 3 control post on-time rate (delivered orders)
MDE = 0.02  # absolute lift to detect (2 pp)
P1 = P0 + MDE
ALPHA = 0.05
POWER = 0.80
RATIO = 1.0  # 1:1 treated : control

# From notebook 03 Query B (orders_analytical, delivered only)
M_ORDERS_PER_CLUSTER = 44.8
ICC = 0.01  # conservative placeholder; orders within state-week correlated

# Olist-scale sanity check (historical data span)
N_STATES = 27
WEEKS_OLIST_SPAN = 104  # ~2 years


def cohens_h(p1: float, p2: float) -> float:
    """Effect size for two proportions (Cohen's h)."""
    return 2 * (np.arcsin(np.sqrt(p2)) - np.arcsin(np.sqrt(p1)))


def main() -> None:
    h = cohens_h(P0, P1)
    power = NormalIndPower()

    n_per_arm_simple = power.solve_power(
        effect_size=h,
        alpha=ALPHA,
        power=POWER,
        ratio=RATIO,
        alternative="two-sided",
    )

    deff = 1 + (M_ORDERS_PER_CLUSTER - 1) * ICC
    n_per_arm_adjusted = n_per_arm_simple * deff
    clusters_per_arm = math.ceil(n_per_arm_adjusted / M_ORDERS_PER_CLUSTER)
    total_clusters = 2 * clusters_per_arm
    total_orders = int(n_per_arm_adjusted * 2)

    state_weeks_in_history = N_STATES * WEEKS_OLIST_SPAN
    weeks_if_all_states = math.ceil(total_clusters / N_STATES)

    print("=" * 60)
    print("POWER ANALYSIS — Regional surge incentive experiment")
    print("=" * 60)
    print(f"Baseline (control) on-time:      {P0:.1%}")
    print(f"MDE (absolute):                  {P0:.1%} → {P1:.1%} (+{MDE:.1%})")
    print(f"α (two-sided):                   {ALPHA}")
    print(f"Power (1 - β):                   {POWER}")
    print(f"Cohen's h:                       {h:.4f}")
    print(f"Avg orders per cluster (m):      {M_ORDERS_PER_CLUSTER}")
    print(f"ICC (assumed):                   {ICC}")
    print(f"Design effect (DEFF):            {deff:.2f}")
    print("-" * 60)
    print(f"n per arm (simple, independent): {n_per_arm_simple:,.0f} orders")
    print(f"n per arm (cluster-adjusted):    {n_per_arm_adjusted:,.0f} orders")
    print(f"Clusters per arm:                {clusters_per_arm:,} state-weeks")
    print(f"Total clusters:                  {total_clusters:,} state-weeks")
    print(f"Total orders (approx):           {total_orders:,}")
    print("-" * 60)
    print("Olist-scale sanity check (historical):")
    print(f"  State-weeks in ~2yr history:   {state_weeks_in_history:,}")
    print(f"  Weeks if all {N_STATES} states enroll: ~{weeks_if_all_states}")
    print(f"  Feasibility Query B clusters:  2,152 state-weeks total")
    print("=" * 60)


if __name__ == "__main__":
    main()
