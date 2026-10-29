# The ReplaceMind: the model behind the book

**How much work will artificial intelligence and robots take, and where?** This repository holds the code and data
behind *The ReplaceMind* by Marc Molften: a model of the world economy in three regions, 4,000 paired simulations with
and without the new wave of AI, a forecast for 19 professions to 2046 and a map of social tension country by country.
Every number in the book is produced by this code, and the same files run in the browser on the website.

- **Simulators (free, in your browser):** [thereplacemind.com](https://thereplacemind.com) —
  [Job Simulator](https://thereplacemind.com/simulator), [Economy Model](https://thereplacemind.com/model),
  [Social Risk](https://thereplacemind.com/social)
- **The book** (English and Italian, Kindle and paperback):
  [English edition on Amazon](https://www.amazon.com/dp/B0HPL8SMR4) ·
  [edizione italiana su Amazon](https://www.amazon.it/dp/B0HPL9WNB7)
- **Reproduce the results:** see the sections below (Python 3.10+, NumPy).
- **License:** code and data under the [MIT License](LICENSE). The book, its covers and the cover illustration are not
  covered by it and remain all rights reserved.

---

# Software package of the book - version 3.1

The macroeconomic model of the report (version 2, with labour demand at elasticity ε),
the employment module by age, observed Eurostat and Stanford/ADP data, and the book's experiments.

## Version history

The name "v2" was used for two different packages; this table tells them apart.

| Version | What it contains | Does it reproduce the book? |
| --- | --- | --- |
| v1 | First edition of the working paper: labour demand = wage bill / wage | No |
| provisional v2 (`aimodel_replication_v2`, October 2026) | Corrected wage trend and revised priors, 20 parameters, **without ε** | No (e.g. ADV unemployment 2036 +2.7 instead of +4.3) |
| v2 (macro model of this package) | + labour demand from technology and output with elasticity ε, 21 parameters | Yes: the report and the book's macro results |
| v3 | + age module linked in one direction only | Yes, for chapters 7-9 in the October 2026 draft |
| **v3.1** (current) | + consistency calibration of the age module, two-way link, entry policies, the book's experiments | Basis of the book's revision |

With v3.1 the numbers of the age module change compared with v3, because of the consistency calibration
(see below). The results of the macro model do not change: with the default options
`simulate()` produces exactly the same values (checked by the tests).

## What is new in v3.1

- **Consistency calibration** (`calibrate_consistency.py`): without calibration, the no-AI world of the
  age module rose above the structural unemployment of the macro model (about 7% instead
  of 5% in advanced economies). One factor per region on the hiring probabilities,
  `hire_hazard_scale` in the configuration, brings the no-AI world back to the structural rate.
  It is a consistency condition between the two models, not an estimate from the data.
- **Two-way link** (`aimodel/core/coupled.py`): non-employment from the age module
  replaces macro unemployment in the wage curve and in the cost of benefits, in both
  paired worlds; the calculation is repeated until it converges. Option `ur_path` of `simulate()`.
- **Entry policies** (option `policy` of `simulate_employment()`): public jobs,
  youth employment incentive, reduced working hours with wage top-up,
  compared at equal cost.
- **The book's experiments** (`run_book_experiments.py`): results in `outputs/experiments/`.
- **Entry barrier**: the parameter `entry_barrier` acts twice, on the distribution
  of jobs by age and on the probability of first entry. This is intended and now documented in the code;
  the sensitivity analysis shows it is one of the two assumptions that weigh the most.

```text
python calibrate_consistency.py          # once, writes hire_hazard_scale into the configuration
python run_employment.py --draws 4000    # chapters 7-9
python run_book_experiments.py           # chapters 9, 12, 24, 26
python -m unittest discover -s tests -v
```

The macro model and its original outputs are kept under `outputs/`.
The results of the age module are in `outputs/employment/`, those of the experiments in
`outputs/experiments/`.

## Opening the results

- `outputs/employment/occupazione.html`: self-contained interactive report, works offline.
- `outputs/employment/sezione_occupazione.pdf`: printable annex with data and charts.
- `outputs/employment/age_series.csv`: all series, scenarios, AI/no-AI versions and percentiles.
- `outputs/employment/results.json` and `config_used.json`: results and the configuration actually used.
- `FONTI_E_METODO.md`: sources, limits, formulas and calibration plan (in Italian).

## Running the extension

Python 3.10+, NumPy. ReportLab only to generate the PDF. No SALib needed
for the extension; SALib is needed for the old `run_all.py`.

```text
python -m pip install -r requirements-employment.txt
python run_employment.py --draws 4000
python make_employment_pdf.py
python -m unittest discover -s tests -v
```

The default configuration uses `config/employment_eu_proxy.json` if present:
an initial ADV profile partly based on EU-27 2025. To compare assumptions
that are entirely illustrative, use:

```text
python run_employment.py --config config/employment.json --draws 4000
```

To update the observations and the proxy (only the first step needs a network connection):

```text
python fetch_employment_data.py --year 2025
python prepare_observed.py
python run_employment.py --draws 4000
python make_employment_pdf.py
```

**Essential limit:** `run_employment.py` uses the module as a satellite linked in one
direction only to the macro model: demand -> flows by age. In that mode the new employment
does NOT change GDP, wages, incomes or debt. The two-way link exists only in the experiment
`feedback` of `run_book_experiments.py`, and it works through wages and unemployment benefits.
The simulations are neither forecasts nor estimated causal effects.
The EU is only a proxy for the advanced economies; all matching/AI parameters and
the EME/LIC profiles remain assumptions. The observed data are shown separately.

## New modules

- `aimodel/core/employment.py`: annual cohorts, entry, separations, matching, discouragement.
- `config/`: assumptions, scenarios and EU proxy with sources.
- `fetch_employment_data.py`, `prepare_observed.py`: data acquisition with hashes, processing and proxy.
- `run_employment.py`: paired draws, CSV series and report.
- `employment_report.py`, `report_template.html`, `make_employment_pdf.py`: visualisation.
- `tests/test_employment.py`: identities, cohorts, matching, neutrality and data decoder.

## Original v2 documentation

*Automation, Distribution and Public Finance in the Age of AI, 2026-2046* (working paper, October 2026)

## Requirements
Python 3.10+, NumPy, SALib (`pip install numpy SALib`).

## Run
    python run_all.py          # everything, about 6 seconds
    python run_all.py --fast   # skips Sobol; 500 draws for policies

Results are written to `outputs/`. The outputs shipped in this package were produced by running `run_all.py` and match the paper.

| File | Paper sections |
| --- | --- |
| outputs/headline.json | 7, 8, 10, 13 (paired Monte Carlo, 4,000 draws, seed 20261010) |
| outputs/backtest.json | 6 (validation) |
| outputs/policy.json   | 12 (nine interventions, 2,000 draws) |
| outputs/sobol.json    | 9 (Saltelli N = 1,024, 23,552 runs, seed 7) |

## Code layout
- `aimodel/calibration/data.py`: calibration targets with sources, and the 21 parameter priors
- `aimodel/core/economy.py`: the model (tasks, labour market, households, firms, government, regions, accounting check)
- `aimodel/core/run.py`: paired runs, with and without AI
- `aimodel/analysis/`: metrics, Monte Carlo and Sobol, backtests, policies

All results are differences between paired runs of the same parameter draw with and without the AI wave. They are conditional model outputs, not forecasts.

## Changes in version 2 (October 2026)
- Wage equation: the wage trend now follows the non-AI erosion of labour task content (d0). In version 1 wages outgrew the wage bill in the no-AI world, so unemployment drifted up without AI when wages were rigid (to about 7.8% in advanced economies by 2046 with kappa = 0.05). The no-AI world now stays at structural unemployment for any kappa; the accounting identity still holds to machine precision.
- Priors revised: kappa 0.20-0.80 -> 0.05-0.50 (flatter wage Phillips curves after 2008); psi 0.25-1.00 -> 0.25-0.85; lag_new 2-8 -> 4-10 years; theta 0.15-0.70 -> 0.25-0.70. Sources are in `aimodel/calibration/data.py`.
- Labour demand: derived from technology and output (tasks left to labour times output, at the wage of the paired no-AI run) with a constant-output wage elasticity `eps` drawn from 0.15-0.75 (Hamermesh 1993). In version 1 labour demand was the wage bill divided by the wage, so lower wages brought back jobs one for one and demand returned to labour supply by construction. With eps = 1 and rent_share = 0 version 2 reproduces version 1 to machine precision. Profit-sharing (rent_share) now raises labour income but no longer creates jobs.
- The outputs in `outputs/` were regenerated with version 2. They no longer match the version 1 paper.

## Report charts
    python make_report_charts.py   # after run_all.py; writes outputs/charts/

Writes the data behind every chart of the report and the annex: `six_indicators.csv`, `aggregate_ai.csv`, `aggregate_noai.csv`, `labour_adv.csv`, `fan_aggregate.csv` and `inline.json` (scenario snapshot, income groups, Sobol indices, policies).
