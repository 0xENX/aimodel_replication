"""Run the age extension offline: python run_employment.py --draws 1000.

Common random numbers across scenarios. Quantiles are conditional simulation
ranges, not confidence intervals, empirical estimates or scenario probabilities.
"""
import argparse
import csv
import gc
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
from aimodel.calibration.data import PRIORS, CAL
from aimodel.core.economy import simulate
from aimodel.core.employment import load_config, simulate_employment

ROOT = Path(__file__).resolve().parent
RATE_KEYS = ["employment_rate", "unemployment_rate", "participation_rate", "inactivity_rate",
             "broad_nonemployment", "gap_rate", "gap_potential", "hire_rate", "rehire_rate", "first_hire_rate"]
STOCK_KEYS = ["potential_supply", "supply", "demand", "employed", "unemployed", "discouraged", "vacancies"]
FLOW_KEYS = ["hires", "first_hires", "rehires", "separations", "job_cuts", "age65_exits",
             "participation_exits", "searcher_returns", "discouragement_flow"]


def summarize(a):
    q = np.percentile(a, [5, 50, 95], axis=1)
    return {name: np.round(v, 6).tolist() for name, v in zip(("p5", "p50", "p95"), q)}


def run(n=1000, seed=20261010, config_path=None):
    if n < 2:
        raise ValueError("At least two draws required")
    if config_path is None:
        proxy = ROOT / "config" / "employment_eu_proxy.json"
        config_path = proxy if proxy.exists() else ROOT / "config" / "employment.json"
    c = load_config(config_path)
    rng = np.random.default_rng(seed)
    p0 = {k: rng.uniform(lo, hi, n) for k,(lo,hi,_) in PRIORS.items()}
    latent = {k:(p0[k]-lo)/(hi-lo) for k,(lo,hi,_) in PRIORS.items()}
    q = np.random.default_rng(seed+1).uniform(*c["matching_draw_range"], n)
    base = simulate(p0, ai=False)
    out = ROOT / "outputs" / "employment"
    out.mkdir(parents=True, exist_ok=True)
    result = dict(years=base["years"].tolist(), regions=c["regions"],
                  ages=[f"{a}-{b}" for a,b in c["bands"]], draws=n, seed=seed,
                  config_status=c["status"], config_sha256=hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
                  config_file=str(Path(config_path).resolve()), scenarios={},
                  architecture="one-way age satellite; no macroeconomic feedback from age employment",
                  stock_units="100 = potential labour force of this age band in 2026; NOT headcounts",
                  flow_units="annual % of potential labour force of this age band in 2026",
                  interval="5th/95th percentiles of assumed parameter draws, NOT statistical confidence intervals",
                  calibration_sources=c["sources"])
    result["runtime"] = dict(python=platform.python_version(),numpy=np.__version__)
    result["code_sha256"] = {str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in [ROOT/"aimodel/core/employment.py",ROOT/"aimodel/core/economy.py",ROOT/"run_employment.py"]}
    records = []
    for name, sc in c["scenarios"].items():
        p = {k:v.copy() for k,v in p0.items()}
        for k, bounds in sc["priors"].items():
            if k not in PRIORS or len(bounds) != 2 or not np.isfinite(bounds).all() or bounds[0] > bounds[1]:
                raise ValueError(f"Invalid scenario prior {k}: {bounds}")
            p[k] = bounds[0] + latent[k]*(bounds[1]-bounds[0])
        macro = simulate(p, ai=True, base_ratio=base["dd_ratio"], base_wage=base["wage"])
        b = simulate_employment(base, c, name, q, ai=False)
        a = simulate_employment(macro, c, name, q, ai=True)
        norm = b["potential_supply"][0][None]
        summary = {}
        for k in RATE_KEYS:
            summary[k] = dict(ai=summarize(a[k]), noai=summarize(b[k]), difference=summarize(a[k]-b[k]))
        for k in STOCK_KEYS+FLOW_KEYS:
            summary[k] = dict(ai=summarize(100*a[k]/norm), noai=summarize(100*b[k]/norm),
                             difference=summarize(100*(a[k]-b[k])/norm))
        aggregate = {}
        # Regional rates: aggregate stocks before division, never average age rates.
        for label, data in (("ai",a),("noai",b)):
            aggregate[label] = dict(
                unemployment=summarize(100*data["unemployed"].sum(-1)/data["supply"].sum(-1)),
                broad_nonemployment=summarize(100*(data["potential_supply"]-data["employed"]).sum(-1)/data["potential_supply"].sum(-1)),
                original_macro_unemployment=summarize(100*(macro if label=="ai" else base)["unemp"]))
        result["scenarios"][name] = dict(label=sc["label"], assumptions=sc, metrics=summary,
            aggregate=aggregate, max_stock_flow_residual=max(a["max_stock_flow_residual"], b["max_stock_flow_residual"]),
            max_macro_accounting_residual=float(np.abs(macro["residual"]).max()))
        for metric, versions in summary.items():
            for version, stats in versions.items():
                for ti, year in enumerate(result["years"]):
                    for r, region in enumerate(result["regions"]):
                        for ag, age in enumerate(result["ages"]):
                            records.append(dict(scenario=name, metric=metric, version=version, year=year,
                                                region=region, age=age, **{k:v[ti][r][ag] for k,v in stats.items()}))
        print(name, "stock-flow residual",result["scenarios"][name]["max_stock_flow_residual"],
              "ADV age unemployment gap in 2046",summary["unemployment_rate"]["difference"]["p50"][-1][0])
        del a,b,macro; gc.collect()
    (out / "results.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    (out / "config_used.json").write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding="utf-8")
    with (out / "age_series.csv").open("w",encoding="utf-8",newline="") as f:
        w = csv.DictWriter(f,fieldnames=list(records[0])); w.writeheader(); w.writerows(records)
    from employment_report import write_html
    write_html(result,out)
    print("Report:",out / "occupazione.html")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws",type=int,default=1000)
    ap.add_argument("--seed",type=int,default=20261010)
    ap.add_argument("--config",type=Path)
    args = ap.parse_args()
    run(args.draws,args.seed,args.config)
