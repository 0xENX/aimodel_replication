"""Download official observations; archive raw responses and provenance.

Network is required only here. Simulations and reports run entirely offline.
Eurostat public LFS aggregates do not identify the causal effect of AI.
Stanford aggregate indices cover an ADP balanced sample, not the entire US.
"""
import argparse
import csv
import hashlib
import itertools
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def decode_jsonstat(d):
    dims = d["id"]
    ordered = []
    for dim in dims:
        index = d["dimension"][dim]["category"]["index"]
        ordered.append(sorted(index, key=index.get) if isinstance(index, dict) else index)
    values, flags = d.get("value", {}), d.get("status") or {}
    for flat, coords in enumerate(itertools.product(*ordered)):
        v = values[flat] if isinstance(values, list) else values.get(str(flat))
        if v is None:
            continue
        flag = flags[flat] if isinstance(flags, list) else flags.get(str(flat), "")
        yield dict(zip(dims, coords), value=v, flag=flag or "")


def save_csv(path, rows):
    rows = list(rows)
    if not rows:
        raise ValueError(f"No observations: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


class DataLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self.href = None; self.label = ""
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href"); self.label = ""
    def handle_data(self, data):
        if self.href:
            self.label += data
    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            if self.label.strip().lower() == "data" and urlparse(self.href).hostname == "storage.googleapis.com":
                self.links.append(self.href)
            self.href = None


def download(out, name, url, manifest):
    raw = urlopen(url, timeout=45).read()
    (out / name).write_bytes(raw)
    manifest.append(dict(file=name, url=url, retrieved_utc=datetime.now(timezone.utc).isoformat(),
                         sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    return raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    args = ap.parse_args()
    out = ROOT / "data" / "observed"
    out.mkdir(parents=True, exist_ok=True)
    manifest, all_rows = [], []
    for geo in ("IT", "EU27_2020"):
        query = urlencode(dict(lang="EN", geo=geo, sex="T", citizen="TOTAL",
                               sinceTimePeriod=2019, untilTimePeriod=args.year))
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsa_pganws?" + query
        d = json.loads(download(out, f"eurostat_{geo}.json", url, manifest))
        rows = list(decode_jsonstat(d)); all_rows.extend(rows)
        print(geo, "stock observations", len(rows), "age codes", sorted({r["age"] for r in rows}))
    save_csv(out / "eurostat_stocks.csv", all_rows)
    # Fetch all published age groups: inspect availability, do not fabricate age flows.
    transitions = []
    for geo in ("IT", "EU27_2020"):
        query = urlencode(dict(lang="EN", geo=geo, sex="T", sinceTimePeriod="2024-Q1", untilTimePeriod="2025-Q4"))
        url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/lfsi_long_q?" + query
        try:
            d = json.loads(download(out, f"eurostat_flows_{geo}.json", url, manifest))
            rows = list(decode_jsonstat(d)); transitions.extend(rows)
            print(geo, "transition dimensions", d["id"], "cells", len(rows))
        except Exception as exc:
            manifest.append(dict(file=f"eurostat_flows_{geo}.json", url=url, error=str(exc)))
    if transitions:
        save_csv(out / "eurostat_flows.csv", transitions)
    page_url = "https://digitaleconomy.stanford.edu/project/indicators/canaries-dashboard/"
    try:
        page = download(out, "stanford_dashboard.html", page_url, manifest).decode("utf-8")
        parser = DataLinks(); parser.feed(page)
        # Index, age x exposure, age totals, sample composition, software, customer support.
        for i, url in enumerate(parser.links[:6]):
            suffix = ".csv" if ".csv" in url.lower() else ".dat"
            download(out, f"stanford_{i:02d}{suffix}", url, manifest)
        print("Stanford downloadable tables", min(len(parser.links), 6))
    except Exception as exc:
        manifest.append(dict(url=page_url, error=str(exc)))
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Observations archived in", out)


if __name__ == "__main__":
    main()
