"""The forecast by occupation has one source: the book table and the simulator must show the same numbers."""
import json
import re
import unittest
from pathlib import Path

from aimodel.analysis import occupations

ROOT = Path(__file__).resolve().parents[1]


class TestOccupations(unittest.TestCase):
    def test_saved_file_matches_module(self):
        saved = json.loads((ROOT / "outputs" / "occupations.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["occupations"], json.loads(json.dumps(occupations.forecast())))

    @unittest.skipUnless((ROOT / "simulator" / "index.html").exists(), "no simulator in this copy")
    def test_simulator_uses_saved_file(self):
        html = (ROOT / "simulator" / "index.html").read_text(encoding="utf-8")
        block = re.search(r"const DATA = (\{.*?\});\n", html, re.S).group(1)
        saved = json.loads((ROOT / "outputs" / "occupations.json").read_text(encoding="utf-8"))
        self.assertEqual(json.loads(block), saved)

    def test_no_loss_above_cap(self):
        for o in occupations.forecast():
            for v in o["results"].values():
                self.assertGreaterEqual(v, -100 * occupations.CAP)


if __name__ == "__main__":
    unittest.main()
