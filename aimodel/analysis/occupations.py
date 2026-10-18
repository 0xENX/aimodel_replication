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
- Robots: Frey and Osborne probability for manual and physical occupations; robots reach the central adoption
  year 5 years after AI.
- Type of occupation: following the distinction between exposure and complementarity of the IMF
  (Pizzinelli et al., WP/23/216; Cazzaniga et al., SDN/2024/001): clerical and routine content work is highly
  exposed with low complementarity; professions with responsibility and human contact have the highest
  complementarity. Software developers and customer service are placed with routine work because the observed
  data already show a decline (Stanford/ADP, last year).
- Adoption: the S-curve of the book (appendix A1), slope 0.425 a year. Where observed data exist, the central
  year is calibrated so that the first simulated year reproduces the decline of the last 12 months
  (Stanford/ADP, August 2025 - August 2026, middle of the range between a young-heavy and an older-heavy age mix);
  office clerks use the customer service series. The other occupations use 2033, close to the calibrated years.
  Emerging economies adopt 3 years later, low-income countries 6.5 years later (book central values).
- New tasks inside the same occupation: 0.15 for each task lost, within 3 years (the new roles, such as the
  architect who guides the AI tools).
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

# observed yearly change, Stanford/ADP Canaries, Aug 2025 - Aug 2026 (young-heavy mix, older-heavy mix)
OBSERVED = {"customer_service": (-0.0313, -0.0118), "software_developers": (-0.0212, -0.0037)}

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


def calibrated_mid(e, phi, theta, decline):
    """Central year that makes the loss in the first year (2026-2027) equal to the observed decline."""
    lo, hi = START + 0.5, 2045.0
    for _ in range(60):
        m = (lo + hi) / 2
        if phi * e * adoption(START + 1, m, theta) > decline:
            lo = m
        else:
            hi = m
    return round((lo + hi) / 2 * 2) / 2


def shares(t, e, e_rob, phi, theta, mid):
    """Cumulative shares of starting jobs at time t: lost to AI, lost to robots, new tasks."""
    lost_ai = lambda x: phi * e * adoption(x, mid, theta)
    lost_rob = lambda x: phi * e_rob * adoption(x, mid + ROBOT_LAG, theta)
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
        mid = calibrated_mid(e, phi, theta, -sum(OBSERVED[obs]) / 2) if obs else DEFAULT_MID
        res = {}
        for reg, lag in REGION_LAG.items():
            for year in (2036, 2046):
                ai, rob, cr = shares(year, e, fo_rob, phi, theta, mid + lag)
                res[f"{reg}_{year}"] = round((cr - ai - rob) * 100, 1)
        rows.append(dict(id=oid, en=en, it=it, soc=soc, exposure_ai=round(e, 3), exposure_robots=fo_rob,
                         type=typ, phi=phi, theta=theta, mid_adv=mid, observed=obs, results=res))
    return rows


def write(path=None):
    path = Path(path or Path(__file__).resolve().parents[2] / "outputs" / "occupations.json")
    data = dict(start=START, end=END, slope=SLOPE, region_lag=REGION_LAG, robot_lag=ROBOT_LAG,
                new_tasks=NEW_TASKS, new_tasks_lag=NEW_TASKS_LAG, cap=CAP, types=TYPES,
                observed=OBSERVED, occupations=forecast())
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = write()
    for o in sorted(d["occupations"], key=lambda o: o["results"]["ADV_2046"]):
        r = o["results"]
        print(f'{o["it"]:26s} {o["type"]:9s} esposizione {o["exposure_ai"]:.2f} anno centrale {o["mid_adv"]}'
              f'  ADV 2036 {r["ADV_2036"]:6.1f}  2046 {r["ADV_2046"]:6.1f}')
