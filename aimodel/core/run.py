"""Paired runs: the same parameter draw with and without the AI wave."""
from aimodel.core.economy import simulate


def paired(p, policy=None):
    base = simulate(p, ai=False)
    ai = simulate(p, policy=policy, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    nopol = ai if not policy else simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    return base, ai, nopol
