"""Country data for the Social Risk page: starting risk, AI use, the book's region of each country.

Sources (archived in data/observed/social, downloaded 18 October 2026, not modified):
- Starting risk: World Bank, Worldwide Governance Indicators, "Political Stability and Absence of
  Violence/Terrorism" (GOV_WGI_PV.EST), 2024 estimate, scale about -2.5 to +2.5 (wgi_pv_2024.json, CC BY 4.0).
  Risk on 0-100 = (2.5 - estimate) / 5 x 100: higher means less stable.
- AI use: Our World in Data, "Estimated share of people using generative AI" (owid_genai.csv), from Microsoft
  AI Economy Institute, share of the working-age population, quarterly 2025-06 to 2026-03 (CC BY 4.0).
- Codes: ISO 3166 alpha-3 and numeric (iso_codes.json, from the npm package i18n-iso-countries 7.11.0) and the
  World Bank country list with regions and capital coordinates (wb_countries.json).

The book's regions (advanced, emerging, low-income) follow the job simulator: USA, Canada, Japan, Europe and
Oceania advanced; China, India, Russia, the rest of Asia and the Americas emerging; Africa low-income.
After the last observation the page lets AI use grow along the book's adoption curve up to the share of
employment exposed to AI in the region (calibration exposure 60/40/26 percent, IMF, chapter 6).
Social tension on the page = work lost in the region since the start, shared by AI and robot take-up, x (1 + 2 x
risk / 100). The starting risk amplifies, it is not shown; the book has no estimated link to unrest (chapter 17).
"""
import csv
import json
from pathlib import Path

from aimodel.calibration.data import CAL

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "observed" / "social"

CENTRAL_ASIA = {"KAZ", "UZB", "KGZ", "TJK", "TKM", "AZE", "ARM", "GEO", "TUR", "RUS"}
NORTH_AFRICA = {"DZA", "EGY", "LBY", "MAR", "TUN", "DJI"}
OCEANIA = {"AUS", "NZL", "FJI", "PNG", "SLB", "VUT", "WSM", "TON", "KIR", "FSM", "MHL", "PLW", "NRU", "TUV",
           "NCL", "PYF", "GUM", "ASM", "MNP"}


def book_region(iso3, wb_region):
    r = wb_region.strip()
    if iso3 in ("USA", "CAN", "BMU", "JPN") or iso3 in OCEANIA:
        return "ADV"
    if r == "Europe & Central Asia":
        return "EME" if iso3 in CENTRAL_ASIA else "ADV"
    if r == "Sub-Saharan Africa" or iso3 in NORTH_AFRICA:
        return "LIC"
    return "EME"   # rest of Asia, Middle East, South Asia, Latin America & Caribbean


def build():
    wb = {c["id"]: c for c in json.loads((RAW / "wb_countries.json").read_text(encoding="utf-8"))[1]
          if c["region"]["value"].strip() != "Aggregates"}
    wgi = {r["countryiso3code"]: r["value"] for r in json.loads((RAW / "wgi_pv_2024.json").read_text(encoding="utf-8"))[1]
           if r["value"] is not None and r["countryiso3code"]}
    num = {a3: n for _, a3, n, _ in json.loads((RAW / "iso_codes.json").read_text(encoding="utf-8"))}
    ai = {}
    with open(RAW / "owid_genai.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["code"] and row["ai_user_share"]:
                ai.setdefault(row["code"], {})[row["day"]] = float(row["ai_user_share"])
    countries = []
    for iso3, v in sorted(wgi.items()):
        if iso3 not in wb:
            continue
        c = wb[iso3]
        countries.append(dict(
            iso3=iso3, iso2=c["iso2Code"], num=num.get(iso3), name=c["name"], region=book_region(iso3, c["region"]["value"]),
            wgi=round(v, 3), risk=round(max(0.0, min(100.0, (2.5 - v) / 5 * 100)), 1),
            lon=float(c["longitude"]) if c["longitude"] else None, lat=float(c["latitude"]) if c["latitude"] else None,
            ai_use=ai.get(iso3, {})))
    return dict(
        sources=dict(risk="World Bank WGI, Political Stability and Absence of Violence/Terrorism, 2024 (GOV_WGI_PV.EST)",
                     ai_use="Our World in Data / Microsoft AI Economy Institute, share of working-age population using generative AI",
                     downloaded="2026-10-18"),
        exposure=dict(zip(("ADV", "EME", "LIC"), [round(float(x), 2) for x in CAL["exposure"]])),
        ai_dates=sorted({d for v in ai.values() for d in v}),
        countries=countries)


def write(dest=None):
    dest = Path(dest or ROOT / "outputs" / "social_risk.json")
    data = build()
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = write()
    cs = d["countries"]
    print(len(cs), "countries;", sum(1 for c in cs if c["ai_use"]), "with AI use data;", "exposure", d["exposure"])
    for iso in ("USA", "CAN", "ITA", "FRA", "DEU", "CHN", "IND", "RUS", "BRA", "NGA", "ARE"):
        c = next(x for x in cs if x["iso3"] == iso)
        print(iso, c["region"], "risk", c["risk"], "AI", c["ai_use"].get("2026-03-31"))
    from collections import Counter
    print(Counter(c["region"] for c in cs))
