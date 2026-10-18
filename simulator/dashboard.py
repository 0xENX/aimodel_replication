"""Bridge between the Economy Model dashboard (model.html) and the aimodel package.

The dashboard runs this file in the browser with Pyodide. It uses the book's model unchanged:
the same parameter draws (analysis/montecarlo.draw), the same paired runs with and without AI,
and the same policies (analysis/policy.POLICIES). Results are percentiles of the paired
differences, year by year, returned as JSON.
"""
import json
import sys
import types

import numpy as np

# montecarlo.py imports SALib for the Sobol analysis, which is not available in the browser.
# The dashboard only needs draw(), so empty modules stand in for SALib.
for _name in ("SALib", "SALib.sample", "SALib.analyze"):
    sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["SALib.sample"].sobol = None
sys.modules["SALib.analyze"].sobol = None

from aimodel.calibration.data import PRIORS, START_YEAR, END_YEAR  # noqa: E402
from aimodel.analysis.montecarlo import draw  # noqa: E402
from aimodel.analysis.policy import POLICIES  # noqa: E402
from aimodel.core.economy import simulate  # noqa: E402

YEARS = list(range(START_YEAR, END_YEAR + 1))
INDICATORS = ("gdp", "unemp_adv", "unemp_eme", "unemp_lic", "labshare", "b50", "m40", "t10",
              "debt_adv", "debt_eme", "debt_lic")


def _series(ai, base):
    """Paired differences for every year and draw, arrays of shape (years, draws).
    Same definitions as analysis/metrics.py."""
    out = {"gdp": (ai["Y"].sum(2) / base["Y"].sum(2) - 1) * 100}
    for r, rn in enumerate(("adv", "eme", "lic")):
        out["unemp_" + rn] = (ai["unemp"][:, :, r] - base["unemp"][:, :, r]) * 100
        out["debt_" + rn] = (ai["debt_ratio"][:, :, r] - base["debt_ratio"][:, :, r]) * 100

    def labshare(o):
        return (o["labshare"] * o["Y"]).sum(2) / o["Y"].sum(2)

    out["labshare"] = (labshare(ai) - labshare(base)) * 100
    for g, name in enumerate(("b50", "m40", "t10")):
        out[name] = (ai["Cg"][:, :, :, g].sum(2) / base["Cg"][:, :, :, g].sum(2) - 1) * 100
    return out


def _params(n, seed, fixed):
    p = draw(n, seed)
    for k, v in fixed.items():
        p[k] = np.full(n, float(v))
    return p


def priors():
    return json.dumps({k: [lo, hi, note] for k, (lo, hi, note) in PRIORS.items()})


def policy_names():
    return json.dumps(list(POLICIES))


def run(n, seed, fixed_json, policy_name):
    """Monte Carlo of paired runs; percentiles 5, 25, 50, 75, 95 for every indicator and year."""
    p = _params(int(n), int(seed), json.loads(fixed_json))
    base = simulate(p, ai=False)
    pol = POLICIES.get(policy_name) or None
    ai = simulate(p, policy=pol, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    s = _series(ai, base)
    q = {k: np.percentile(s[k], [5, 25, 50, 75, 95], axis=1).round(4).tolist() for k in INDICATORS}
    return json.dumps({"years": YEARS, "q": q, "n": int(n),
                       "residual": float(np.abs(ai["residual"]).max())})


def policies(n, seed, fixed_json, year):
    """Median results of every policy in the book for one year, against the no-AI world."""
    p = _params(int(n), int(seed), json.loads(fixed_json))
    base = simulate(p, ai=False)
    ti = int(year) - START_YEAR
    rows = []
    for name, pol in POLICIES.items():
        o = simulate(p, policy=pol or None, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
        s = _series(o, base)
        row = {"name": name}
        for k in ("gdp", "unemp_adv", "b50", "t10", "debt_adv"):
            row[k] = float(np.median(s[k][ti]))
        rows.append(row)
    return json.dumps(rows)
