"""Outcome metrics comparing the AI run with the paired no-AI run (same parameter draw)."""
import numpy as np
from aimodel.calibration.data import CAL, GROUP_POP, START_YEAR

POP_W = CAL["pop_share"]


def _ti(year):
    return year - START_YEAR


def group_ratio(ai, base, year, group, region=None, theta=None, omega=None):
    """Real consumption per head of an income group, AI run / no-AI run - 1 (in %).
    region=None aggregates the same group across the three regions (population-weighted).
    omega/theta: if given, adds unmeasured welfare omega * (adoption / theta)."""
    ti = _ti(year)
    rs = range(3) if region is None else [region]
    num = 0.0
    den = 0.0
    for r in rs:
        c_ai = ai["Cg"][ti, :, r, group]
        c_b = base["Cg"][ti, :, r, group]
        if omega is not None:
            frac = np.where(theta > 0, ai["adopt"][ti, :, r] / np.maximum(theta, 1e-9), 0.0)
            c_ai = c_ai * (1 + omega * frac)
        num = num + c_ai
        den = den + c_b
    return (num / den - 1) * 100


def world_gdp_ratio(ai, base, year):
    ti = _ti(year)
    return (ai["Y"][ti].sum(axis=1) / base["Y"][ti].sum(axis=1) - 1) * 100


def world_labshare(o, year):
    ti = _ti(year)
    return (o["labshare"][ti] * o["Y"][ti]).sum(axis=1) / o["Y"][ti].sum(axis=1)


def metrics(p, ai, base):
    th = np.asarray(p["theta"])
    m = {}
    for y in (2031, 2036, 2041, 2046):
        m[f"gdp_{y}"] = world_gdp_ratio(ai, base, y)
        for g, name in enumerate(["b50", "m40", "t10"]):
            m[f"{name}_{y}"] = group_ratio(ai, base, y, g)
            m[f"{name}_adv_{y}"] = group_ratio(ai, base, y, g, region=0)
            m[f"{name}_eme_{y}"] = group_ratio(ai, base, y, g, region=1)
            m[f"{name}_lic_{y}"] = group_ratio(ai, base, y, g, region=2)
        m[f"b50w_{y}"] = group_ratio(ai, base, y, 0, theta=th, omega=np.asarray(p["omega"]))
        m[f"m40w_{y}"] = group_ratio(ai, base, y, 1, theta=th, omega=np.asarray(p["omega"]))
        m[f"labshare_{y}"] = (world_labshare(ai, y) - world_labshare(base, y)) * 100
        ti = _ti(y)
        for r, rn in enumerate(["adv", "eme", "lic"]):
            m[f"unemp_{rn}_{y}"] = (ai["unemp"][ti, :, r] - base["unemp"][ti, :, r]) * 100
            m[f"debt_{rn}_{y}"] = (ai["debt_ratio"][ti, :, r] - base["debt_ratio"][ti, :, r]) * 100
            m[f"util_{rn}_{y}"] = ai["util"][ti, :, r]
        m[f"profit_{y}"] = ((ai["profit_share"][ti] * ai["Y"][ti]).sum(1) / ai["Y"][ti].sum(1)
                            - (base["profit_share"][ti] * base["Y"][ti]).sum(1) / base["Y"][ti].sum(1)) * 100
    return m
