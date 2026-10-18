"""The chapter on social risk (37) prints the projection of the Social Risk page: same rules, same numbers."""
import json
import math
import re
import unittest
from pathlib import Path

from aimodel.analysis import social_tension

ROOT = Path(__file__).resolve().parents[1]
BOOK_IT = Path(r"C:\BOOKS\NUOVAVERSIONE\campione_voce\riscrittura\37_capitolo.txt")
BOOK_EN = Path(r"C:\BOOKS\NUOVAVERSIONE\campione_voce\english\37_capitolo.txt")


def js_round(v):
    return int(math.floor(v + 0.5))


class TestSocialTension(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = json.loads((ROOT / "outputs" / "social_tension.json").read_text(encoding="utf-8"))

    def test_saved_file_matches_module(self):
        self.assertEqual(self.saved, json.loads(json.dumps(social_tension.build())))

    @unittest.skipUnless((ROOT / "simulator" / "social.html").exists(), "no social page in this copy")
    def test_page_uses_the_same_rules(self):
        html = (ROOT / "simulator" / "social.html").read_text(encoding="utf-8")
        self.assertEqual(float(re.search(r"const AMPLIFY = ([\d.]+);", html).group(1)), social_tension.AMPLIFY)
        m = re.search(r"const SLOW = ([\d.]+), ROBOT_ENTRY = ([\d.]+);", html)
        self.assertEqual((float(m.group(1)), float(m.group(2))), (social_tension.SLOW, social_tension.ROBOT_ENTRY))

    def test_order_from_2030(self):
        """Every advanced economy above every emerging one, every emerging one above every low-income country."""
        reg = self.saved["region_of"]
        for y in range(2030, 2047):
            t = self.saved["tension"][str(y)]
            lo = lambda r: min(v for k, v in t.items() if reg[k] == r)
            hi = lambda r: max(v for k, v in t.items() if reg[k] == r)
            self.assertGreater(lo("ADV"), hi("EME"), y)
            self.assertGreater(lo("EME"), hi("LIC"), y)

    def test_numbers_quoted_in_the_chapter(self):
        t46, t38 = self.saved["tension"]["2046"], self.saved["tension"]["2038"]
        r = self.saved["regions"]
        quoted = {("ISR", "2046"): 64, ("USA", "2046"): 60, ("GRC", "2046"): 60, ("DEU", "2046"): 59,
                  ("JPN", "2046"): 55, ("ARE", "2046"): 44, ("CHN", "2046"): 35}
        for (k, y), v in quoted.items():
            self.assertEqual(js_round(self.saved["tension"][y][k]), v, (k, y))
        self.assertEqual([js_round(r["2046"][x]["tension_median"]) for x in ("ADV", "EME", "LIC")], [56, 35, 18])
        self.assertEqual([js_round(r["2038"][x]["tension_median"]) for x in ("ADV", "EME", "LIC")], [37, 13, 2])
        s46, s38 = self.saved["us_states"]["2046"], self.saved["us_states"]["2038"]
        self.assertEqual([js_round(s38[k]) for k in ("UT", "ID", "DC")], [43, 42, 35])
        self.assertEqual([js_round(s46[k]) for k in ("IN", "SC", "GA", "UT", "ID", "TN")], [63] * 6)
        self.assertEqual([js_round(s46[k]) for k in ("IN", "NY", "DC", "CA", "TX")], [63, 57, 47, 61, 61])
        e = self.saved["robot_entry_year"]
        self.assertEqual([(int(e[x]), js_round((e[x] % 1) * 12) + 1) for x in ("ADV", "EME", "LIC")], [(2033, 3), (2037, 3), (2041, 12)])

    @unittest.skipUnless(BOOK_IT.exists() and BOOK_EN.exists(), "book texts not on this machine")
    def test_chapter_text_carries_the_numbers(self):
        it, en = BOOK_IT.read_text(encoding="utf-8"), BOOK_EN.read_text(encoding="utf-8")
        for needle in ("Israele, con 64 punti", "mediana di 56", "mediana di 35", "mediana di 18", "marzo 2033", "dicembre 2041",
                       "[[T:tensione_regioni]]", "[[T:tensione_paesi]]", "social.html"):
            self.assertIn(needle, it)
        for needle in ("Israel, with 64 points", "median of 56", "median of 35", "median of 18", "March 2033", "December 2041",
                       "[[T:tensione_regioni]]", "[[T:tensione_paesi]]", "social.html"):
            self.assertIn(needle, en)


if __name__ == "__main__":
    unittest.main()
