"""Three-region task-based model with stock-flow consistent demand and fiscal closure.

Production follows the task framework of Acemoglu and Restrepo (2018, 2019) with a unit
elasticity across tasks, so the labour share equals labour task content Gamma_L.
AI displaces labour from tasks (displacement), creates new labour tasks with a lag
(reinstatement) and raises productivity by the cost saving on automated tasks
(Acemoglu 2025: dTFP = GDP share of automated tasks x cost saving), plus a gain on
augmented (complementary) tasks.

Demand closure: output is the minimum of supply and effective demand. Effective demand
is consumption (group-specific propensities out of disposable income) + investment
(responding to the profit share) + government purchases (incl. training). Every flow has a
sender and a receiver; the sectoral-balance identity
    S_households + S_firms + S_government + (income paid abroad - income received)
        = Y - aggregate demand
is evaluated every period and returned as `residual` (must be ~0 to machine precision).

All functions are vectorised over N parameter draws.
"""
import numpy as np
from aimodel.calibration.data import CAL, GROUP_POP, START_YEAR, END_YEAR

NR, NG = 3, 3


def _logistic(t, mid, k):
    return 1.0 / (1.0 + np.exp(-k * (t - mid)))


def adoption(t, theta, mid, k):
    """Share of substitutable exposed tasks automated at time t (zero in START_YEAR)."""
    f0 = _logistic(START_YEAR, mid, k)
    f = _logistic(t, mid, k)
    return np.where(t <= START_YEAR, 0.0, theta * (f - f0) / (1.0 - f0))


def labour_income_shares():
    """Group shares of labour income implied by income and wealth shares (pre-tax)."""
    lam = np.zeros((NR, NG))
    for r in range(NR):
        sl = CAL["labshare0"][r]
        lab = np.clip(CAL["inc_share"][r] - CAL["wealth_share"][r] * (1 - sl), 0.0, None)
        lam[r] = lab / lab.sum()
    return lam


LAMBDA = labour_income_shares()


def simulate(p, policy=None, ai=True, base_ratio=None, base_wage=None, ur_path=None):
    """Simulate 2026-2046 for N parameter draws.

    p: dict of arrays (N,) for every name in PRIORS.
    policy: dict of policy settings (see analysis/policy.py); None = status quo.
    ai: False sets automation to zero (counterfactual without the AI wave, same draw).
    base_ratio: demand/supply ratio path of the no-AI run (T, N, NR). The no-AI world is
        assumed to run at potential (monetary policy closes its gaps); AI-induced demand
        shortfalls are measured relative to it. None with ai=False -> util = 1.
    base_wage: wage path of the paired no-AI run (T, N, NR); switches labour demand to the
        technology-and-output rule with elasticity eps (version 2).
    ur_path: optional unemployment path (T, N, NR) that replaces the macro rate after the
        labour-market step. It feeds the wage Phillips term and unemployment benefits, the two
        channels through which unemployment enters the macro model. Used by core/coupled.py to
        close the loop with the age module. None (default) leaves results unchanged.
    """
    policy = policy or {}
    N = np.asarray(p["theta"]).shape[0]
    years = np.arange(START_YEAR, END_YEAR + 1)
    T = len(years)
    theta = np.asarray(p["theta"], dtype=float) * (1.0 if ai else 0.0)
    mids = np.stack([p["mid_adv"], p["mid_adv"] + p["lag_eme"], p["mid_adv"] + p["lag_lic"]])
    mids = mids + policy.get("slow_rollout", 0.0)
    psi = np.clip(p["psi"] + policy.get("psi_add", 0.0), 0.0, 1.2)
    lag_new = np.clip(p["lag_new"] - policy.get("lag_cut", 0.0), 0.5, None)
    rent_share = np.clip(p["rent_share"] + policy.get("rent_share_add", 0.0), 0.0, 0.9)
    zeta = p["zeta"] * policy.get("zeta_mult", 1.0)
    tauK_add = policy.get("tauK_add", 0.0)
    div_frac = policy.get("ai_dividend", 0.0)
    cov = np.asarray(policy.get("ub_cov", CAL["ub_cov"]))
    rep = np.asarray(policy.get("ub_rep", CAL["ub_rep"]))
    train_cost = policy.get("train_cost", 0.0)

    sl0, rev, mix, apc = CAL["labshare0"], CAL["rev_gdp"], CAL["rev_mix"], CAL["apc"]
    exposure, phi = CAL["exposure"], np.asarray(p["phi_s"])[:, None]
    u_star, ret = CAL["u_star"], CAL["retained"]
    Ys0 = 100.0 * CAL["gdp_share"]
    tauL = rev * mix[:, 0] / sl0
    tauK = rev * mix[:, 1] / (1 - sl0)
    tK_sq = tauK
    r_real = CAL["r_real"] + np.asarray(p["dr"])[:, None]

    Ys = np.tile(Ys0, (N, 1))
    LS = np.ones((N, NR))
    pop = np.ones((N, NR))
    GamL = np.tile(sl0, (N, 1))
    GamL_n = GamL.copy()
    wealth = np.tile((CAL["wealth_share"] * (CAL["k_y"] * Ys0)[:, None])[None], (N, 1, 1))
    debt = np.tile(CAL["debt0"] * Ys0, (N, 1))
    pens_share = np.tile(CAL["pension0"], (N, 1))
    w = np.tile(sl0 * Ys0 / (1 - u_star), (N, 1))
    ur = np.tile(u_star, (N, 1)).astype(float)
    UB = CAL["ub_rep"] * CAL["ub_cov"] * w * LS * ur          # 2026: status-quo benefits
    a_prev = np.zeros((N, NR))
    alag_prev = np.zeros((N, NR))

    keys = ["Y", "Ys", "util", "labshare", "unemp", "debt_ratio", "primary", "profit_share",
            "C_real", "residual", "excess_demand", "dd_ratio", "adopt", "pop", "train", "transfers_policy", "ldem", "lsup", "wage"]  # ldem: labour demand at the current wage; lsup: labour supply
    out = {k: np.zeros((T, N, NR)) for k in keys}
    out["Cg"] = np.zeros((T, N, NR, NG))

    for ti, t in enumerate(years):
        # ---- technology and labour supply ------------------------------------------
        a = np.stack([adoption(t, theta, mids[r], p["k_slope"]) for r in range(NR)], axis=1)
        alag = np.stack([adoption(t - lag_new, theta, mids[r], p["k_slope"]) for r in range(NR)], axis=1)
        # exposure widens over time with capabilities and robotics (exp_mult by END_YEAR)
        def expo(tt):
            gr = np.clip((tt - START_YEAR) / (END_YEAR - START_YEAR), 0.0, None)[..., None] if np.ndim(tt) else np.clip((tt - START_YEAR) / (END_YEAR - START_YEAR), 0.0, None)
            return np.minimum(0.95, exposure * (1 + (np.asarray(p["exp_mult"])[:, None] - 1) * gr))
        Ea, Ea_prev = expo(t) * a, expo(t - 1) * a_prev
        Elag, Elag_prev = expo(t - lag_new) * alag, expo(t - 1 - lag_new) * alag_prev
        delta_ai = phi * np.clip(Ea - Ea_prev, 0.0, None)
        rho_ai = psi[:, None] * phi * np.clip(Elag - Elag_prev, 0.0, None)
        if ti > 0:
            ls_g = CAL["ls_g_start"] + (CAL["ls_g_end"] - CAL["ls_g_start"]) * ti / (T - 1)
            pi_s = np.asarray(p["pi_save"])[:, None]
            g_ai = (GamL * delta_ai * pi_s
                    + np.asarray(p["mu"])[:, None] * (1 - phi) * np.clip(Ea - Ea_prev, 0.0, None) * GamL
                    + GamL * rho_ai * 0.5 * pi_s)
            Ys_prev_ls = Ys / LS
            Ys = Ys * (1 + CAL["g_base"] + g_ai)
            LS = LS * (1 + ls_g)
            pop = pop * (1 + ls_g)
            GamL = np.clip(GamL * (1 - np.asarray(p["d0"])[:, None] - delta_ai + rho_ai), 0.05, 0.95)
            GamL_n = GamL_n * (1 - np.asarray(p["d0"])[:, None])
            pens_share = pens_share + CAL["pension_drift"]
            # wage per unit of labour: trend + pass-through of excess productivity - Phillips term
            # trend output per worker without AI, and the matching wage trend: wages follow the
            # non-AI erosion of labour task content (d0), as the historical labour-share decline was
            # absorbed by wages growing below productivity, not by rising unemployment.
            g_trend = (1 + CAL["g_base"]) / (1 + ls_g) - 1
            g_wtrend = (1 + g_trend) * (1 - np.asarray(p["d0"])[:, None]) - 1
            g_pot = (Ys / LS) / Ys_prev_ls - 1
            w = w * (1 + g_wtrend + np.asarray(p["beta_w"])[:, None] * (g_pot - g_trend)
                     - np.asarray(p["kappa"])[:, None] * (ur - u_star))
        on = 1.0 if ti > 0 else 0.0                               # policies start in 2027
        tK = tK_sq + tauK_add * on
        ai_gap = np.clip(GamL_n - GamL, 0.0, None)
        if base_wage is not None:
            # labour demand from technology and output: tasks left to labour (GamL) times output,
            # at the no-AI wage wr, adjusted by the wage gap with elasticity eps
            wr = base_wage[ti]
            eps = np.asarray(p["eps"])[:, None]
            wage_gap = (w / wr) ** (1 - eps)              # labour income per unit of task content
            sL = GamL * wage_gap + rent_share[:, None] * ai_gap
        else:
            sL = GamL + rent_share[:, None] * ai_gap
        sK = 1 - sL
        P = pens_share * Ys
        train = train_cost * w * LS * delta_ai
        if ti == 0:
            G_share = (rev * Ys - P - UB - CAL["primary0"] * Ys) / Ys
        G = G_share * Ys
        interest = r_real * debt

        # ---- household income per unit of Y and fixed transfers --------------------
        wsh = wealth / wealth.sum(axis=2, keepdims=True)
        dist_k = (sK * (1 - tK) * (1 - ret))                                  # distributed profits / Y
        ai_dist = ai_gap * (1 - tK) * (1 - ret)                               # AI-induced part
        out_frac = np.zeros((N, NR))
        out_frac[:, 1:] = zeta[:, None] * ai_dist[:, 1:] * (1 - div_frac)     # paid abroad / Y
        recyc = tauK_add * on * sK                                            # recycled per head / Y
        dy = (LAMBDA[None] * (sL * (1 - tauL))[:, :, None]
              + wsh * (dist_k - div_frac * ai_dist - out_frac)[:, :, None]
              + (div_frac * ai_dist + recyc)[:, :, None] * GROUP_POP[None, None])
        tr = (P[:, :, None] * CAL["pension_dist"][None, None]
              + UB[:, :, None] * CAL["ub_dist"][None, None]
              + interest[:, :, None] * wsh)
        c_y = (apc[None] * dy).sum(axis=2)
        if ti == 0:
            sK0 = sK.copy()
            c_tr0 = (apc[None] * tr).sum(axis=2)
            tauC = rev * mix[:, 2] * Ys / (c_y * Ys + c_tr0)                   # tax per unit of spending
            I_share = ((1 - c_y * (1 - tauC)) * Ys - c_tr0 * (1 - tauC) - G - train) / Ys
        I = I_share * Ys * np.clip(sK / sK0, 0.2, 5.0) ** np.asarray(p["eta"])[:, None]

        # ---- effective demand: payers (EME, LIC) first, then ADV with inflows -------
        def solve(c_tr):
            Yd = (c_tr * (1 - tauC) + I + G + train) / (1 - c_y * (1 - tauC))
            ratio = Yd / Ys
            rel = ratio / base_ratio[ti] if base_ratio is not None else np.ones_like(ratio)
            util = np.where(rel < 1, rel ** np.asarray(p["nu"])[:, None], 1.0)
            return util * Ys, util, ratio
        c_tr = (apc[None] * tr).sum(axis=2)
        Y, util, ratio = solve(c_tr)
        inflow = (out_frac[:, 1:] * Y[:, 1:]).sum(axis=1)
        tr[:, 0, 2] += inflow
        c_tr = (apc[None] * tr).sum(axis=2)
        Y, util, ratio = solve(c_tr)

        # ---- labour market ----------------------------------------------------------
        W = sL * Y
        E_max = LS * (1 - u_star)
        if base_wage is not None:
            E_d = GamL * Y / wr * (w / wr) ** (-eps)
            # labour shortage: the wage rises until demand equals supply (applies from next year)
            w = np.where(E_d > E_max, wr * (GamL * Y / (wr * E_max)) ** (1 / eps), w)
        else:
            E_d = W / w
            w = np.where(E_d > E_max, W / E_max, w)
        E = np.minimum(E_d, E_max)
        out["ldem"][ti], out["lsup"][ti], out["wage"][ti] = E_d, LS, w
        ur = 1 - E / LS if ur_path is None else np.asarray(ur_path[ti], dtype=float)

        # ---- incomes, consumption, saving, wealth -----------------------------------
        Ydg = dy * Y[:, :, None] + tr
        Cspend = apc[None] * Ydg
        Creal = Cspend * (1 - tauC)[:, :, None]
        S_h = (Ydg - Cspend).sum(axis=2)
        retained = sK * (1 - tK) * ret * Y
        wealth = np.clip(wealth + (Ydg - Cspend) + retained[:, :, None] * wsh, 1e-6, None)

        # ---- government ------------------------------------------------------------
        revenue = tauL * W + tK * sK * Y + tauC * Cspend.sum(axis=2)
        spend = G + P + UB + recyc * Y + train
        primary = revenue - spend
        debt = debt + interest - primary

        # ---- accounting identity ----------------------------------------------------
        AD = Creal.sum(axis=2) + I + G + train
        paid_abroad = out_frac * Y
        received = np.zeros((N, NR)); received[:, 0] = inflow
        S_f = retained - I
        S_g = primary - interest
        resid = (S_h + S_f + S_g + paid_abroad - received) - (Y - AD)

        UB = rep * cov * w * LS * ur          # paid next period (benefits lag one year)
        a_prev, alag_prev = a, alag

        out["Y"][ti], out["Ys"][ti], out["util"][ti] = Y, Ys, util
        out["labshare"][ti], out["unemp"][ti] = sL, ur
        out["debt_ratio"][ti], out["primary"][ti] = debt / Y, primary / Y
        out["profit_share"][ti] = sK * util
        out["C_real"][ti], out["Cg"][ti] = Creal.sum(axis=2), Creal
        out["residual"][ti] = resid / Y
        out["excess_demand"][ti] = (AD - Y) / Y
        out["dd_ratio"][ti] = ratio
        out["adopt"][ti], out["pop"][ti] = a, pop
        out["train"][ti] = train / Y
        out["transfers_policy"][ti] = (recyc * Y + div_frac * ai_dist * Y) / Y
    out["years"] = years
    return out
