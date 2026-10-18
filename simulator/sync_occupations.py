"""Copies outputs/occupations.json into simulator/index.html (between the OCCUPATIONS markers).

The job simulator and the book table read the same numbers. Run after aimodel/analysis/occupations.py:
    python -m aimodel.analysis.occupations
    python simulator/sync_occupations.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
page = ROOT / "simulator" / "index.html"
data = json.loads((ROOT / "outputs" / "occupations.json").read_text(encoding="utf-8"))
html = page.read_text(encoding="utf-8")
block = "  const DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
new, n = re.subn(r"(/\* OCCUPATIONS:BEGIN[^\n]*\n).*?(  /\* OCCUPATIONS:END \*/)", lambda m: m.group(1) + block + m.group(2), html, flags=re.S)
assert n == 1, "markers not found"
page.write_text(new, encoding="utf-8")
print("simulator updated with", len(data["occupations"]), "occupations")
