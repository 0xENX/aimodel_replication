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
- **Reproduce the results:** see the sections below (Python 3.10+, NumPy). The rest of this README is in Italian.
- **License:** code and data under the [MIT License](LICENSE). The book, its covers and the cover illustration are not
  covered by it and remain all rights reserved.

---

# Pacchetto software del libro - versione 3.1

Modello macroeconomico del report (versione 2, con domanda di lavoro a elasticità ε),
modulo occupazionale per età, dati osservati Eurostat e Stanford/ADP, esperimenti del libro.

## Storia delle versioni

Il nome "v2" è stato usato per due pacchetti diversi; questa tabella li distingue.

| Versione | Che cosa contiene | Riproduce il libro? |
| --- | --- | --- |
| v1 | Prima edizione del working paper: domanda di lavoro = monte salari / salario | No |
| v2 provvisoria (`aimodel_replication_v2`, ottobre 2026) | Trend salariale corretto e prior rivisti, 20 parametri, **senza ε** | No (es. disoccupazione ADV 2036 +2,7 invece di +4,3) |
| v2 (modello macro di questo pacchetto) | + domanda di lavoro da tecnologia e prodotto con elasticità ε, 21 parametri | Sì: report e risultati macro del libro |
| v3 | + modulo per età collegato in una sola direzione | Sì, per i capitoli 7-9 nella stesura di ottobre 2026 |
| **v3.1** (attuale) | + taratura di coerenza del modulo per età, collegamento a due vie, politiche d'ingresso, esperimenti del libro | Base della revisione del libro |

Con la v3.1 i numeri del modulo per età cambiano rispetto alla v3, per la taratura di coerenza
(vedi sotto). I risultati del modello macro non cambiano: con le opzioni predefinite
`simulate()` produce esattamente gli stessi valori (verificato dai test).

## Novità della v3.1

- **Taratura di coerenza** (`calibrate_consistency.py`): senza taratura il mondo senza AI del
  modulo per età saliva sopra la disoccupazione strutturale del modello macro (circa 7% invece
  del 5% nelle economie avanzate). Un fattore per regione sulle probabilità di assunzione,
  `hire_hazard_scale` nella configurazione, riporta il mondo senza AI al tasso strutturale.
  È una condizione di coerenza fra i due modelli, non una stima dai dati.
- **Collegamento a due vie** (`aimodel/core/coupled.py`): la non occupazione del modulo per età
  sostituisce la disoccupazione macro nella curva dei salari e nel costo dei sussidi, nei due
  mondi appaiati; il calcolo si ripete fino a convergenza. Opzione `ur_path` di `simulate()`.
- **Politiche d'ingresso** (opzione `policy` di `simulate_employment()`): posti pubblici,
  incentivo all'occupazione giovanile, riduzione dell'orario con integrazione salariale,
  confrontati a parità di costo.
- **Esperimenti del libro** (`run_book_experiments.py`): risultati in `outputs/experiments/`.
- **Barriera d'ingresso**: il parametro `entry_barrier` agisce due volte, sulla distribuzione
  dei posti per età e sulla probabilità di primo ingresso. È voluto e ora documentato nel codice;
  l'analisi di sensibilità mostra che è una delle due ipotesi che pesano di più.

```text
python calibrate_consistency.py          # una volta, scrive hire_hazard_scale nella configurazione
python run_employment.py --draws 4000    # capitoli 7-9
python run_book_experiments.py           # capitoli 9, 12, 24, 26
python -m unittest discover -s tests -v
```

Il modello macro e i suoi output originali sono preservati sotto `outputs/`.
I risultati del modulo per età sono in `outputs/employment/`, quelli degli esperimenti in
`outputs/experiments/`.

## Aprire i risultati

- `outputs/employment/occupazione.html`: rapporto interattivo autonomo, funziona offline.
- `outputs/employment/sezione_occupazione.pdf`: appendice stampabile con dati e grafici.
- `outputs/employment/age_series.csv`: tutte le serie, scenari, versioni AI/no-AI e percentili.
- `outputs/employment/results.json` e `config_used.json`: risultati e configurazione effettiva.
- `FONTI_E_METODO.md`: fonti, limiti, formule e piano di calibrazione.

## Eseguire l'estensione

Python 3.10+, NumPy. ReportLab solo per generare il PDF. Nessuna SALib necessaria
per l'estensione; SALib serve per il vecchio `run_all.py`.

```text
python -m pip install -r requirements-employment.txt
python run_employment.py --draws 4000
python make_employment_pdf.py
python -m unittest discover -s tests -v
```

La configurazione predefinita usa `config/employment_eu_proxy.json` se presente:
profilo iniziale ADV parzialmente basato su UE-27 2025. Per confrontare ipotesi
interamente illustrative usare:

```text
python run_employment.py --config config/employment.json --draws 4000
```

Per aggiornare osservazioni e proxy (solo la prima operazione richiede rete):

```text
python fetch_employment_data.py --year 2025
python prepare_observed.py
python run_employment.py --draws 4000
python make_employment_pdf.py
```

**Limite essenziale:** `run_employment.py` usa il modulo come satellite collegato in una sola
direzione al modello macro: domanda -> flussi per eta. In quella modalita la nuova occupazione
NON modifica PIL, salari, redditi o debito. Il collegamento a due vie esiste solo nell'esperimento
`feedback` di `run_book_experiments.py`, e agisce attraverso salari e sussidi di disoccupazione.
Le simulazioni non sono previsioni ne effetti causali stimati.
UE e solo un proxy delle economie avanzate; tutti i parametri di matching/AI e
i profili EME/LIC restano ipotesi. I dati osservati sono mostrati separatamente.

## Moduli nuovi

- `aimodel/core/employment.py`: coorti annuali, ingresso, separazioni, matching, scoraggiamento.
- `config/`: assunzioni, scenari e proxy EU con fonti.
- `fetch_employment_data.py`, `prepare_observed.py`: acquisizione con hash, trattamento e proxy.
- `run_employment.py`: estrazioni appaiate, serie CSV e report.
- `employment_report.py`, `report_template.html`, `make_employment_pdf.py`: visualizzazione.
- `tests/test_employment.py`: identita, coorti, matching, neutralita e decoder dati.

## Documentazione originale v2

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
