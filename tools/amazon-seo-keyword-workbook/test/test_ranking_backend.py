"""Optional backend (generic_keyword) scoring in ranking_score.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

import ranking_score as rs  # noqa: E402

KWS = [("blue widget", 1000), ("travel case", 400), ("steel hinge", 200)]
BASE_KEYS = {
    "title", "bullets", "description", "total", "max_possible", "pct_of_max",
    "keywords_credited", "keywords_scored", "weights", "highlights_field",
}
BACKEND_KEYS = {
    "backend", "backend_weight", "backend_weighted", "backend_keywords_credited",
    "total_with_backend", "pct_of_max_with_backend",
}


class BackendAbsentTest(unittest.TestCase):
    def test_without_backend_the_result_keeps_the_original_shape_and_values(self):
        plain = rs.score_listing(KWS, "Blue Widget", ["A travel case"], "steel")
        for empty in (None, "", "   ", []):
            with self.subTest(backend=empty):
                self.assertEqual(rs.score_listing(KWS, "Blue Widget", ["A travel case"], "steel", backend=empty), plain)
        self.assertEqual(set(plain), BASE_KEYS)
        self.assertEqual(plain["weights"], rs.DEFAULT_WEIGHTS)
        self.assertEqual(plain["total"], 3 * 1000 + 2 * 400)

    def test_backend_weight_alone_does_not_change_a_listing_without_backend(self):
        plain = rs.score_listing(KWS, "Blue Widget", [])
        weighted = rs.score_listing(KWS, "Blue Widget", [], weights={"backend": 5})
        self.assertEqual(plain, weighted)

    def test_listings_from_data_adds_no_key_for_existing_inputs(self):
        items = rs.listings_from_data({"listings": [{"asin": "B0TEST0001", "title": "Blue Widget", "bullets": "a\nb"}]})
        self.assertEqual(items, [{"asin": "B0TEST0001", "title": "Blue Widget", "bullets": ["a", "b"],
                                  "description": "", "item_highlights": ""}])


class BackendPresentTest(unittest.TestCase):
    def test_backend_is_scored_after_the_visible_fields(self):
        s = rs.score_listing(KWS, "Blue Widget", [], "", backend="travel case hinge steel")
        self.assertEqual(set(s), BASE_KEYS | BACKEND_KEYS)
        self.assertEqual(s["total"], 3 * 1000)
        self.assertEqual(s["pct_of_max"], round(100 * 3000 / (3 * 1600), 2))
        # travel case exact (1.0 x 400), steel hinge any order (0.5 x 200)
        self.assertEqual(s["backend"], 400 + 100)
        self.assertEqual(s["backend_keywords_credited"], 2)
        self.assertEqual(s["backend_weight"], 1.0)
        self.assertEqual(s["backend_weighted"], 500)
        self.assertEqual(s["total_with_backend"], 3500)
        self.assertEqual(s["pct_of_max_with_backend"], round(100 * 3500 / 4800, 2))
        self.assertNotIn("backend", s["weights"])

    def test_backend_only_earns_the_improvement_over_higher_fields(self):
        s = rs.score_listing([("blue widget", 1000)], "Widget, blue", ["in blue"], "", backend="blue widget")
        self.assertEqual(s["title"], 500)
        self.assertEqual(s["bullets"], 0)
        self.assertEqual(s["backend"], 500)
        none = rs.score_listing([("blue widget", 1000)], "Blue Widget", [], "", backend="blue widget")
        self.assertEqual(none["backend"], 0)
        self.assertEqual(none["backend_keywords_credited"], 0)

    def test_backend_weight_key(self):
        s = rs.score_listing(KWS, "", [], "", backend="travel case", weights={"backend": 0.5, "title": 2})
        self.assertEqual(s["backend_weight"], 0.5)
        self.assertEqual(s["backend_weighted"], 200)
        self.assertEqual(s["weights"]["title"], 2.0)

    def test_listings_from_data_passes_backend_through(self):
        data = {"listings": [
            {"asin": "B0TEST0001", "title": "t", "backend": "travel case"},
            {"asin": "B0TEST0002", "title": "t", "generic_keyword": [{"value": "steel hinge", "marketplace_id": "ATVPDKIKX0DER"}]},
            {"asin": "B0TEST0003", "title": "t", "item_highlights": "Travel Case", "generic_keyword": ""},
        ]}
        items = rs.listings_from_data(data)
        self.assertEqual(items[0]["backend"], "travel case")
        self.assertEqual(items[1]["backend"], "steel hinge")
        self.assertNotIn("backend", items[2])
        self.assertEqual(items[2]["item_highlights"], "Travel Case")
        scored = rs.score_entry(KWS, items[1])
        self.assertEqual(scored["backend"], 200)

    def test_cli_reports_backend_separately(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core.csv").write_text("#,Search Terms,SV\n1,blue widget,1000\n2,travel case,400\n", encoding="utf-8")
            (root / "listing.json").write_text(json.dumps({"listings": [
                {"asin": "B0TEST0001", "title": "Blue Widget", "backend": "travel case"},
                {"asin": "B0TEST0002", "title": "Blue Widget"},
            ]}), encoding="utf-8")
            base = [sys.executable, str(TOOL_DIR / "ranking_score.py"), "--keywords", str(root / "core.csv"),
                    "--listing", str(root / "listing.json")]
            out = json.loads(subprocess.run(base + ["--json"], capture_output=True, text=True, check=True).stdout)
            rows = {r["name"]: r for r in out["rows"]}
            self.assertEqual(rows["B0TEST0001"]["total"], rows["B0TEST0002"]["total"])
            self.assertEqual(rows["B0TEST0001"]["total_with_backend"], 3000 + 400)
            self.assertFalse(BACKEND_KEYS & set(rows["B0TEST0002"]))
            table = subprocess.run(base, capture_output=True, text=True, check=True).stdout
            self.assertIn("Backend search terms", table)


if __name__ == "__main__":
    unittest.main()
