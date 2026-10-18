"""Social tension projection: the same formulas as the Social Risk page (simulator/social.html), for the book.

The page computes the projection live in the browser; this module repeats it step by step so that the chapter on
social risk prints the same numbers. Start month January 2026, everything as the increase since then.

- Work taken by AI and robots in a region: the nineteen occupations of Table 65 weighted by employment, with the
  region's lag, scaled by the share of employment exposed in the region (60/40/26 percent, chapter 6).
- Pressure on a country: work taken in its region since the start (percentage points) x (people using AI in the
  country + robots) / (regional average of people using AI + robots).
- Raw tension: pressure x (1 + 0.5 x starting risk / 100).
- Pace: month by month the growth of raw tension is added at a quarter of its speed until robots take 3 percentage
  points of the work of the region, at full speed after that (linear in between).
- United States by state: the national value x work taken with the state's employment / work taken nationally.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ("ADV", "EME", "LIC")
AMPLIFY, SLOW, ROBOT_ENTRY = 0.5, 0.25, 3.0


class Projection:
    def __init__(self, data=None, social=None, start_year=2026):
        self.D = data or json.loads((ROOT / "outputs" / "occupations.json").read_text(encoding="utf-8"))
        self.S = social or json.loads((ROOT / "outputs" / "social_risk.json").read_text(encoding="utf-8"))
        self.start = start_year * 12
        dates = self.S["ai_dates"]
        self.obs_t = [self._date_y(x) for x in dates]
        self.t_last = self.obs_t[-1]
        last = dates[-1]
        self.reg_median = {}
        for r in REG:
            v = sorted(c["ai_use"][last] for c in self.S["countries"] if c["region"] == r and c["ai_use"].get(last) is not None)
            self.reg_median[r] = v[len(v) // 2] if v else 10
        self.cum_m, self.cum, self.prev = self.start, {}, {}

    @staticmethod
    def _date_y(s):
        y, m, d = (int(x) for x in s.split("-"))
        return y + (m - 1 + d / 31) / 12

    def logistic(self, t, mid):
        return 1 / (1 + math.exp(-self.D["slope"] * (t - mid)))

    def adoption(self, t, mid, theta):
        if t <= self.D["start"]:
            return 0.0
        f0 = self.logistic(self.D["start"], mid)
        return theta * (self.logistic(t, mid) - f0) / (1 - f0)

    def work_taken(self, r, t, w=None):
        w = w or self.D["aggregate"]["weights"]
        lag, W, AI, rob = self.D["region_lag"][r], 0.0, 0.0, 0.0
        for j in self.D["occupations"]:
            mid = j["mid_adv"] + lag
            ai = j["phi"] * j["exposure_ai"] * self.adoption(t, mid, j["theta"])
            rb = j["exposure_robots"] * self.adoption(t, mid + self.D["robot_lag"], j["theta"])
            if ai + rb > self.D["cap"]:
                rb *= self.D["cap"] / (ai + rb)
            W += w[j["id"]]; AI += w[j["id"]] * ai; rob += w[j["id"]] * rb
        e = self.S["exposure"][r] / self.S["exposure"]["ADV"]
        return e * AI / W, e * rob / W

    def ai_use(self, c, t):
        dates = self.S["ai_dates"]
        obs = [c["ai_use"].get(x) for x in dates]
        last = obs[-1] / 100 if obs[-1] is not None else self.reg_median[c["region"]] / 100
        if t <= self.t_last:
            if obs[0] is None:
                return last
            i = next((k for k, x in enumerate(self.obs_t) if x >= t), -1)
            if i <= 0:
                return obs[0] / 100
            a, b = obs[i - 1] / 100, obs[i] / 100
            return a + (b - a) * (t - self.obs_t[i - 1]) / (self.obs_t[i] - self.obs_t[i - 1])
        target = max(last, self.S["exposure"][c["region"]])
        mid = 2033 + self.D["region_lag"][c["region"]]
        f0 = self.logistic(self.t_last, mid)
        return last + (target - last) * (self.logistic(t, mid) - f0) / (1 - f0)

    def raw_tensions(self, yr):
        t0 = self.start / 12
        mean = {}
        for r in REG:
            cs = [x for x in self.S["countries"] if x["region"] == r]
            ai_now, rob_now = self.work_taken(r, yr)
            ai_0, rob_0 = self.work_taken(r, t0)
            mean[r] = (sum(self.ai_use(x, yr) for x in cs) / len(cs), rob_now, 100 * max(0.0, ai_now + rob_now - ai_0 - rob_0))
        out = {}
        for c in self.S["countries"]:
            ai_mean, rob, u = mean[c["region"]]
            own = self.ai_use(c, yr) + rob
            pressure = u * own / (ai_mean + rob) if ai_mean + rob > 0 else 0.0
            out[c["iso3"]] = pressure * (1 + AMPLIFY * c["risk"] / 100)
        return out

    def pace(self, r, yr):
        rob = self.work_taken(r, yr)[1] - self.work_taken(r, self.start / 12)[1]
        return SLOW + (1 - SLOW) * min(1.0, 100 * max(0.0, rob) / ROBOT_ENTRY)

    def tension(self, month):
        """{iso3: tension} at the given month (year x 12 + month index)."""
        while self.cum_m < month:
            self.cum_m += 1
            y = self.cum_m / 12
            p = {r: self.pace(r, y) for r in REG}
            raw = self.raw_tensions(y)
            for c in self.S["countries"]:
                k = c["iso3"]
                self.cum[k] = self.cum.get(k, 0.0) + (raw[k] - self.prev.get(k, 0.0)) * p[c["region"]]
                self.prev[k] = raw[k]
        return dict(self.cum)

    def state_factor(self, s, yr):
        t0 = self.start / 12
        tot = lambda w=None: sum(self.work_taken("ADV", yr, w)) - sum(self.work_taken("ADV", t0, w))
        nat = tot()
        return tot(s["weights"]) / nat if nat > 0 else 0.0

    def robot_entry_year(self, r):
        """First month in which robots take ROBOT_ENTRY percentage points of the work of the region."""
        for m in range(self.start, self.start + 12 * 30):
            y = m / 12
            if 100 * (self.work_taken(r, y)[1] - self.work_taken(r, self.start / 12)[1]) >= ROBOT_ENTRY:
                return y
        return None


def build(years=(2030, 2034, 2038, 2042, 2046)):
    pr = Projection()
    S = pr.S
    by_year = {}
    for y in range(2027, 2047):
        by_year[y] = {k: round(v, 3) for k, v in pr.tension(y * 12).items()}
    regions = {}
    for y in years:
        regions[y] = {}
        for r in REG:
            cs = [c for c in S["countries"] if c["region"] == r]
            ai_now, rob_now = pr.work_taken(r, y)
            ai_0, rob_0 = pr.work_taken(r, 2026)
            regions[y][r] = dict(
                new_ai_users=round(100 * sum(pr.ai_use(c, y) - pr.ai_use(c, 2026) for c in cs) / len(cs), 3),
                robots=round(100 * (rob_now - rob_0), 3), ai_work=round(100 * (ai_now - ai_0), 3),
                tension_median=round(sorted(by_year[y][c["iso3"]] for c in cs)[len(cs) // 2], 3))
    states = {y: {s["abbr"]: round(by_year[y]["USA"] * pr.state_factor(s, y), 3) for s in S["us_states"]} for y in years}
    return dict(start="2026-01", years=list(years), amplify=AMPLIFY, slow=SLOW, robot_entry_pp=ROBOT_ENTRY,
                robot_entry_year={r: round(pr.robot_entry_year(r), 2) for r in REG},
                tension={str(y): v for y, v in by_year.items()},
                regions={str(y): v for y, v in regions.items()},
                us_states={str(y): v for y, v in states.items()},
                names={c["iso3"]: c["name"] for c in S["countries"]},
                region_of={c["iso3"]: c["region"] for c in S["countries"]})


def write(dest=None):
    dest = Path(dest or ROOT / "outputs" / "social_tension.json")
    data = build()
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = write()
    print("robot entry", d["robot_entry_year"])
    for y in ("2030", "2034", "2038", "2042", "2046"):
        t = d["tension"][y]
        top = sorted(t, key=lambda k: -t[k])[:6]
        print(y, {k: round(t[k]) for k in ("USA", "DEU", "JPN", "CHN", "IND", "BRA", "NGA", "YEM", "ISR")}, "top", [(k, round(t[k])) for k in top])
        print("   regions", d["regions"][y])
