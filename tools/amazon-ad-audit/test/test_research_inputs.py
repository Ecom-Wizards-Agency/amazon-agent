"""research.json (tools/soldscope/keywords.py) drives the audit readers; DataDive keys still read."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from analyze_audit import (  # noqa: E402
    parse_datadive,
    parse_research,
    research_keywords_csv,
    research_meta,
    research_paths,
)
from build_audit import preflight  # noqa: E402
from build_audit_workbook import _adapt_competitors  # noqa: E402

RESEARCH = {
    "provider": "soldscope",
    "source": "keyword_research_search_multi_asin",
    "search_id": 90001,
    "marketplace": "US",
    "asins": ["B0TEST0001", "B0TEST0002", "B0TEST0003"],
    "anchor": "B0TEST0001",
    "date_from": "2026-10-01",
    "date_to": "2026-10-31",
    "created_at": "2026-11-01T09:00:00Z",
    "statistics": {"numKeywords": 3},
    "keywords": [
        {"keyword": "test widget", "searchVolume": 900, "relevancy": 0.8,
         "asinRanks": {"B0TEST0001": 7, "B0TEST0002": 2, "B0TEST0003": None}, "origin": "core"},
        {"keyword": "test widget large", "searchVolume": 300, "relevancy": 0.5,
         "asinRanks": {"B0TEST0001": None, "B0TEST0002": 101, "B0TEST0003": 4}, "origin": "pool"},
        {"keyword": "widget", "searchVolume": 5000, "relevancy": 0.4,
         "asinRanks": {"B0TEST0001": 40, "B0TEST0002": 12, "B0TEST0003": 9}, "origin": "pool"},
    ],
    "competitors": [
        {"asin": "B0TEST0001", "brand": "Testbrand", "price": 20.0, "rating": 4.4,
         "reviewCount": 120, "reviews": 120, "revenue": 9000, "sellerCountry": "",
         "category": "Test Category", "advertisedKws": 30, "kwRankedOnP1Percent": 0.4,
         "isAnchor": True},
        {"asin": "B0TEST0002", "brand": "Rival One", "price": 25.0, "rating": 4.6,
         "reviewCount": 800, "reviews": 800, "revenue": 20000, "sellerCountry": "",
         "category": "Test Category", "advertisedKws": 50, "kwRankedOnP1Percent": 0.7,
         "isAnchor": False},
        {"asin": "B0TEST0003", "brand": "Rival Two", "price": 18.0, "rating": 4.1,
         "reviewCount": 60, "reviews": 60, "revenue": 4000, "sellerCountry": "",
         "category": "Test Category", "advertisedKws": 10, "kwRankedOnP1Percent": 0.2,
         "isAnchor": False},
    ],
    "benchmark": {"price": 20.0, "reviewCount": 120, "rating": 4.4,
                  "basis": "median of 3 compared ASINs"},
}

LEGACY_NICHE = {"keywords": [{"keyword": "test widget", "searchVolume": 900, "relevancy": 0.8,
                              "asinRanks": {"B0TEST0001": 5}}]}


class ResearchInputsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, payload):
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def _cfg(self, **inputs):
        return {"client": "Example", "marketplaces": ["US"], "amazon_account": "Example Seller",
                "asin_groups": {"Main": ["B0TEST0001"]},
                "windows": {"ads": "2026-10-01..2026-10-31",
                            "business_report": "2026-10-01..2026-10-31", "sqp_weeks": []},
                "inputs": inputs}

    def test_one_research_json_feeds_keywords_and_competitors(self):
        path = self._write("research.json", RESEARCH)
        paths = research_paths(self._cfg(research_json=path))
        self.assertEqual(paths["keywords"], path)
        self.assertEqual(paths["competitors"], path)
        self.assertFalse(paths["legacy"])

    def test_research_json_wins_over_legacy_keys(self):
        path = self._write("research.json", RESEARCH)
        legacy = self._write("niche.json", LEGACY_NICHE)
        cfg = self._cfg(research_json=path, datadive_niche_json=legacy,
                        datadive_competitors_json=legacy)
        self.assertEqual(research_paths(cfg)["keywords"], path)
        self.assertEqual(research_meta(cfg)["provider"], "SoldScope")

    def test_soldscope_labels_and_sources_line(self):
        meta = research_meta(self._cfg(research_json=self._write("research.json", RESEARCH)))
        self.assertEqual(meta["provider"], "SoldScope")
        self.assertFalse(meta["legacy"])
        self.assertEqual(meta["window"], "2026-10-01..2026-10-31")
        self.assertEqual(meta["median_label"], "median of the 3 compared ASINs")
        self.assertIn("search_id 90001", meta["source_line"])
        self.assertIn("B0TEST0001, B0TEST0002, B0TEST0003", meta["source_line"])
        self.assertNotIn("niche", meta["source_line"].lower())

    def test_research_json_drives_parsing(self):
        cfg = self._cfg(research_json=self._write("research.json", RESEARCH))
        cfg["asin_groups"] = {"Main": ["B0TEST0001", "B0TEST0003"]}
        agg = {}
        parse_research(cfg, agg)
        self.assertEqual(agg["dd"]["provider"], "SoldScope")
        best = {row["kw"]: row["rank"] for row in agg["dd"]["keywords"]}
        # Only the Core rows count, the equivalent of DataDive's visible MKL.
        self.assertEqual(best, {"test widget": 7})
        self.assertIs(parse_datadive, parse_research)

    def test_legacy_rows_without_origin_all_count(self):
        legacy = json.loads(json.dumps(RESEARCH))
        for k in legacy["keywords"]:
            k.pop("origin", None)
        cfg = self._cfg(research_json=self._write("legacy.json", legacy))
        cfg["asin_groups"] = {"Main": ["B0TEST0001", "B0TEST0003"]}
        agg = {}
        parse_research(cfg, agg)
        best = {row["kw"]: row["rank"] for row in agg["dd"]["keywords"]}
        self.assertEqual(best, {"test widget": 7, "test widget large": 4, "widget": 9})

    def test_research_json_drives_preflight(self):
        path = self._write("research.json", RESEARCH)
        cfg = self._cfg(research_json=path)
        cfg["research"] = {"marketplace": "US", "asins": RESEARCH["asins"]}
        out = io.StringIO()
        with redirect_stdout(out):
            preflight(cfg, "config.example-us.json")
        rendered = out.getvalue()
        self.assertIn(f"[OK] SoldScope research.json (keywords + competitors)  ->  {path}", rendered)
        self.assertNotIn("MISSING SOLDSCOPE MCP INPUTS", rendered)

    def test_competitors_from_research_json(self):
        comp = _adapt_competitors(RESEARCH, {"B0TEST0001"})
        self.assertEqual(comp["category"], "Test Category")
        self.assertEqual(comp["num_keywords"], 3)
        self.assertEqual(comp["median_price"], 20.0)
        self.assertEqual(comp["median_reviews"], 120)
        self.assertEqual([c["asin"] for c in comp["competitors"] if c["is_client"]], ["B0TEST0001"])
        derived = {"competitors": [], "median_price": 1}
        self.assertIs(_adapt_competitors(derived, set()), derived)

    def test_price_phrase_names_the_compared_asins(self):
        from build_audit_workbook import _price_phrase
        self.assertEqual(_price_phrase({"premium": 0.25}, "median of the 3 compared ASINs"),
                         "price sits 25% above the median of the 3 compared ASINs")
        self.assertEqual(_price_phrase({"premium": 0.25}), "price sits 25% above the category median")

    def test_legacy_datadive_keys_keep_datadive_labels(self):
        cfg = self._cfg(datadive_niche_json=self._write("niche.json", LEGACY_NICHE),
                        rank_radar_json=self._write("radar.json", []))
        cfg["datadive_niche"] = "niche-123"
        cfg["windows"]["datadive"] = "2026-09-30"
        meta = research_meta(cfg)
        self.assertEqual(meta["provider"], "DataDive")
        self.assertTrue(meta["legacy"])
        self.assertEqual(meta["source_line"], "DataDive niche niche-123")
        self.assertEqual(meta["window"], "2026-09-30")
        self.assertEqual(meta["median_label"], "category median")
        self.assertEqual(meta["rank_provider"], "DataDive")
        self.assertTrue(research_paths(cfg)["rank_series"].endswith("radar.json"))
        agg = {}
        parse_research(cfg, agg)
        self.assertEqual(agg["dd"]["keywords"][0]["rank"], 5)

    def test_rank_series_key_and_window_alias(self):
        cfg = self._cfg(rank_series_json=self._write("ranks.json", []),
                        rank_radar_json=self._write("radar.json", []))
        cfg["windows"]["research"] = "2026-10-01..2026-10-31"
        self.assertTrue(research_paths(cfg)["rank_series"].endswith("ranks.json"))
        self.assertEqual(research_meta(cfg)["rank_provider"], "SoldScope")
        self.assertIsNone(research_meta(cfg)["provider"])

    def test_keywords_csv_falls_back_to_legacy_name(self):
        clean = self.root / "clean"
        clean.mkdir()
        self.assertEqual(research_keywords_csv(clean).name, "research_keywords.csv")
        (clean / "datadive_keywords.csv").write_text("kw,sv,rel,rank\n", encoding="utf-8")
        self.assertEqual(research_keywords_csv(clean).name, "datadive_keywords.csv")
        (clean / "research_keywords.csv").write_text("kw,sv,rel,rank\n", encoding="utf-8")
        self.assertEqual(research_keywords_csv(clean).name, "research_keywords.csv")


class ResearchOutputLabelsTest(unittest.TestCase):
    """Workbook tabs, the narrative heading and the Sources line name the provider."""

    def _build(self, root, legacy):
        from build_audit_workbook import build as build_workbook
        from narrative_scaffold import build as build_narrative
        from test_window_alignment import fixture_metrics

        cfg = {"client": "Fixture", "marketplaces": ["US"], "brand_tokens": ["fixture"],
               "competitor_tokens": ["rival"], "asin_groups": {"Main": ["B0TEST0001"]},
               "narrative": {"include_levers": False}, "inputs": {}}
        path = root / "research.json"
        if legacy:
            payload = {k: v for k, v in RESEARCH.items() if k != "provider"}
            path.write_text(json.dumps(payload))
            cfg["datadive_niche"] = "niche-123"
            cfg["inputs"] = {"datadive_niche_json": str(path), "datadive_competitors_json": str(path)}
        else:
            path.write_text(json.dumps(RESEARCH))
            cfg["inputs"] = {"research_json": str(path)}
        (root / "config.json").write_text(json.dumps(cfg))
        (root / "metrics.json").write_text(json.dumps(fixture_metrics("matched")))
        (root / "clean").mkdir()
        from openpyxl import load_workbook
        with redirect_stdout(io.StringIO()):
            wb = load_workbook(build_workbook(root / "config.json", root))
            md = build_narrative(root / "config.json", root, force=True).read_text()
        return wb, md

    def test_soldscope_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            wb, md = self._build(Path(tmp), legacy=False)
        self.assertIn("SoldScope Competitors", wb.sheetnames)
        self.assertNotIn("DataDive Niche", wb.sheetnames)
        note = wb["SoldScope Competitors"].cell(4, 1).value
        self.assertIn("Median of the 3 compared ASINs", note)
        self.assertIn("search_id 90001", note)
        self.assertIn("## SoldScope: category difficulty", md)
        self.assertIn("Across the 3 compared ASINs", md)
        self.assertIn("SoldScope keyword research (search_id 90001; US; "
                      "ASINs B0TEST0001, B0TEST0002, B0TEST0003; 2026-10-01..2026-10-31)", md)
        self.assertNotIn("DataDive", md)

    def test_legacy_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            wb, md = self._build(Path(tmp), legacy=True)
        self.assertIn("DataDive Niche", wb.sheetnames)
        self.assertIn("## DataDive: category difficulty", md)
        self.assertIn("- DataDive niche niche-123.", md)


if __name__ == "__main__":
    unittest.main()
