"""Observed data weighted by year: recent years count most.

The effect of AI is read from all observed years, each weighted by how much it reflects AI rather than the
post-pandemic hiring cycle and the rise in interest rates: 2026 and 2025 at 100%, 2024 at 50%, 2023 at 5%,
2022 at 1%. Every monthly change (Stanford/ADP) or yearly change (Eurostat) takes the weight of its year;
the weighted average gives the observed yearly pace. The archived data in data/observed are not modified
and the book keeps every series and table.
"""
import math

YEAR_WEIGHTS = {2022: 0.01, 2023: 0.05, 2024: 0.50, 2025: 1.00, 2026: 1.00}
AGES = ["Early Career 1 (22-25)", "Early Career 2 (26-30)", "Developing (31-34)",
        "Mid-Career 1 (35-40)", "Mid-Career 2 (41-49)", "Senior (50+)"]


def weighted_pace(rows, column):
    """Weighted yearly change of a monthly index: sum of w(year) * log monthly change / sum of w, times 12."""
    rows = sorted((r for r in rows if r.get(column) not in ("", None)), key=lambda r: r["observation_date"])
    num = den = 0.0
    for prev, cur in zip(rows, rows[1:]):
        w = YEAR_WEIGHTS.get(int(cur["observation_date"][:4]), 0.0)
        if w:
            num += w * math.log(float(cur[column]) / float(prev[column]))
            den += w
    return math.exp(12 * num / den) - 1


def weighted_points(rows, geo, age, field="employment_rate"):
    """Weighted yearly change in points of a Eurostat annual rate (change from year y-1 to y weighted by y)."""
    s = {int(r["year"]): float(r[field]) for r in rows if r["geo"] == geo and r["age"] == age}
    num = den = 0.0
    for y, w in YEAR_WEIGHTS.items():
        if y in s and y - 1 in s and y - 1 >= 2022:
            num += w * (s[y] - s[y - 1]); den += w
    return num / den if den else float("nan")


def summary(obs):
    st = obs["stanford"]
    q = {}
    for r in st["canaries_age_by_exposure"]:
        q.setdefault(r["exposure_quintile"], []).append(r)
    least, most = q["Quintile 1 (least exposed)"], q["Quintile 5 (most exposed)"]
    out = {"weights": YEAR_WEIGHTS,
           "young_22_25": {"least": weighted_pace(least, AGES[0]), "most": weighted_pace(most, AGES[0])},
           "young_26_30": {"least": weighted_pace(least, AGES[1]), "most": weighted_pace(most, AGES[1])}}
    for occ in ("software_developers", "customer_service"):
        rows = st["canaries_" + occ]
        by_age = {a: weighted_pace(rows, a) for a in AGES}
        out[occ] = {"by_age": by_age, "all_ages": sum(by_age.values()) / len(by_age)}
    eu = obs["eurostat"]
    out["eurostat"] = {geo: {age: {"employment": weighted_points(eu, geo, age),
                                   "participation": weighted_points(eu, geo, age, "participation_rate")}
                             for age in ("15-24", "25-34", "35-49", "50-64")} for geo in ("IT", "EU27_2020")}
    return out


if __name__ == "__main__":
    import json
    from pathlib import Path
    obs = json.loads((Path(__file__).parent / "data/observed/observed_summary.json").read_text(encoding="utf-8"))
    s = summary(obs)
    print(json.dumps(s, indent=1))
