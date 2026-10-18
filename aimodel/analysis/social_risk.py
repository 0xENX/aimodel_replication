"""Country data for the Social Risk page: starting risk, AI use, the book's region of each country.

Sources (archived in data/observed/social, downloaded 18 October 2026, not modified):
- Starting risk: World Bank, Worldwide Governance Indicators, "Political Stability and Absence of
  Violence/Terrorism" (GOV_WGI_PV.EST), 2024 estimate, scale about -2.5 to +2.5 (wgi_pv_2024.json, CC BY 4.0).
  Risk on 0-100 = (2.5 - estimate) / 5 x 100: higher means less stable.
- AI use: Our World in Data, "Estimated share of people using generative AI" (owid_genai.csv), from Microsoft
  AI Economy Institute, share of the working-age population, quarterly 2025-06 to 2026-03 (CC BY 4.0).
- United States by state: BLS Occupational Employment and Wage Statistics, May 2024, state file
  (oews_state_M2024_dl.xlsx, public domain): employment of the nineteen occupations in each state, so that the work
  taken by AI and robots follows the occupations of the state. Doctors are all physicians (29-121x, 29-122x, 29-124x);
  the few suppressed cells take the national share of the occupation.
- China and Russia by large city: no comparable data on occupations by city, so every city carries the value of its
  country; the cities only show where people live (city centre coordinates).
- Codes: ISO 3166 alpha-3 and numeric (iso_codes.json, from the npm package i18n-iso-countries 7.11.0) and the
  World Bank country list with regions and capital coordinates (wb_countries.json).

The book's regions follow the IMF groups used for the exposure (chapter 6): advanced = the IMF list of advanced
economies (World Economic Outlook); low-income = World Bank low income, plus lower middle income in sub-Saharan
Africa; every other country emerging.
After the last observation the page lets AI use grow along the book's adoption curve up to the share of
employment exposed to AI in the region (calibration exposure 60/40/26 percent, IMF, chapter 6).
Social tension on the page = work taken by AI and robots since the start (scaled by the region's exposure, shared
by AI take-up) x (1 + 0.5 x risk / 100). The starting risk amplifies, it is not shown; the book has no estimated link to unrest (chapter 17).
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

from aimodel.calibration.data import CAL

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "observed" / "social"

# IMF World Economic Outlook, advanced economies
IMF_ADVANCED = {"AND", "AUS", "AUT", "BEL", "CAN", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "GRC",
                "HKG", "ISL", "IRL", "ISR", "ITA", "JPN", "KOR", "LVA", "LTU", "LUX", "MAC", "MLT", "NLD", "NZL",
                "NOR", "PRT", "PRI", "SMR", "SGP", "SVK", "SVN", "ESP", "SWE", "CHE", "TWN", "GBR", "USA"}


def book_region(iso3, wb_region, income):
    if iso3 in IMF_ADVANCED:
        return "ADV"
    if income == "Low income" or (income == "Lower middle income" and wb_region.strip() == "Sub-Saharan Africa"):
        return "LIC"
    return "EME"


# SOC codes of the nineteen occupations in the OEWS files (same as the book table; physicians summed)
OEWS_SOC = {"clerk": ["43-9061"], "accountant": ["13-2011"], "callcenter": ["43-4051"], "translator": ["27-3091"],
            "developer": ["15-1252"], "designer": ["27-1024"], "journalist": ["27-3023"], "architect": ["15-1211"],
            "lawyer": ["23-1011"], "doctor": ["29-121", "29-122", "29-124"], "nurse": ["29-1141"],
            "teacher": ["25-2031"], "retail": ["41-2031"], "driver": ["53-3032"], "warehouse": ["53-7062"],
            "factory": ["51-2090"], "cook": ["35-2014"], "construction": ["47-2061"], "electrician": ["47-2111", "47-2152"]}
US_STATES_FIPS = {"AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10", "DC": "11",
                  "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21",
                  "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30",
                  "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
                  "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47", "TX": "48", "UT": "49",
                  "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56"}

# large cities: English name, Italian name, longitude, latitude (city centre)
CITIES = {
    "CHN": [("Shanghai", "Shanghai", 121.47, 31.23), ("Beijing", "Pechino", 116.41, 39.90), ("Chongqing", "Chongqing", 106.55, 29.56),
            ("Guangzhou", "Canton", 113.26, 23.13), ("Shenzhen", "Shenzhen", 114.06, 22.54), ("Chengdu", "Chengdu", 104.07, 30.57),
            ("Tianjin", "Tientsin", 117.20, 39.13), ("Wuhan", "Wuhan", 114.31, 30.59), ("Xi'an", "Xi'an", 108.94, 34.34),
            ("Hangzhou", "Hangzhou", 120.16, 30.27), ("Nanjing", "Nanchino", 118.80, 32.06), ("Shenyang", "Shenyang", 123.43, 41.80),
            ("Harbin", "Harbin", 126.53, 45.80), ("Zhengzhou", "Zhengzhou", 113.63, 34.75), ("Kunming", "Kunming", 102.83, 24.88),
            ("Urumqi", "Ürümqi", 87.62, 43.83), ("Lanzhou", "Lanzhou", 103.83, 36.06), ("Changsha", "Changsha", 112.94, 28.23)],
    "RUS": [("Moscow", "Mosca", 37.62, 55.76), ("Saint Petersburg", "San Pietroburgo", 30.31, 59.94), ("Novosibirsk", "Novosibirsk", 82.92, 55.03),
            ("Yekaterinburg", "Ekaterinburg", 60.60, 56.84), ("Kazan", "Kazan'", 49.11, 55.80), ("Nizhny Novgorod", "Nižnij Novgorod", 44.00, 56.33),
            ("Chelyabinsk", "Čeljabinsk", 61.40, 55.16), ("Krasnoyarsk", "Krasnojarsk", 92.87, 56.01), ("Samara", "Samara", 50.10, 53.20),
            ("Rostov-on-Don", "Rostov sul Don", 39.72, 47.24), ("Omsk", "Omsk", 73.37, 54.99), ("Irkutsk", "Irkutsk", 104.28, 52.29),
            ("Khabarovsk", "Chabarovsk", 135.07, 48.48), ("Vladivostok", "Vladivostok", 131.89, 43.12)],
}


def us_states():
    """Employment of the nineteen occupations by state, BLS OEWS May 2024."""
    import openpyxl
    ws = openpyxl.load_workbook(RAW / "oews_state_M2024_dl.xlsx", read_only=True).active
    emp, total = defaultdict(dict), {}
    names = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        st, occ, n = r[3], r[8], r[11]
        if st not in US_STATES_FIPS or r[10] not in ("total", "detailed", "broad"):
            continue
        names[st] = r[1]
        if occ == "00-0000":
            total[st] = n
            continue
        for oid, codes in OEWS_SOC.items():
            if any(occ == c or (len(c) == 6 and occ.startswith(c) and r[10] == "detailed") for c in codes):
                emp[st].setdefault(oid, []).append(n if isinstance(n, (int, float)) else None)
    # suppressed cells: national share of the occupation times the state's employment
    nat = {oid: sum(v for st in emp for v in emp[st].get(oid, []) if v) for oid in OEWS_SOC}
    nat_total = sum(total.values())
    out = []
    for st, fips in sorted(US_STATES_FIPS.items(), key=lambda kv: -total[kv[0]]):
        w = {}
        for oid in OEWS_SOC:
            vals = emp[st].get(oid, [])
            w[oid] = sum(v for v in vals if v) if vals and all(v is not None for v in vals) else round(nat[oid] / nat_total * total[st])
        out.append(dict(abbr=st, fips=fips, name=names[st], employment=total[st], weights=w))
    return out


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
            iso3=iso3, iso2=c["iso2Code"], num=num.get(iso3), name=c["name"], region=book_region(iso3, c["region"]["value"], c["incomeLevel"]["value"]),
            wgi=round(v, 3), risk=round(max(0.0, min(100.0, (2.5 - v) / 5 * 100)), 1),
            lon=float(c["longitude"]) if c["longitude"] else None, lat=float(c["latitude"]) if c["latitude"] else None,
            ai_use=ai.get(iso3, {})))
    return dict(
        sources=dict(us_states="BLS OEWS May 2024, state employment by occupation",
                     risk="World Bank WGI, Political Stability and Absence of Violence/Terrorism, 2024 (GOV_WGI_PV.EST)",
                     ai_use="Our World in Data / Microsoft AI Economy Institute, share of working-age population using generative AI",
                     downloaded="2026-10-18"),
        exposure=dict(zip(("ADV", "EME", "LIC"), [round(float(x), 2) for x in CAL["exposure"]])),
        ai_dates=sorted({d for v in ai.values() for d in v}),
        countries=countries,
        us_states=us_states(),
        cities={k: [dict(name=en, it=it, lon=lon, lat=lat) for en, it, lon, lat in v] for k, v in CITIES.items()})


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
