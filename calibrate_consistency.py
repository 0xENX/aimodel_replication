"""Consistency calibration of the age module: python calibrate_consistency.py [config].

The age module's hire hazards are assumptions. Left unscaled, its no-AI reference world
drifts above the macro model's structural unemployment rate u* (to about 7% in ADV by
2036), so the two models disagree before any AI effect. This script finds, for each
region, one factor on both hire hazards such that the no-AI reference world (central
parameters, matching draw 1) has mean active unemployment u* over 2027-2046.

It is a consistency condition between the two models, not an estimate from data. The
factor is written into the config as "hire_hazard_scale", with its provenance.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
from aimodel.calibration.data import CENTRAL, CAL
from aimodel.core.economy import simulate
from aimodel.core.employment import load_config, simulate_employment

ROOT = Path(__file__).resolve().parent


def mean_unemployment(config, scale, base):
    c = copy.deepcopy(config)
    c["hire_hazard_scale"] = list(scale)
    e = simulate_employment(base, c, "reference", ai=False)
    u = e["unemployed"].sum(-1) / e["supply"].sum(-1)          # (T, N, R)
    return u[1:].mean(axis=0)[0]                                # draw 0, per region


def calibrate(config, lo=0.5, hi=3.0, tol=1e-6):
    p = {k: np.full(1, v) for k, v in CENTRAL.items()}
    base = simulate(p, ai=False)
    lo, hi = np.full(3, lo), np.full(3, hi)
    if (mean_unemployment(config, hi, base) > CAL["u_star"]).any():
        raise ValueError("Structural rate not reachable within the search range")
    while (hi - lo).max() > tol:                                 # bisection, per region
        mid = (lo + hi) / 2
        above = mean_unemployment(config, mid, base) > CAL["u_star"]
        lo, hi = np.where(above, mid, lo), np.where(above, hi, mid)
    scale = (lo + hi) / 2
    return scale, mean_unemployment(config, scale, base)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", type=Path, default=ROOT / "config" / "employment_eu_proxy.json")
    args = ap.parse_args()
    raw = json.loads(args.config.read_text(encoding="utf-8"))
    raw.pop("hire_hazard_scale", None)
    load_config(args.config)                                     # validate before calibrating
    scale, achieved = calibrate(raw)
    raw["hire_hazard_scale"] = [round(float(s), 6) for s in scale]
    raw.setdefault("sources", {})["hire_hazard_scale"] = (
        "Consistency calibration (calibrate_consistency.py): per-region factor on first-hire and "
        "rehire hazards so that the no-AI reference world, central parameters, has mean active "
        "unemployment equal to the macro structural rate u* over 2027-2046. Not an empirical estimate.")
    args.config.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print("hire_hazard_scale", raw["hire_hazard_scale"], "achieved", np.round(achieved, 5), "target", CAL["u_star"])
