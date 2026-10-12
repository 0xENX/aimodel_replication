"""Annual age-cohort labour market, driven by the macro model's demand path.

One-way satellite: age employment does NOT feed back into GDP, wages, tax,
income groups or debt. Macro results must not be presented as age-adjusted.
All new defaults are assumptions. Units: initial regional labour force = 1.
States: employed, first-job search, previous-worker search, discouraged first
searchers and discouraged previous workers. Single-year ages 15..64 age annually.
Demand denotes accessible age-segment job capacity, not actual employment.
"""
import json
from pathlib import Path
import numpy as np
from aimodel.calibration.data import CAL


def load_config(path=None):
    path = Path(path) if path else Path(__file__).resolve().parents[2] / "config" / "employment.json"
    c = json.loads(path.read_text(encoding="utf-8"))
    if c["regions"] != ["ADV", "EME", "LIC"] or c["bands"] != [[15, 24], [25, 34], [35, 49], [50, 64]]:
        raise ValueError("Supported axes: ADV/EME/LIC and four bands covering ages 15..64")
    for name in ("population_shares", "participation"):
        a = np.asarray(c[name], float)
        if a.shape != (3, 4) or not np.isfinite(a).all() or (a < 0).any() or (a > 1).any():
            raise ValueError(f"Invalid {name}")
    if not np.allclose(np.sum(c["population_shares"], axis=1), 1):
        raise ValueError("Population shares must sum to one per region")
    if (np.asarray(c["participation"]) <= 0).any():
        raise ValueError("Participation must be positive")
    for name in ("first_search_share", "turnover", "first_hire_probability", "rehire_probability",
                 "return_probability", "discouragement_probability"):
        a = np.asarray(c[name], float)
        if a.shape != (4,) or not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
            raise ValueError(f"Invalid probability: {name}")
    for name in ("unemployment_relative", "age_exposure_relative"):
        a = np.asarray(c[name], float)
        if a.shape != (4,) or not np.isfinite(a).all() or (a <= 0).any():
            raise ValueError(f"Invalid {name}")
    if len(c["cohort_entry_growth"]) != 3 or min(c["cohort_entry_growth"]) <= -1:
        raise ValueError("Invalid cohort entry growth")
    lo, hi = c["matching_draw_range"]
    if not 0 < lo <= hi:
        raise ValueError("Invalid matching draw range")
    for sc in c["scenarios"].values():
        if sc["matching_scale"] <= 0 or not 0 <= sc["entry_barrier"] <= 1:
            raise ValueError("Invalid matching scale or entry barrier")
        if not 0 <= sc["mismatch"] <= 1 or not 0 <= sc["discouragement_add"] <= 1:
            raise ValueError("Invalid mismatch or discouragement")
    for name in ("population_single_age", "participation_single_age"):
        if name in c:
            a = np.asarray(c[name], float)
            if a.shape != (3, 50) or not np.isfinite(a).all() or (a <= 0).any():
                raise ValueError(f"Invalid {name}")
            if name == "population_single_age" and not np.allclose(a.sum(-1), 1):
                raise ValueError("Single-year population shares must sum to one")
            if name == "participation_single_age" and (a > 1).any():
                raise ValueError("Participation exceeds one")
    if "hire_hazard_scale" in c:
        a = np.asarray(c["hire_hazard_scale"], float)
        if a.shape != (3,) or not np.isfinite(a).all() or (a <= 0).any():
            raise ValueError("Invalid hire_hazard_scale")
    if "unemployment_relative_by_region" in c:
        a = np.asarray(c["unemployment_relative_by_region"], float)
        if a.shape != (3, 4) or not np.isfinite(a).all() or (a <= 0).any():
            raise ValueError("Invalid regional unemployment profile")
    return c


def _expand(values, widths=(10, 10, 15, 15)):
    return np.repeat(np.asarray(values, float), widths, axis=-1)


def _bands(a):
    return np.stack([a[..., :10].sum(-1), a[..., 10:20].sum(-1),
                     a[..., 20:35].sum(-1), a[..., 35:].sum(-1)], axis=-1)


def _age(a):
    b = np.zeros_like(a)
    b[..., 1:] = a[..., :-1]
    return b


def simulate_employment(macro, config, scenario, matching_draw=None, ai=True, policy=None):
    """Return (year, draw, region, age-band) stocks, annual flows and rates.

    Demand total equals macro ldem. Its age allocation weights baseline potential
    supply by exp(-entry_barrier * cumulative_adoption * relative_exposure).
    Allocation is an assumption about accessibility, NOT measured vacancies by age.
    Matching failure leaves both vacancies and unemployment. Discouragement moves
    searchers out of the active labour force; broad non-employment remains visible.

    policy (optional, used by the entry-policy experiments; None leaves results unchanged):
      "demand_scale": (T, N, R) multiplier on macro demand in persons (shorter hours);
      "extra_demand": (T, N, R) additional job capacity from 2027 (public jobs, net hiring-credit jobs);
      "extra_band_weights": four weights, one per age band, for where the extra capacity goes.
    The macro model is not changed by these policies: costs are reported separately.
    """
    T, N, R = macro["lsup"].shape
    sc = config["scenarios"][scenario]
    policy = policy or {}
    dscale = None if policy.get("demand_scale") is None else np.asarray(policy["demand_scale"], float)
    dadd = None if policy.get("extra_demand") is None else np.asarray(policy["extra_demand"], float)
    add_weights = _expand(policy.get("extra_band_weights", [1, 1, 1, 1]))[None, None]
    q = np.ones((N, 1, 1)) if matching_draw is None else np.asarray(matching_draw).reshape(N, 1, 1)
    shares = np.asarray(config["population_shares"])
    part = np.asarray(config.get("participation_single_age", _expand(config["participation"])))[None]
    pop0 = np.asarray(config.get("population_single_age", _expand(shares / np.array([10, 10, 15, 15]))))[None]
    pop0 = pop0 / (pop0 * part).sum(-1, keepdims=True)
    pop = np.broadcast_to(pop0, (N, R, 50)).copy()
    potential = pop * part
    relative = (_expand(config["unemployment_relative_by_region"])[None]
                if "unemployment_relative_by_region" in config
                else _expand(config["unemployment_relative"])[None, None])
    u = CAL["u_star"][None, :, None] * relative / (potential * relative).sum(-1, keepdims=True)
    if (u >= 1).any():
        raise ValueError("Initial unemployment profile exceeds 100%")
    E = potential * (1 - u)
    first_share = _expand(config["first_search_share"])[None, None]
    F, U = potential * u * first_share, potential * u * (1 - first_share)
    DF, DU = np.zeros_like(E), np.zeros_like(E)
    exposures = _expand(config["age_exposure_relative"])[None, None]
    turnover = _expand(config["turnover"])[None, None]
    # Consistency calibration (calibrate_consistency.py): one factor per region on both hire
    # hazards, chosen so that the no-AI reference world stays at the macro structural rate.
    hazard_scale = np.asarray(config.get("hire_hazard_scale", [1.0, 1.0, 1.0]), float)[None, :, None]
    first_hazard = _expand(config["first_hire_probability"])[None, None] * hazard_scale
    rehire_hazard = _expand(config["rehire_probability"])[None, None] * hazard_scale
    return_hazard = _expand(config["return_probability"])[None, None]
    discourage_hazard = _expand(config["discouragement_probability"])[None, None]
    keys = ["population", "potential_supply", "supply", "demand", "employed", "unemployed",
            "discouraged", "first_searchers", "hires", "first_hires", "rehires", "separations",
            "job_cuts", "age65_exits", "participation_exits", "vacancies", "searcher_returns",
            "discouragement_flow", "rehire_eligible", "first_hire_eligible", "employment_rate",
            "unemployment_rate", "participation_rate", "inactivity_rate", "broad_nonemployment",
            "gap_rate", "gap_potential", "rehire_rate", "first_hire_rate", "hire_rate"]
    out = {k: np.zeros((T, N, R, 4)) for k in keys}
    residual_max = 0.0
    for t in range(T):
        zero = np.zeros_like(E)
        hires = first_hires = rehires = sep = cuts = exits = returns = disc_flow = zero
        age65 = np.zeros((N, R, 4))
        if t:
            age65[..., 3] = E[..., -1]
            # Uniform within initial bands; exact single-year cohort movement thereafter.
            pop = _age(pop)
            entrants = pop0[..., 0] * (1 + np.asarray(config["cohort_entry_growth"])[None]) ** t
            pop[..., 0] = entrants
            # Disclosed demographic residual: rescale all cohorts to v2 potential LF.
            pop *= (macro["lsup"][t] / (pop * part).sum(-1))[..., None]
            potential = pop * part
            E, F, U, DF, DU = (_age(x) for x in (E, F, U, DF, DU))
            aged_E = E.copy()
            exits = np.maximum(E - potential, 0)
            E = np.minimum(E, potential)
            # Reconcile cohort participation capacity without converting inactivity to jobs.
            remaining = potential - E
            old_pool = F + U + DF + DU
            scale = np.minimum(1, remaining / np.maximum(old_pool, 1e-15))
            F, U, DF, DU = (x * scale for x in (F, U, DF, DU))
            new_search = np.maximum(remaining - (F + U + DF + DU), 0)
            # Labour-force entrants are not necessarily first-ever job seekers.
            F += new_search * first_share
            U += new_search * (1 - first_share)
            rf, ru = DF * return_hazard, DU * return_hazard
            DF -= rf; DU -= ru; F += rf; U += ru
            returns = rf + ru
            sep = E * turnover
            E -= sep; U += sep
        adoption = macro["adopt"][t, ..., None] if ai else np.zeros((N, R, 1))
        # entry_barrier acts in TWO places by design: here it shifts accessible job capacity
        # away from the more exposed (younger) ages, and below it lowers the first-hire hazard.
        # Both channels are assumptions; their joint strength is what the scenarios vary.
        weights = potential * (1 - u) * np.exp(-sc["entry_barrier"] * adoption * exposures)
        ldem_t = macro["ldem"][t] if dscale is None else macro["ldem"][t] * dscale[t]
        demand = ldem_t[..., None] * weights / weights.sum(-1, keepdims=True)
        if dadd is not None and t:
            # policy jobs: extra capacity, allocated within targeted bands by potential supply
            target = potential * add_weights
            demand = demand + dadd[t][..., None] * target / np.maximum(target.sum(-1, keepdims=True), 1e-15)
        if t:
            cuts = np.maximum(E - demand, 0)
            E -= cuts; U += cuts
            preF, preU = F.copy(), U.copy()
            # Suppressed junior hiring and slower transfer of workers into new tasks.
            hF = np.clip(first_hazard * q * sc["matching_scale"] *
                         np.exp(-sc["entry_barrier"] * adoption * exposures), 0, 1)
            hU = np.clip(rehire_hazard * q * sc["matching_scale"] *
                         np.exp(-sc["mismatch"] * adoption * exposures), 0, 1)
            offersF, offersU = F * hF, U * hU
            fill = np.minimum(1, np.maximum(demand - E, 0) / np.maximum(offersF + offersU, 1e-15))
            first_hires, rehires = offersF * fill, offersU * fill
            hires = first_hires + rehires
            F -= first_hires; U -= rehires; E += hires
            dc = np.clip(discourage_hazard + sc["discouragement_add"] * adoption * exposures, 0, 1)
            df, du = F * dc, U * dc
            F -= df; U -= du; DF += df; DU += du
            disc_flow = df + du
            residual_max = max(residual_max, float(np.abs(E - (aged_E - exits - sep - cuts + hires)).max()))
        else:
            preF, preU = F.copy(), U.copy()
        unemployed, discouraged = F + U, DF + DU
        supply = E + unemployed
        stocks = dict(population=pop, potential_supply=potential, supply=supply,
                      demand=demand, employed=E, unemployed=unemployed, discouraged=discouraged,
                      first_searchers=F, hires=hires, first_hires=first_hires, rehires=rehires,
                      separations=sep, job_cuts=cuts, participation_exits=exits,
                      vacancies=np.maximum(demand-E, 0), searcher_returns=returns,
                      discouragement_flow=disc_flow, rehire_eligible=preU, first_hire_eligible=preF)
        for k, v in stocks.items():
            out[k][t] = _bands(v)
        out["age65_exits"][t] = age65
        P, L, Pot, Emp, Un = (out[k][t] for k in ("population", "supply", "potential_supply", "employed", "unemployed"))
        def pct(num, den):
            return 100 * num / np.maximum(den, 1e-15)
        out["employment_rate"][t] = pct(Emp, P)
        out["unemployment_rate"][t] = pct(Un, L)
        out["participation_rate"][t] = pct(L, P)
        out["inactivity_rate"][t] = pct(P-L, P)
        out["broad_nonemployment"][t] = pct(Pot-Emp, Pot)
        out["gap_rate"][t] = pct(L-out["demand"][t], L)
        out["gap_potential"][t] = pct(Pot-out["demand"][t], Pot)
        out["rehire_rate"][t] = pct(out["rehires"][t], out["rehire_eligible"][t]) if t else 0
        out["first_hire_rate"][t] = pct(out["first_hires"][t], out["first_hire_eligible"][t]) if t else 0
        out["hire_rate"][t] = pct(out["hires"][t], L)
        residual_max = max(residual_max, float(np.abs(potential - E-F-U-DF-DU).max()))
        if min(float(x.min()) for x in (E, F, U, DF, DU)) < -1e-12 or not np.isfinite(E).all():
            raise ArithmeticError("Invalid labour-market state")
        if t and (E > demand + 1e-12).any():
            raise ArithmeticError("Employment exceeds job capacity")
    out["years"] = macro["years"]
    out["max_stock_flow_residual"] = residual_max
    return out
