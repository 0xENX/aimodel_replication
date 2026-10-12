"""Monte Carlo over the parameter priors and Sobol global sensitivity analysis."""
import numpy as np
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze
from aimodel.calibration.data import PRIORS, PARAM_NAMES
from aimodel.core.run import paired
from aimodel.analysis.metrics import metrics


def draw(n, seed=20261010):
    rng = np.random.default_rng(seed)
    return {k: rng.uniform(lo, hi, n) for k, (lo, hi, _) in PRIORS.items()}


def run_mc(n=4000, policy=None, seed=20261010):
    p = draw(n, seed)
    base, ai, _ = paired(p, policy)
    return p, base, ai, metrics(p, ai, base)


def summarize(x):
    q = np.percentile(x, [5, 25, 50, 75, 95])
    return {"p5": q[0], "p25": q[1], "median": q[2], "p75": q[3], "p95": q[4],
            "mean": float(np.mean(x)), "prob_neg": float(np.mean(x < 0))}


def run_sobol(n=1024, outputs=("b50_2036", "m40_2036", "gdp_2036", "unemp_adv_2036", "debt_adv_2046", "b50_2046"), seed=7):
    problem = {"num_vars": len(PARAM_NAMES), "names": PARAM_NAMES,
               "bounds": [[PRIORS[k][0], PRIORS[k][1]] for k in PARAM_NAMES]}
    X = sobol_sample.sample(problem, n, calc_second_order=False, seed=seed)
    p = {k: X[:, i] for i, k in enumerate(PARAM_NAMES)}
    base, ai, _ = paired(p)
    m = metrics(p, ai, base)
    res = {}
    for out in outputs:
        Si = sobol_analyze.analyze(problem, m[out], calc_second_order=False, seed=seed)
        res[out] = {"S1": dict(zip(PARAM_NAMES, Si["S1"])), "ST": dict(zip(PARAM_NAMES, Si["ST"])),
                    "ST_conf": dict(zip(PARAM_NAMES, Si["ST_conf"]))}
    return res, X.shape[0]
