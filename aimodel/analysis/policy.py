"""Policy interventions evaluated on the same Monte Carlo draws as the status quo."""
import numpy as np
from aimodel.analysis.montecarlo import draw
from aimodel.core.economy import simulate
from aimodel.analysis.metrics import metrics

POLICIES = {
    "Status quo": {},
    "Capital income tax +5 pp, recycled per head": {"tauK_add": 0.05},
    "AI dividend fund (50% of AI-induced profits)": {"ai_dividend": 0.5},
    "Income support decoupled from work": {"ub_cov": [0.80, 0.50, 0.25], "ub_rep": [0.60, 0.50, 0.40]},
    "Retraining and new-task creation": {"psi_add": 0.15, "lag_cut": 2.0, "train_cost": 0.20},
    "Bargaining and profit-sharing": {"rent_share_add": 0.20},
    "Slower rollout (+2 years)": {"slow_rollout": 2.0},
    "AI rents taxed where used": {"zeta_mult": 0.5},
    "Package: dividend + support + retraining + bargaining": {
        "ai_dividend": 0.5, "ub_cov": [0.80, 0.50, 0.25], "ub_rep": [0.60, 0.50, 0.40],
        "psi_add": 0.15, "lag_cut": 2.0, "train_cost": 0.20, "rent_share_add": 0.20},
    "Package + capital tax + rents taxed where used": {
        "ai_dividend": 0.5, "ub_cov": [0.80, 0.50, 0.25], "ub_rep": [0.60, 0.50, 0.40],
        "psi_add": 0.15, "lag_cut": 2.0, "train_cost": 0.20, "rent_share_add": 0.20,
        "tauK_add": 0.05, "zeta_mult": 0.5},
}


def world_primary(o, t0=4, t1=14):
    """GDP-weighted world primary balance, average 2030-2040 (% GDP)."""
    w = o["Y"][t0:t1 + 1]
    return ((o["primary"][t0:t1 + 1] * w).sum(axis=2) / w.sum(axis=2)).mean(axis=0) * 100


def evaluate(n=2000, seed=20261010):
    p = draw(n, seed)
    base = simulate(p, ai=False)
    sq = simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    res = {}
    for name, pol in POLICIES.items():
        o = sq if not pol else simulate(p, policy=pol, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
        bpol = base if not pol else simulate(p, policy=pol, ai=False)
        m = metrics(p, o, base)            # level: AI + policy vs no-AI without policy
        mr = metrics(p, o, bpol)           # AI impact under the same policy regime
        fiscal = world_primary(o) - world_primary(sq)
        debt46 = ((o["debt_ratio"][20] * o["Y"][20]).sum(1) / o["Y"][20].sum(1)
                  - (sq["debt_ratio"][20] * sq["Y"][20]).sum(1) / sq["Y"][20].sum(1)) * 100
        res[name] = {"m": m, "mr": mr, "fiscal_pb": fiscal, "debt46": debt46,
                     "resid": float(np.abs(o["residual"]).max())}
    return p, res
