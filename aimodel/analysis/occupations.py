"""Forecast by occupation (book, chapter 36, table "Previsione per mestiere"; job simulator).

One source for every number by occupation: the book table and the simulator read outputs/occupations.json,
written by this module. There are no alternative scenarios: one set of inputs, one result per occupation.

Inputs, each with its source:
- AI exposure: Eloundou, Manning, Mishkin and Rock, "GPTs are GPTs", Science 384 (2024), occupation file
  occ_level.csv, gamma measure rated by human experts (tasks whose time a GPT-type system with software tools can
  cut by at least half).
- Classic office automation: for routine office jobs the exposure is the higher of the Eloundou value and the
  Frey and Osborne probability of computerisation (2013 appendix): office clerks 0.96, accountants 0.94,
  customer service 0.55.
- Robots: Frey and Osborne probability for manual and physical occupations, used directly as the automatable
  share (the substitutable share phi applies only to the Eloundou exposure, which counts tasks touched, not
  tasks that can be automated); robots reach the central adoption
  year 5 years after AI.
- Type of occupation: following the distinction between exposure and complementarity of the IMF
  (Pizzinelli et al., WP/23/216; Cazzaniga et al., SDN/2024/001): clerical and routine content work is highly
  exposed with low complementarity; professions with responsibility and human contact have the highest
  complementarity. Software developers and customer service are placed with routine work because the observed
  data already show a decline (Stanford/ADP).
- Adoption: the S-curve of the book (appendix A1), slope 0.425 a year. Where observed data show a decline, the
  central year is calibrated so that the first simulated year reproduces it: Stanford/ADP monthly series, each
  monthly change weighted by its year (2026 and 2025 100%, 2024 50%, 2023 5%, 2022 1%; observed_weights.py),
  as the gap with peers of the same age in the least exposed jobs, averaged over the six age groups. Office
  clerks use the customer service series. Software developers decline only under age 30 and grow above it: no
  overall decline, so they keep 2033 like the other occupations.
  Emerging economies adopt 3 years later, low-income countries 6.5 years later (book central values).
- New tasks inside the same occupation: 0.15 for each task lost, within 3 years (the new roles, such as the
  architect who guides the AI tools).
- Demand: the work machines take over is not the same as jobs lost when demand for the occupation grows (nurses,
  cooks, electricians). Each occupation keeps the yearly growth of the BLS Employment Projections 2025-35
  (published 21 September 2026, table "Occupational projections and characteristics"), extended at the same pace
  to 2046. BLS attributes to AI and automation only the decline of office and administrative support
  occupations (SOC 43): for those, demand is held flat, so that automation is not counted twice.
  Jobs at year t = demand index x (1 - work taken by AI and robots + new roles).
"""
import json
import math
from pathlib import Path

START, END = 2026, 2046
SLOPE = 0.425
REGION_LAG = {"ADV": 0.0, "EME": 3.0, "LIC": 6.5}
ROBOT_LAG = 5.0
DEFAULT_MID = 2033.0
NEW_TASKS, NEW_TASKS_LAG = 0.15, 3.0
CAP = 0.95

# substitutable share of exposed work, share of it automated by 2046
TYPES = {
    "routine":   {"phi": 0.85, "theta": 0.85, "it": "Routine d'ufficio e contenuti", "en": "Routine office and content work"},
    "architect": {"phi": 0.70, "theta": 0.70, "it": "Progettazione con strumenti AI", "en": "Design with AI tools"},
    "care":      {"phi": 0.55, "theta": 0.475, "it": "Responsabilità e contatto umano", "en": "Responsibility and human contact"},
    "manual":    {"phi": 0.55, "theta": 0.70, "it": "Manuale, soprattutto robot", "en": "Manual, mainly robots"},
}

def observed():
    """Weighted yearly gap with the least exposed peers, per occupation series (observed_weights.py)."""
    import sys
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    from observed_weights import weighted_pace, AGES
    st = json.loads((root / "data" / "observed" / "observed_summary.json").read_text(encoding="utf-8"))["stanford"]
    least = [r for r in st["canaries_age_by_exposure"] if r["exposure_quintile"].startswith("Quintile 1")]
    out = {}
    for occ in ("customer_service", "software_developers"):
        gaps = [weighted_pace(st["canaries_" + occ], a) - weighted_pace(least, a) for a in AGES]
        out[occ] = round(sum(gaps) / len(gaps), 4)
    return out


OBSERVED = observed()

# BLS Employment Projections 2025-35, percent change in employment 2025-2035 (SOC used by BLS)
BLS = {
    "clerk": ("43-9061", -6.0), "accountant": ("13-2011", 5.0), "callcenter": ("43-4051", -5.3),
    "translator": ("27-3091", 2.0), "developer": ("15-1252", 10.2), "designer": ("27-1024", -1.7),
    "journalist": ("27-3023", -5.9), "architect": ("15-1211", 7.9), "lawyer": ("23-1011", 4.7),
    "doctor": ("29-1215", 3.3), "nurse": ("29-1141", 5.6), "teacher": ("25-2031", -0.2),
    "retail": ("41-2031", -0.3), "driver": ("53-3032", 3.8), "warehouse": ("53-7062", 1.8),
    "factory": ("51-2090", 1.1),  # team assemblers are part of 51-2090 since SOC 2018
    "cook": ("35-2014", 12.1), "construction": ("47-2061", 7.3),
    # electricians 821.0 -> 896.9 and plumbers 510.6 -> 545.2 thousand: (896.9 + 545.2) / (821.0 + 510.6) - 1
    "electrician": ("47-2111, 47-2152", 8.3),
}
BLS_YEARS = 10.0


def demand_growth(oid):
    """Yearly demand growth used: BLS pace, flat for office and administrative support (BLS: decline due to AI)."""
    soc, pct = BLS[oid]
    if soc.startswith("43-"):
        return 0.0
    return (1.0 + pct / 100.0) ** (1.0 / BLS_YEARS) - 1.0


def demand(t, g):
    return (1.0 + g) ** (t - START)


OCCUPATIONS = [
    # id, English, Italian, SOC, Eloundou gamma (human), Frey-Osborne office, Frey-Osborne robots, type, observed
    ("clerk", "Office clerk", "Impiegato d'ufficio", "43-9061", 0.788, 0.96, 0.0, "routine", "customer_service"),
    ("accountant", "Accountant", "Contabile", "13-2011", 0.840, 0.94, 0.0, "routine", None),
    ("callcenter", "Call center agent", "Addetto call center", "43-4051", 0.864, 0.55, 0.0, "routine", "customer_service"),
    ("translator", "Translator", "Traduttore", "27-3091", 0.880, 0.0, 0.0, "routine", None),
    ("developer", "Software developer", "Sviluppatore software", "15-1252", 0.842, 0.0, 0.0, "routine", "software_developers"),
    ("designer", "Graphic designer", "Grafico", "27-1024", 0.821, 0.0, 0.0, "routine", None),
    ("journalist", "Journalist", "Giornalista", "27-3023", 0.833, 0.0, 0.0, "routine", None),
    ("architect", "Solution architect", "Architetto software", "15-1211", 0.824, 0.0, 0.0, "architect", None),
    ("lawyer", "Lawyer", "Avvocato", "23-1011", 0.800, 0.0, 0.0, "care", None),
    ("doctor", "Doctor", "Medico", "29-1215", 0.542, 0.0, 0.0, "care", None),
    ("nurse", "Nurse", "Infermiere", "29-1141", 0.571, 0.0, 0.0, "care", None),
    ("teacher", "Teacher", "Insegnante", "25-2031", 0.524, 0.0, 0.0, "care", None),
    ("retail", "Retail clerk", "Commesso", "41-2031", 0.447, 0.0, 0.92, "manual", None),
    ("driver", "Driver", "Autista", "53-3032", 0.308, 0.0, 0.79, "manual", None),
    ("warehouse", "Warehouse worker", "Magazziniere", "53-7062", 0.120, 0.0, 0.85, "manual", None),
    ("factory", "Factory worker", "Operaio", "51-2092", 0.176, 0.0, 0.97, "manual", None),
    ("cook", "Cook", "Cuoco", "35-2014", 0.162, 0.0, 0.96, "manual", None),
    ("construction", "Construction worker", "Muratore", "47-2061", 0.050, 0.0, 0.88, "manual", None),
    ("electrician", "Electrician / plumber", "Elettricista / idraulico", "47-2111, 47-2152", 0.178, 0.0, 0.25, "manual", None),
]


def logistic(t, mid):
    return 1.0 / (1.0 + math.exp(-SLOPE * (t - mid)))


def adoption(t, mid, theta):
    """Additional adoption since 2026, zero in 2026, limit theta (appendix A1)."""
    if t <= START:
        return 0.0
    f0 = logistic(START, mid)
    return theta * (logistic(t, mid) - f0) / (1.0 - f0)


def exposure(gamma, fo_office):
    return min(CAP, max(gamma, fo_office))


def calibrated_mid(e, phi, theta, decline, g=0.0):
    """Central year that makes the net change in the first year (2026-2027) equal to the observed decline."""
    target = 1.0 - (1.0 - decline) / (1.0 + g)  # work taken that, with demand growth g, gives the observed decline
    lo, hi = START + 0.5, 2045.0
    for _ in range(60):
        m = (lo + hi) / 2
        if phi * e * adoption(START + 1, m, theta) > target:
            lo = m
        else:
            hi = m
    return round((lo + hi) / 2 * 2) / 2


def shares(t, e, e_rob, phi, theta, mid):
    """Cumulative shares of starting jobs at time t: lost to AI, lost to robots, new tasks."""
    lost_ai = lambda x: phi * e * adoption(x, mid, theta)
    lost_rob = lambda x: e_rob * adoption(x, mid + ROBOT_LAG, theta)  # Frey-Osborne is already the automatable share
    ai, rob = lost_ai(t), lost_rob(t)
    if ai + rob > CAP:
        s = CAP / (ai + rob)
        ai, rob = ai * s, rob * s
    created = NEW_TASKS * min(CAP, lost_ai(t - NEW_TASKS_LAG) + lost_rob(t - NEW_TASKS_LAG))
    return ai, rob, created


def forecast():
    rows = []
    for oid, en, it, soc, gamma, fo_office, fo_rob, typ, obs in OCCUPATIONS:
        phi, theta = TYPES[typ]["phi"], TYPES[typ]["theta"]
        e = exposure(gamma, fo_office)
        g = demand_growth(oid)
        decline = -OBSERVED[obs] if obs else 0.0
        mid = calibrated_mid(e, phi, theta, decline, g) if decline > 0 else DEFAULT_MID
        res, work = {}, {}
        for reg, lag in REGION_LAG.items():
            for year in (2036, 2046):
                ai, rob, cr = shares(year, e, fo_rob, phi, theta, mid + lag)
                work[f"{reg}_{year}"] = round((cr - ai - rob) * 100, 1)
                res[f"{reg}_{year}"] = round((demand(year, g) * (1.0 + cr - ai - rob) - 1.0) * 100, 1)
        rows.append(dict(id=oid, en=en, it=it, soc=soc, exposure_ai=round(e, 3), exposure_robots=fo_rob,
                         type=typ, phi=phi, theta=theta, mid_adv=mid, observed=obs,
                         bls_soc=BLS[oid][0], bls_change=BLS[oid][1], demand_growth=round(g, 6),
                         work=work, results=res))
    return rows


def write(path=None):
    path = Path(path or Path(__file__).resolve().parents[2] / "outputs" / "occupations.json")
    data = dict(start=START, end=END, slope=SLOPE, region_lag=REGION_LAG, robot_lag=ROBOT_LAG,
                new_tasks=NEW_TASKS, new_tasks_lag=NEW_TASKS_LAG, cap=CAP, types=TYPES,
                observed=OBSERVED, bls_years=BLS_YEARS, occupations=forecast())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = write()
    for o in sorted(d["occupations"], key=lambda o: o["results"]["ADV_2046"]):
        r = o["results"]
        w = o["work"]
        print(f'{o["it"]:26s} {o["type"]:9s} esp {o["exposure_ai"]:.2f} anno {o["mid_adv"]} BLS {o["bls_change"]:+5.1f}'
              f'  lavoro 2046 {w["ADV_2046"]:6.1f}  posti 2036 {r["ADV_2036"]:6.1f}  2046 {r["ADV_2046"]:6.1f}')
