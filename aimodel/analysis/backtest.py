"""Validation of the model against historical and external benchmarks.

1. Labour-share erosion: the non-AI drift d0 must reproduce observed labour-share declines.
   - ILO global labour income share: about 54.0% (2004) to 52.4% (2024), -1.6 pp.
   - Karabarbounis and Neiman (2014): global corporate labour share 64% (1975) to 59% (2012), -5 pp.
   - Acemoglu and Restrepo (2019): US task content of production -0.35%/yr, 1987-2017 (about -10%).
2. Fiscal path: the no-AI run must track IMF Fiscal Monitor (April 2026) debt projections for 2031
   (advanced 114.8, emerging 88.9, low-income 44.0 % of GDP).
3. Engels' pause (Allen 2009): with weak reinstatement the task model must be able to generate a
   period where output per worker grows while the labour share falls (Britain 1800-1830: output per
   worker +0.63%/yr, real wage 0.00%/yr).
4. Macro magnitude: the 10-year GDP effect is compared with published estimates (Acemoglu 2025:
   TFP gain at most 0.66% over 10 years).
"""
import numpy as np
from aimodel.calibration.data import PRIORS, CENTRAL
from aimodel.core.economy import simulate


def labour_share_tests():
    lo, hi = PRIORS["d0"][0], PRIORS["d0"][1]
    rows = []
    for name, s0, years, obs in [("ILO global 2004-2024", 54.0, 20, -1.6),
                                 ("Karabarbounis-Neiman global corporate 1975-2012", 64.0, 37, -5.0)]:
        pred_lo = s0 * ((1 - lo) ** years - 1)
        pred_hi = s0 * ((1 - hi) ** years - 1)
        implied = 1 - (1 + obs / s0) ** (1 / years)
        rows.append({"test": name, "observed_pp": obs, "model_range_pp": (round(pred_hi, 2), round(pred_lo, 2)),
                     "implied_d0": round(implied, 5), "inside_prior": lo <= implied <= hi})
    implied_us = 0.0035
    rows.append({"test": "Acemoglu-Restrepo US task content 1987-2017", "observed_pp": None,
                 "model_range_pp": None, "implied_d0": implied_us, "inside_prior": lo <= implied_us <= hi})
    return rows


def fiscal_test():
    p = {k: np.array([v]) for k, v in CENTRAL.items()}
    o = simulate(p, ai=False)
    ti = 2031 - 2026
    model = (o["debt_ratio"][ti, 0] * 100).round(1)
    imf = np.array([114.8, 88.9, 44.0])
    return {"model_2031": model.tolist(), "imf_2031": imf.tolist(), "diff_pp": (model - imf).round(1).tolist()}


def engels_pause_test():
    """Task-model arithmetic: with displacement d and reinstatement rho, the labour share changes by
    (rho - d)/yr; wages per worker grow by output-per-worker growth plus that change.
    Britain 1800-1830: output per worker +0.63%/yr and real wage 0.00%/yr imply a labour-share fall
    of about 0.63%/yr, i.e. net displacement d - rho ~ 0.6%/yr (close to Acemoglu-Restrepo's
    US manufacturing displacement of about 1.1%/yr in 1987-2017, without reinstatement)."""
    g_out, g_wage = 0.0063, 0.0
    net_disp = g_out - g_wage
    return {"required_net_displacement": round(net_disp, 4),
            "comparable_modern_value": "US manufacturing displacement about 1.1%/yr (AR 2019)",
            "share_fall_over_30y_pct": round(((1 - net_disp) ** 30 - 1) * 100, 1)}
