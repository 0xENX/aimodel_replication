"""Build observed charts and a clearly labelled EU age-profile proxy.

Only ADV initial age structure/participation/unemployment SHAPE is replaced.
ADV total initial unemployment remains the v2 structural rate. EU is not the
whole advanced-economy region; no AI elasticities are estimated here.
"""
import csv
import io
import json
import zipfile
from pathlib import Path
import numpy as np
from aimodel.core.employment import load_config, _expand

ROOT = Path(__file__).resolve().parent


def prepare(year=2025):
    folder = ROOT / "data" / "observed"
    rows = list(csv.DictReader((folder / "eurostat_stocks.csv").open(encoding="utf-8")))
    index = {(r["geo"], int(r["time"]), r["age"], r["wstatus"]): r for r in rows}
    bands = [(15, 24), (25, 34), (35, 49), (50, 64)]
    processed = []
    for geo in ("IT", "EU27_2020"):
        for y in range(2019, year + 1):
            for lo, hi in bands:
                totals, flags = {}, set()
                for status in ("POP", "ACT", "EMP", "UNE", "INAC"):
                    cells = [index.get((geo, y, f"Y{a}-{a+4}", status)) for a in range(lo, hi+1, 5)]
                    if any(c is None for c in cells):
                        raise ValueError(f"Missing cells: {geo}/{y}/{lo}-{hi}/{status}")
                    totals[status] = sum(float(c["value"]) for c in cells)
                    flags.update(c["flag"] for c in cells if c["flag"])
                processed.append(dict(geo=geo, year=y, age=f"{lo}-{hi}",
                    population_thousands=totals["POP"], labour_force_thousands=totals["ACT"],
                    employed_thousands=totals["EMP"], unemployed_thousands=totals["UNE"],
                    employment_rate=100*totals["EMP"]/totals["POP"],
                    participation_rate=100*totals["ACT"]/totals["POP"],
                    unemployment_rate=100*totals["UNE"]/totals["ACT"], flags=";".join(sorted(flags))))
    with (folder / "age_indicators.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(processed[0])); w.writeheader(); w.writerows(processed)
    c = load_config()
    latest = [r for r in processed if r["geo"] == "EU27_2020" and r["year"] == year]
    totalpop = sum(r["population_thousands"] for r in latest)
    c["population_shares"][0] = [r["population_thousands"]/totalpop for r in latest]
    c["participation"][0] = [r["participation_rate"]/100 for r in latest]
    c["unemployment_relative_by_region"] = [
        [r["unemployment_rate"]/100 for r in latest],
        c["unemployment_relative"].copy(), c["unemployment_relative"].copy()]
    popfine = _expand(np.asarray(c["population_shares"])/[10,10,15,15])
    partfine = _expand(c["participation"])
    for a in range(15,65,5):
        agecode = f"Y{a}-{a+4}"
        P = float(index[("EU27_2020",year,agecode,"POP")]["value"])
        L = float(index[("EU27_2020",year,agecode,"ACT")]["value"])
        popfine[0,a-15:a-10] = P/totalpop/5
        partfine[0,a-15:a-10] = L/P
    c["population_single_age"] = popfine.tolist()
    c["participation_single_age"] = partfine.tolist()
    c["status"] = "PARTIAL_EU_PROXY_CALIBRATION_AI_PARAMETERS_ASSUMED"
    c["sources"]["ADV_age_profile"] = f"Eurostat lfsa_pganws, EU27_2020, {year}, sex T, citizen TOTAL; five-year groups aggregated without averaging rates. Initial unemployment SHAPE is normalized to original ADV u_star. EU is a proxy, not all advanced economies."
    c["sources"]["all_age_numbers"] = "EME/LIC age profiles and all matching/turnover/AI coefficients remain assumptions. ADV structure and participation use observed EU aggregates; within five-year groups ages are uniform."
    dest = ROOT / "config" / "employment_eu_proxy.json"
    dest.write_text(json.dumps(c, indent=2), encoding="utf-8")
    stanford, dictionaries = {}, {}
    for filename in folder.glob("stanford_*.dat"):
        with zipfile.ZipFile(filename) as z:
            for n in z.namelist():
                # Read archive entries into memory; never trust extraction paths.
                if n.endswith(".csv") and "annualized" not in n and "yoy_change" not in n:
                    stanford[Path(n).stem] = list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8"))))
                elif n.endswith(".md"):
                    dictionaries[n] = z.read(n).decode("utf-8")
    flows = list(csv.DictReader((folder / "eurostat_flows.csv").open(encoding="utf-8")))
    flow_summary = [r for r in flows if r["s_adj"] == "NSA" and r["unit"] != "THS_PER"]
    obs = dict(eurostat=processed, stanford=stanford, stanford_dictionaries=dictionaries,
               eurostat_transitions=flow_summary,
               notes=["Eurostat stocks: Italy/EU, all occupations; no AI causal identification.",
                      "Eurostat downloaded flows have no age axis; do not use as age-specific hiring rates.",
                      "Stanford: US ADP balanced sample; native age groups preserved, exposure correlation is not causation.",
                      "Eurostat 2021 methodology break: interpret pre/post comparisons with caution."])
    (folder / "observed_summary.json").write_text(json.dumps(obs, indent=2), encoding="utf-8")
    print("Observed indicators and partial proxy prepared:", dest)
    for r in processed:
        if r["year"] == year:
            print(r["geo"],r["age"],"employment",round(r["employment_rate"],2),"unemployment",round(r["unemployment_rate"],2))
    for key in ("canaries_age_by_exposure", "canaries_software_developers"):
        if key in stanford:
            print(key, "last observations", stanford[key][-5:])
    return obs


if __name__ == "__main__":
    prepare()
