"""Copies the book's data into the simulator pages (between the BEGIN/END markers).

The job simulator and the book table read the same numbers; the social tensions page also reads the yearly
additional unemployment by region. Run after the two analysis modules:
    python -m aimodel.analysis.occupations
    python -m aimodel.analysis.unemployment_path
    python -m aimodel.analysis.social_risk
    python simulator/sync_occupations.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
occupations = json.loads((ROOT / "outputs" / "occupations.json").read_text(encoding="utf-8"))
unemployment = json.loads((ROOT / "outputs" / "unemployment_path.json").read_text(encoding="utf-8"))
social = json.loads((ROOT / "outputs" / "social_risk.json").read_text(encoding="utf-8"))


def inject(html, marker, name, data):
    block = "  const " + name + " = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    new, n = re.subn(r"(/\* " + marker + r":BEGIN[^\n]*\n).*?(  /\* " + marker + r":END \*/)",
                     lambda m: m.group(1) + block + m.group(2), html, flags=re.S)
    assert n == 1, marker + " markers not found"
    return new


for page, blocks in (("index.html", [("OCCUPATIONS", "DATA", occupations)]),
                     ("social.html", [("OCCUPATIONS", "DATA", occupations), ("UNEMP", "UNEMP", unemployment), ("SOCIAL", "SOCIAL", social)])):
    p = ROOT / "simulator" / page
    html = p.read_text(encoding="utf-8")
    for marker, name, data in blocks:
        html = inject(html, marker, name, data)
    p.write_text(html, encoding="utf-8")
    print(page, "updated")
