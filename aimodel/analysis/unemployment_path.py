"""Additional unemployment by region, year by year (book, chapter 14; job simulator, social tension).

Same Monte Carlo as the book's results (4,000 paired draws, seed 20261010): for each region and year the median
of the paired difference in the unemployment rate, world with AI minus world without AI, in percentage points.
The job simulator draws its social tension patch from this series: the book does not measure social unrest
(chapter 17), so the patch is a picture of the additional unemployment in the region, not a measure of disorder.
"""
import json
import sys
import types
from pathlib import Path

import numpy as np

# montecarlo.py imports SALib only for the Sobol analysis; this module needs the draws, so empty modules stand in
for _name in ("SALib", "SALib.sample", "SALib.analyze"):
    sys.modules.setdefault(_name, types.ModuleType(_name))
for _name in ("SALib.sample", "SALib.analyze"):
    if not hasattr(sys.modules[_name], "sobol"):
        sys.modules[_name].sobol = None

from aimodel.analysis.montecarlo import run_mc  # noqa: E402
from aimodel.calibration.data import START_YEAR, END_YEAR  # noqa: E402

REGIONS = ("ADV", "EME", "LIC")


def path(n=4000, seed=20261010):
    _, base, ai, _ = run_mc(n, seed=seed)
    years = list(range(START_YEAR, END_YEAR + 1))
    out = {}
    for r, name in enumerate(REGIONS):
        diff = (ai["unemp"][:, :, r] - base["unemp"][:, :, r]) * 100
        out[name] = [round(float(v), 3) for v in np.median(diff, axis=1)]
    return {"years": years, "draws": n, "seed": seed, "unit": "pp", "median_additional_unemployment": out}


def write(dest=None):
    dest = Path(dest or Path(__file__).resolve().parents[2] / "outputs" / "unemployment_path.json")
    data = path()
    dest.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = write()
    for r, v in d["median_additional_unemployment"].items():
        peak = max(v); print(r, "2036", v[d["years"].index(2036)], "2046", v[-1], "peak", peak, "in", d["years"][v.index(peak)])
