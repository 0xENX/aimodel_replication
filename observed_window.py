"""Observed data used to read the effect of AI: last year only.

Data from 2022 to 2024 reflect post-pandemic over-hiring and higher interest rates and are not used to read the
effect of AI. Stanford/ADP series keep observations from August 2025 and are rebased to August 2025 = 100;
Eurostat annual series keep 2024 and 2025. The archived files in data/observed are left unchanged.
"""
import copy

START_MONTH = "2025-08-01"
START_YEAR = 2024
ID_COLUMNS = {"observation_date", "exposure_quintile", "vintage", "Age Group", "Exposure Group", "Share"}


def _rebase(rows, group_key=None):
    out = [r for r in rows if r["observation_date"] >= START_MONTH]
    groups = {}
    for r in out:
        groups.setdefault(r.get(group_key) if group_key else None, []).append(r)
    for g in groups.values():
        g.sort(key=lambda r: r["observation_date"])
        base = dict(g[0])   # values of August 2025, kept before any row is rebased
        for r in g:
            for k, v in list(r.items()):
                if k in ID_COLUMNS or k.startswith("composition"):
                    continue
                if v not in ("", None) and base.get(k) not in ("", None, "0", 0):
                    r[k] = round(float(v) / float(base[k]) * 100, 2)
    return out


def last_year(obs):
    """Copy of observed_summary.json restricted to the last year (indices rebased to August 2025 = 100)."""
    o = copy.deepcopy(obs)
    st = o.get("stanford", {})
    for key, rows in list(st.items()):
        if not rows or "observation_date" not in rows[0]:
            continue
        if key == "canaries_composition":
            st[key] = [r for r in rows if r["observation_date"] >= START_MONTH]
        elif rows and "exposure_quintile" in rows[0]:
            st[key] = _rebase(rows, "exposure_quintile")
        elif key == "canaries_by_exposure":
            st[key] = _rebase(rows)
        else:
            st[key] = _rebase(rows)
    if "eurostat" in o:
        o["eurostat"] = [r for r in o["eurostat"] if int(r["year"]) >= START_YEAR]
    return o
