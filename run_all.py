"""Reproduce every number in the working paper.

Usage:  python run_all.py [--fast]
Writes outputs/headline.json, outputs/sobol.json, outputs/policy.json, outputs/backtest.json.
--fast skips the Sobol analysis (23,552 runs) and runs policies on 500 draws.
"""
import json, sys, time, os
import numpy as np
from aimodel.analysis.montecarlo import run_mc, summarize, run_sobol
from aimodel.analysis.backtest import labour_share_tests, fiscal_test, engels_pause_test
from aimodel.analysis.policy import evaluate

FAST = "--fast" in sys.argv
os.makedirs("outputs", exist_ok=True)
t0 = time.time()

# 1. Paired Monte Carlo, 4,000 draws, seed 20261010
p, base, ai, m = run_mc(4000)
head = {k: summarize(v) for k, v in m.items()}
head["max_accounting_residual"] = float(max(np.abs(ai["residual"]).max(), np.abs(base["residual"]).max()))
json.dump(head, open("outputs/headline.json", "w"), indent=1, default=float)
print(f"Monte Carlo done in {time.time()-t0:.1f}s; max SFC residual {head['max_accounting_residual']:.1e}")
for k in ["gdp_2036", "labshare_2036", "b50_2036", "b50w_2036", "m40_2036", "t10_2036",
          "unemp_adv_2036", "debt_adv_2046"]:
    if k in head:
        h = head[k]; print(f"  {k:16s} median {h['median']:+.2f}  [{h['p5']:+.2f}, {h['p95']:+.2f}]  P(<0)={h['prob_neg']:.2f}")

# 2. Validation
bt = {"labour_share": labour_share_tests(), "fiscal": fiscal_test(), "engels": engels_pause_test()}
json.dump(bt, open("outputs/backtest.json", "w"), indent=1, default=str)
print("Backtests:", bt["fiscal"])

# 3. Policies (2,000 draws)
_, res = evaluate(n=500 if FAST else 2000)
pol = {}
for name, r in res.items():
    pol[name] = {"b50_2036_impact": summarize(r["mr"]["b50_2036"]), "b50_2036_level": summarize(r["m"]["b50_2036"]),
                 "fiscal_pb_vs_sq": float(np.median(r["fiscal_pb"])), "debt46_vs_sq": float(np.median(r["debt46"])),
                 "max_residual": r["resid"]}
    print(f"  {name[:45]:45s} impact median {pol[name]['b50_2036_impact']['median']:+.2f}  P(<0)={pol[name]['b50_2036_impact']['prob_neg']:.2f}")
json.dump(pol, open("outputs/policy.json", "w"), indent=1, default=float)

# 4. Sobol total-order indices (N=1,024, seed 7)
if not FAST:
    s, nruns = run_sobol(1024)
    json.dump(s, open("outputs/sobol.json", "w"), indent=1, default=float)
    print(f"Sobol done: {nruns} runs")
print(f"Total {time.time()-t0:.1f}s")
