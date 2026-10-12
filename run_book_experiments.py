"""New experiments for the book: python run_book_experiments.py [--draws 4000] [--only NAME ...]

feedback       the missing arrow: age-module unemployment fed back into the macro model (ch. 26)
entry          entry policies at equal cost on the age module (ch. 24)
age_sobol      global sensitivity of the age module's own assumptions (ch. 9)
priors         reinstatement up to full compensation; adoption and retraining that move together (ch. 12)

Results go to outputs/experiments/<name>.json. Existing outputs are not touched.
Every result is a difference between paired runs; percentiles describe the assumed parameter
draws, not statistical confidence intervals or probabilities of the future.
"""
import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from aimodel.calibration.data import PRIORS, CAL
from aimodel.core.economy import simulate
from aimodel.core.employment import load_config, simulate_employment
from aimodel.core.coupled import coupled_pair, age_unemployment
from aimodel.analysis.metrics import metrics

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "experiments"
CONFIG = ROOT / "config" / "employment_eu_proxy.json"
SEED = 20261010
T36, T46 = 10, 20
ADV, YOUNG, CORE = 0, 0, 1          # region index; age bands 15-24 and 25-34


def stats(x):
    x = np.asarray(x, float)
    q = np.percentile(x, [5, 50, 95])
    return dict(p5=round(float(q[0]), 4), median=round(float(q[1]), 4), p95=round(float(q[2]), 4),
                share_negative=round(float(np.mean(x < 0)), 4))


def provenance(n, extra=None):
    files = ["aimodel/core/economy.py", "aimodel/core/employment.py", "aimodel/core/coupled.py",
             "aimodel/calibration/data.py", "run_book_experiments.py", "config/employment_eu_proxy.json"]
    d = dict(draws=n, seed=SEED, sha256={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in files},
             note="Paired differences AI minus no-AI unless stated. Percentiles of assumed draws, not confidence intervals.")
    d.update(extra or {})
    return d


def draws(n, config):
    rng = np.random.default_rng(SEED)
    p0 = {k: rng.uniform(lo, hi, n) for k, (lo, hi, _) in PRIORS.items()}
    latent = {k: (p0[k] - lo) / (hi - lo) for k, (lo, hi, _) in PRIORS.items()}
    q = np.random.default_rng(SEED + 1).uniform(*config["matching_draw_range"], n)
    return p0, latent, q


def scenario_params(p0, latent, sc):
    p = {k: v.copy() for k, v in p0.items()}
    for k, (lo, hi) in sc["priors"].items():
        p[k] = lo + latent[k] * (hi - lo)
    return p


def save(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written", OUT / f"{name}.json")


# --------------------------------------------------------------------------- feedback (ch. 26)
def macro_block(p, ai, base):
    m = metrics(p, ai, base)
    wage = lambda t: 100 * (ai["wage"][t, :, ADV] / base["wage"][t, :, ADV] - 1)
    prim = lambda t: 100 * (ai["primary"][t, :, ADV] - base["primary"][t, :, ADV])
    return {"gdp_world_2036_pct": stats(m["gdp_2036"]), "gdp_world_2046_pct": stats(m["gdp_2046"]),
            "unemployment_adv_2036_pp": stats(m["unemp_adv_2036"]), "unemployment_adv_2046_pp": stats(m["unemp_adv_2046"]),
            "wage_adv_2036_pct": stats(wage(T36)), "wage_adv_2046_pct": stats(wage(T46)),
            "bottom50_world_2036_pct": stats(m["b50_2036"]), "bottom50_world_2046_pct": stats(m["b50_2046"]),
            "labour_share_world_2046_pp": stats(m["labshare_2046"]),
            "primary_balance_adv_2036_pp_gdp": stats(prim(T36)), "debt_adv_2046_pp_gdp": stats(m["debt_adv_2046"])}


def age_block(emp_a, emp_b, mac_a, mac_b):
    d = lambda k: emp_a[k] - emp_b[k]
    nonemp = 100 * (age_unemployment(emp_a, mac_a) - age_unemployment(emp_b, mac_b))
    return {"nonemployment_adv_2036_pp": stats(nonemp[T36, :, ADV]), "nonemployment_adv_2046_pp": stats(nonemp[T46, :, ADV]),
            "employment_rate_25_34_2036_pp": stats(d("employment_rate")[T36, :, ADV, CORE]),
            "employment_rate_25_34_2046_pp": stats(d("employment_rate")[T46, :, ADV, CORE]),
            "first_hire_rate_15_24_2036_pp": stats(d("first_hire_rate")[T36, :, ADV, YOUNG]),
            "noai_nonemployment_adv_2036_pct": stats(100 * age_unemployment(emp_b, mac_b)[T36, :, ADV])}


def exp_feedback(n):
    c = load_config(CONFIG)
    p0, latent, q = draws(n, c)
    base0 = simulate(p0, ai=False)
    res = {}
    for name, sc in c["scenarios"].items():
        p = scenario_params(p0, latent, sc)
        ai0 = simulate(p, ai=True, base_ratio=base0["dd_ratio"], base_wage=base0["wage"])
        eb0 = simulate_employment(base0, c, name, q, ai=False)
        ea0 = simulate_employment(ai0, c, name, q, ai=True)
        one_way = dict(macro=macro_block(p, ai0, base0), age=age_block(ea0, eb0, ai0, base0))
        del ai0, eb0, ea0; gc.collect()
        r = coupled_pair(p, c, name, q)
        two_way = dict(macro=macro_block(p, r["ai"], r["base"]), age=age_block(r["emp_ai"], r["emp_base"], r["ai"], r["base"]),
                       convergence=dict(no_ai=r["info_base"], ai=r["info_ai"]),
                       max_accounting_residual=float(max(np.abs(r["ai"]["residual"]).max(), np.abs(r["base"]["residual"]).max())))
        res[name] = dict(label=sc["label"], one_way=one_way, two_way=two_way)
        print(name, "two-way converged", r["info_base"]["converged"], r["info_ai"]["converged"],
              "unemp ADV 2036 one-way", one_way["macro"]["unemployment_adv_2036_pp"]["median"],
              "two-way", two_way["macro"]["unemployment_adv_2036_pp"]["median"])
        del r; gc.collect()
    save("feedback", dict(provenance=provenance(n, dict(
        rate_fed_back="1 - employed / potential labour force from the age module (discouraged count as slack)",
        channels="wage Phillips term and unemployment benefits")), scenarios=res))


# --------------------------------------------------------------------------- entry policies (ch. 24)
BUDGET = 0.007            # share of regional GDP per year from 2027: the cost of income support in the report
HIRING_SUBSIDY = 0.5      # share of the annual wage paid for each subsidised young worker (assumption)
DEADWEIGHT = (0.4, 0.8)   # share of subsidised jobs that would have existed anyway (assumption, drawn)
STW_REPLACEMENT = 0.6     # share of lost wages replaced in short-time work (German Kurzarbeitergeld basic rate)


def policy_inputs(kind, macro, deadweight):
    """Policy dict for simulate_employment at cost BUDGET x GDP in every region and year."""
    Y, w, sL = macro["Y"], macro["wage"], macro["labshare"]
    if kind == "public_jobs":
        return dict(extra_demand=BUDGET * Y / w, extra_band_weights=[1, 1, 1, 1])
    if kind == "youth_hiring_subsidy":
        subsidised = BUDGET * Y / (HIRING_SUBSIDY * w)
        return dict(extra_demand=(1 - deadweight)[None, :, None] * subsidised, extra_band_weights=[1, 1, 0, 0])
    if kind == "shorter_hours":
        hours_cut = BUDGET / (STW_REPLACEMENT * sL)                 # 1 - h, from the budget
        scale = 1 / (1 - hours_cut)
        scale[0] = 1.0                                                # policies start in 2027
        return dict(demand_scale=scale)
    raise ValueError(kind)


def exp_entry(n, scenarios=("reference", "slow")):
    c = load_config(CONFIG)
    p0, latent, q = draws(n, c)
    deadweight = np.random.default_rng(SEED + 2).uniform(*DEADWEIGHT, n)
    base = simulate(p0, ai=False)
    res = {}
    for name in scenarios:
        sc = c["scenarios"][name]
        p = scenario_params(p0, latent, sc)
        ai = simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
        sq_b = simulate_employment(base, c, name, q, ai=False)
        sq_a = simulate_employment(ai, c, name, q, ai=True)
        out = {"status_quo": age_block(sq_a, sq_b, ai, base)}
        for kind in ("public_jobs", "youth_hiring_subsidy", "shorter_hours"):
            pb, pa = policy_inputs(kind, base, deadweight), policy_inputs(kind, ai, deadweight)
            eb = simulate_employment(base, c, name, q, ai=False, policy=pb)
            ea = simulate_employment(ai, c, name, q, ai=True, policy=pa)
            vs_sq = lambda k, t, band: ea[k][t, :, ADV, band] - sq_a[k][t, :, ADV, band]
            jobs = (pa.get("extra_demand", 0 * ai["Y"]) / ai["lsup"])[T36, :, ADV] * 100
            block = dict(ai_impact_under_policy=age_block(ea, eb, ai, base),
                         policy_effect_in_ai_world=dict(
                             employment_rate_15_24_2036_pp=stats(vs_sq("employment_rate", T36, YOUNG)),
                             employment_rate_25_34_2036_pp=stats(vs_sq("employment_rate", T36, CORE)),
                             employment_rate_25_34_2046_pp=stats(vs_sq("employment_rate", T46, CORE)),
                             first_hire_rate_15_24_2036_pp=stats(vs_sq("first_hire_rate", T36, YOUNG)),
                             nonemployment_adv_2036_pp=stats(100 * (age_unemployment(ea, ai) - age_unemployment(sq_a, ai))[T36, :, ADV]),
                             unfilled_policy_capacity_share_2036=stats(
                                 (ea["vacancies"].sum(-1) / np.maximum(ea["demand"].sum(-1), 1e-12))[T36, :, ADV]
                                 - (sq_a["vacancies"].sum(-1) / np.maximum(sq_a["demand"].sum(-1), 1e-12))[T36, :, ADV])),
                         extra_capacity_adv_2036_pct_labour_force=stats(jobs))
            if kind == "shorter_hours":
                cut = 100 * BUDGET / (STW_REPLACEMENT * ai["labshare"][T36, :, ADV])
                block["hours_cut_adv_2036_pct"] = stats(cut)
                block["workers_income_loss_adv_2036_pct_of_labour_income"] = stats(cut * (1 - STW_REPLACEMENT))
            out[kind] = block
            del eb, ea; gc.collect()
        res[name] = out
        print(name, {k: v["policy_effect_in_ai_world"]["employment_rate_25_34_2036_pp"]["median"] for k, v in out.items() if k != "status_quo"})
        del ai, sq_a, sq_b; gc.collect()
    save("entry_policies", dict(provenance=provenance(n, dict(
        budget_share_of_gdp=BUDGET, hiring_subsidy_share_of_wage=HIRING_SUBSIDY, deadweight_range=DEADWEIGHT,
        short_time_work_replacement=STW_REPLACEMENT,
        design="All three policies cost the same share of GDP in every region from 2027 and apply in both worlds. "
               "One-way: costs are not fed back into the macro model.")), scenarios=res))


# --------------------------------------------------------------------------- age-module sensitivity (ch. 9)
AGE_FACTORS = {                      # ranges span the four scenarios of the config
    # matching_scale multiplies both hire hazards; it absorbs the per-draw matching factor
    # (scenario scale 0.65-1.2 times draw 0.8-1.2), so the draw is fixed at 1 here.
    "matching_scale": (0.5, 1.5), "entry_barrier": (0.0, 0.9), "mismatch": (0.0, 0.8),
    "discouragement_add": (0.0, 0.07)}


def _age_outputs(X, central_ai, central_base, c):
    n = X.shape[0]
    tile = lambda m: {k: (np.repeat(v, n, axis=1) if isinstance(v, np.ndarray) and v.ndim == 3 else v) for k, v in m.items()}
    a_m, b_m = tile(central_ai), tile(central_base)
    sc = {k: X[:, i].reshape(n, 1, 1) for i, k in enumerate(AGE_FACTORS)}
    cfg = dict(c); cfg["scenarios"] = {"grid": dict(label="grid", priors={}, **sc)}
    ea = simulate_employment(a_m, cfg, "grid", None, ai=True)
    eb = simulate_employment(b_m, cfg, "grid", None, ai=False)
    d = lambda k: ea[k] - eb[k]
    return {"employment_rate_25_34_2036": d("employment_rate")[T36, :, ADV, CORE],
            "employment_rate_25_34_2046": d("employment_rate")[T46, :, ADV, CORE],
            "first_hire_rate_15_24_2036": d("first_hire_rate")[T36, :, ADV, YOUNG],
            "broad_nonemployment_15_24_2036": d("broad_nonemployment")[T36, :, ADV, YOUNG]}


def exp_age_sobol(n_base=2048, chunk=4096):
    """Saltelli design with Jansen total-order and Saltelli first-order estimators (numpy only)."""
    c = load_config(CONFIG)
    from aimodel.calibration.data import CENTRAL
    p = {k: np.full(1, v) for k, v in CENTRAL.items()}
    base = simulate(p, ai=False)
    ai = simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    k = len(AGE_FACTORS)
    rng = np.random.default_rng(SEED + 3)
    lo = np.array([v[0] for v in AGE_FACTORS.values()]); hi = np.array([v[1] for v in AGE_FACTORS.values()])
    A = lo + rng.random((n_base, k)) * (hi - lo)
    B = lo + rng.random((n_base, k)) * (hi - lo)
    blocks = [A, B] + [np.where(np.arange(k) == i, B, A) for i in range(k)]   # AB_i: column i from B
    X = np.vstack(blocks)
    outs = {}
    for s in range(0, X.shape[0], chunk):
        part = _age_outputs(X[s:s + chunk], ai, base, c)
        for key, v in part.items():
            outs.setdefault(key, []).append(v)
        gc.collect()
    res = {}
    for key, parts in outs.items():
        y = np.concatenate(parts)
        fA, fB = y[:n_base], y[n_base:2 * n_base]
        var = np.var(np.concatenate([fA, fB]))
        idx = {}
        for i, name in enumerate(AGE_FACTORS):
            fABi = y[(2 + i) * n_base:(3 + i) * n_base]
            S1 = float(np.mean(fB * (fABi - fA)) / var)
            ST = float(0.5 * np.mean((fA - fABi) ** 2) / var)
            idx[name] = dict(first_order=round(S1, 4), total=round(ST, 4))
        res[key] = dict(indices=idx, median=round(float(np.median(fA)), 4), variance=round(float(var), 4))
    save("age_sobol", dict(provenance=provenance(n_base, dict(
        design=f"Saltelli, N={n_base}, {X.shape[0]} paired age runs; macro path fixed at central parameters",
        factors={k: list(v) for k, v in AGE_FACTORS.items()},
        estimators="first order: Saltelli (2010); total: Jansen (1999)")), outputs=res))


# --------------------------------------------------------------------------- prior experiments (ch. 12)
def _macro_summary(p):
    base = simulate(p, ai=False)
    ai = simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
    m = metrics(p, ai, base)
    keys = ["gdp_2036", "b50_2036", "b50_2046", "unemp_adv_2036", "unemp_adv_2046", "labshare_2046", "debt_adv_2046", "t10_2036"]
    return {k: stats(m[k]) for k in keys}


def _phi(z):
    return 0.5 * (1 + np.vectorize(math.erf)(z / math.sqrt(2)))


def exp_priors(n):
    rng = np.random.default_rng(SEED)
    p0 = {k: rng.uniform(lo, hi, n) for k, (lo, hi, _) in PRIORS.items()}
    latent = {k: (p0[k] - lo) / (hi - lo) for k, (lo, hi, _) in PRIORS.items()}
    res = {"baseline": _macro_summary(p0)}
    # (a) reinstatement range extended to full compensation and beyond (cap 1.2 as in the code)
    p = dict(p0); p["psi"] = 0.25 + latent["psi"] * (1.20 - 0.25)
    res["psi_0.25_1.20"] = _macro_summary(p)
    full = p["psi"] >= 1.0
    sub = {k: v[full] for k, v in p.items()}
    res["psi_at_least_1_subset"] = dict(share_of_draws=round(float(full.mean()), 4), **_macro_summary(sub))
    # (b) adoption timing and reinstatement speed move together (Gaussian copula on the latents)
    z = np.random.default_rng(SEED + 4).standard_normal((n, 3))
    for rho in (0.5, -0.5):
        # rho > 0: early adoption comes with fast retraining (short lag, high psi); rho < 0: the opposite
        cov = np.array([[1, rho, -rho], [rho, 1, -rho * rho], [-rho, -rho * rho, 1]])
        L = np.linalg.cholesky(cov)
        u = _phi(z @ L.T)
        p = dict(p0)
        for col, key in enumerate(("mid_adv", "lag_new", "psi")):
            lo, hi, _ = PRIORS[key]
            p[key] = lo + u[:, col] * (hi - lo)
        tag = "prepared" if rho > 0 else "unprepared"
        res[f"copula_rho_{rho:+.1f}_{tag}"] = _macro_summary(p)
    p = dict(p0)
    for col, key in enumerate(("mid_adv", "lag_new", "psi")):
        lo, hi, _ = PRIORS[key]
        p[key] = lo + _phi(z[:, col]) * (hi - lo)
    res["copula_rho_0_same_draws"] = _macro_summary(p)
    save("priors", dict(provenance=provenance(n, dict(
        note_copula="Spearman-type dependence via Gaussian copula on mid_adv, lag_new and psi; other priors independent. "
                    "rho>0: early adoption paired with short lags and high reinstatement ('prepared'); rho<0 the opposite. "
                    "rho=0 uses the same normal draws for a like-for-like comparison.")), results=res))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=4000)
    ap.add_argument("--sobol-base", type=int, default=2048)
    ap.add_argument("--only", nargs="*", default=["feedback", "entry", "age_sobol", "priors"])
    a = ap.parse_args()
    if "priors" in a.only: exp_priors(a.draws)
    if "age_sobol" in a.only: exp_age_sobol(a.sobol_base)
    if "entry" in a.only: exp_entry(a.draws)
    if "feedback" in a.only: exp_feedback(a.draws)
