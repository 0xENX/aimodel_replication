"""Two-way link between the macro model and the age module ("the missing arrow").

In the one-way design the age module receives labour demand from economy.py but its
employment never returns to the macro model. Here the age module's non-employment rate
replaces the macro unemployment rate in the two places where unemployment enters the macro
model: the wage Phillips term and unemployment benefits. Demand, wages and benefits then
change, the age module is run again, and the loop is repeated until the unemployment path
stops changing (fixed point over whole trajectories).

Both paired worlds are coupled in the same way, so the AI effect is still measured within
each pair. The rate passed back is 1 - employed / potential labour force, the same
definition the macro model uses (it has no separate discouraged state): discouraged
searchers therefore still count as slack for wages and for benefit costs. This is an
assumption, documented in FONTI_E_METODO.md.
"""
import numpy as np
from aimodel.core.economy import simulate
from aimodel.core.employment import simulate_employment


def age_unemployment(emp, macro):
    """Regional non-employment rate from the age module, macro definition (T, N, R)."""
    return 1.0 - emp["employed"].sum(-1) / macro["lsup"]


def _fixed_point(run_macro, run_age, max_iter, tol):
    macro = run_macro(None)
    emp = run_age(macro)
    ur = age_unemployment(emp, macro)
    for it in range(1, max_iter + 1):
        macro = run_macro(ur)
        emp = run_age(macro)
        new = age_unemployment(emp, macro)
        change = float(np.abs(new - ur).max())
        ur = new
        if change < tol:
            return macro, emp, dict(iterations=it, max_change=change, converged=True)
    return macro, emp, dict(iterations=max_iter, max_change=change, converged=False)


def coupled_pair(p, config, scenario, matching_draw=None, policy=None, max_iter=60, tol=1e-9):
    """Coupled no-AI and AI runs for one scenario. Returns dict with both worlds and diagnostics."""
    base, emp_b, info_b = _fixed_point(
        lambda ur: simulate(p, ai=False, ur_path=ur),
        lambda m: simulate_employment(m, config, scenario, matching_draw, ai=False),
        max_iter, tol)
    ai, emp_a, info_a = _fixed_point(
        lambda ur: simulate(p, policy=policy, ai=True, base_ratio=base["dd_ratio"],
                            base_wage=base["wage"], ur_path=ur),
        lambda m: simulate_employment(m, config, scenario, matching_draw, ai=True),
        max_iter, tol)
    return dict(base=base, ai=ai, emp_base=emp_b, emp_ai=emp_a, info_base=info_b, info_ai=info_a)
