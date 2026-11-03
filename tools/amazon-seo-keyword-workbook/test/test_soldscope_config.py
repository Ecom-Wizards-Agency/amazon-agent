"""SoldScope config keys, their legacy DataDive fallbacks, and the shipped template."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook, load_workbook

TOOL_DIR = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("builder", TOOL_DIR / "build_keyword_workbook.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

LEGACY_GROUP = {
    "min_relevancy": "30%",
    "visible_keyword_count": "94",
    "visible_search_volume": "94867",
    "export_timestamp": "2026-09-04T04:08:00Z",
    "niche_id": "niche-123",
    "marketplace": "de",
    "hero_keyword": "example keyword",
}
SOLDSCOPE_GROUP = {
    "search_id": 12345,
    "asins": ["B0TEST0001", "B0TEST0002"],
    "marketplace": "US",
    "date_from": "2026-10-01",
    "date_to": "2026-10-30",
    "raw_rows": 120,
    "kept_rows": 40,
    "core_min": 0.3,
    "pool_min": 0.01,
    "relevancy_mode": "native",
}


def groups(item: dict) -> dict:
    return {"core_mkl": dict(item), "expanded_mkl": dict(item)}


class KeywordExportsFallbackTest(unittest.TestCase):
    def test_new_key_is_read(self):
        cfg = {"keyword_exports": groups(SOLDSCOPE_GROUP)}
        self.assertEqual(b.keyword_exports(cfg)["core_mkl"]["search_id"], 12345)

    def test_falls_back_to_legacy_key(self):
        cfg = {"datadive_exports": groups(LEGACY_GROUP)}
        self.assertEqual(b.keyword_exports(cfg)["core_mkl"]["niche_id"], "niche-123")

    def test_new_key_wins_over_legacy_key(self):
        cfg = {"keyword_exports": groups(SOLDSCOPE_GROUP), "datadive_exports": groups(LEGACY_GROUP)}
        self.assertIn("search_id", b.keyword_exports(cfg)["core_mkl"])

    def test_empty_new_key_falls_back(self):
        cfg = {"keyword_exports": {}, "datadive_exports": groups(LEGACY_GROUP)}
        self.assertIn("niche_id", b.keyword_exports(cfg)["core_mkl"])

    def test_neither_key(self):
        self.assertEqual(b.keyword_exports({}), {})


class ExportMetadataGateTest(unittest.TestCase):
    def test_legacy_datadive_set_passes(self):
        self.assertEqual(b.export_metadata_missing({"datadive_exports": groups(LEGACY_GROUP)}), [])

    def test_soldscope_set_passes(self):
        self.assertEqual(b.export_metadata_missing({"keyword_exports": groups(SOLDSCOPE_GROUP)}), [])

    def test_soldscope_placeholder_fails(self):
        meta = groups(SOLDSCOPE_GROUP)
        meta["core_mkl"]["search_id"] = "TO_RECORD_FROM_RESEARCH_JSON"
        meta["expanded_mkl"]["kept_rows"] = "<pool rows>"
        missing = b.export_metadata_missing({"keyword_exports": meta})
        self.assertEqual(missing, ["core_mkl.search_id", "expanded_mkl.kept_rows"])

    def test_empty_or_placeholder_asin_list_fails(self):
        for asins in ([], ["TO_RECORD_FROM_RESEARCH_JSON"], ["B0TEST0001", ""]):
            meta = groups(SOLDSCOPE_GROUP)
            meta["core_mkl"]["asins"] = asins
            self.assertEqual(b.export_metadata_missing({"keyword_exports": meta}), ["core_mkl.asins"], asins)

    def test_legacy_placeholder_still_fails(self):
        meta = groups(LEGACY_GROUP)
        meta["core_mkl"]["visible_keyword_count"] = "TO_RECORD_FROM_DATADIVE_UI"
        self.assertEqual(
            b.export_metadata_missing({"datadive_exports": meta}), ["core_mkl.visible_keyword_count"]
        )

    def test_missing_group_fails(self):
        missing = b.export_metadata_missing({"keyword_exports": {"core_mkl": dict(SOLDSCOPE_GROUP)}})
        self.assertTrue(missing)
        self.assertTrue(all(m.startswith("expanded_mkl.") for m in missing))

    def test_zero_counts_are_recorded_values(self):
        meta = groups(SOLDSCOPE_GROUP)
        meta["expanded_mkl"]["kept_rows"] = 0
        self.assertEqual(b.export_metadata_missing({"keyword_exports": meta}), [])

    def test_shipped_template_fails_until_filled(self):
        cfg = json.loads((TOOL_DIR / "config.TEMPLATE.json").read_text(encoding="utf-8"))
        missing = b.export_metadata_missing(cfg)
        self.assertIn("core_mkl.search_id", missing)
        self.assertIn("expanded_mkl.raw_rows", missing)


class ResearchIdentityTest(unittest.TestCase):
    def test_research_block(self):
        cfg = {"keyword_source": "SoldScope", "product_anchor": {"research": {
            "asins": ["B0TEST0001", "B0TEST0002"], "marketplace": "US", "search_id": 12345,
            "date_from": "2026-10-01", "date_to": "2026-10-30"}}}
        text = b.research_identity(cfg)
        self.assertEqual(text, "SoldScope search 12345 (US, ASINs B0TEST0001,B0TEST0002 2026-10-01..2026-10-30)")

    def test_falls_back_to_datadive_niche(self):
        cfg = {"product_anchor": {"datadive_niche": "niche-123"}}
        self.assertEqual(b.research_identity(cfg), "DataDive niche niche-123")


class RankingScoreNoteLabelTest(unittest.TestCase):
    def test_rj_note_uses_neutral_label(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "seo.json"
            path.write_text(json.dumps({"rows": [
                {"section": "Title", "current": "Old title", "new": "New title", "rj": "1234 (+12%)"},
            ]}), encoding="utf-8")
            ws = Workbook().active
            b.build_seo_text(ws, str(path), {}, [])
            notes = ws.cell(2, 4).value
            self.assertEqual(notes, "Keyword ranking score note: 1234 (+12%)")
            cells = [str(v) for row in ws.iter_rows(values_only=True) for v in row if v is not None]
            self.assertFalse(any("Ranking Juice" in v for v in cells))


class TemplateConfigMatchesWorkbookTest(unittest.TestCase):
    """Every tab the shipped config names exists in the template after its renames,
    so a build never creates a stray tab."""

    # Built by the builder from competitors_csv; not a template sheet.
    GENERATED = {"4.2 Competitors"}

    def setUp(self):
        self.cfg = json.loads((TOOL_DIR / "config.TEMPLATE.json").read_text(encoding="utf-8"))
        self.wb = load_workbook(TOOL_DIR / "template_keyword_workbook.xlsx")
        warnings: list[str] = []
        self.applied = b.apply_template_renames(self.wb, self.cfg, warnings)
        self.assertEqual(warnings, [])

    def test_source_is_soldscope(self):
        self.assertEqual(b.keyword_source_label(self.cfg), "SoldScope")
        self.assertEqual(
            self.cfg["tabs"]["template_renames"],
            {"3.1 MKL DataDive 30%": "3.1 MKL SoldScope 30%", "2.1 MKL DataDive 1%": "2.1 MKL SoldScope 1%"},
        )
        self.assertIn("keyword_exports", self.cfg)
        self.assertNotIn("datadive_exports", self.cfg)
        self.assertIn("research", self.cfg["product_anchor"])
        self.assertNotIn("datadive_niche", self.cfg["product_anchor"])

    def test_named_tabs_exist_after_renames(self):
        tabs = self.cfg["tabs"]
        named = {
            "tabs.exact_paste": list(tabs["exact_paste"]),
            "tabs.rebuild": tabs["rebuild"],
            "tabs.carry_forward": tabs["carry_forward"],
            "tab_order": self.cfg["tab_order"],
            "required_current_tabs": self.cfg["required_current_tabs"],
            "stale_data_guard.tabs": self.cfg["stale_data_guard"]["tabs"],
        }
        for key, names in named.items():
            stray = [n for n in names if n not in self.wb.sheetnames and n not in self.GENERATED]
            self.assertEqual(stray, [], key)
        self.assertEqual(tabs["exact_paste"]["3.1 MKL SoldScope 30%"], "master_csv")
        self.assertEqual(tabs["exact_paste"]["2.1 MKL SoldScope 1%"], "expanded_mkl_csv")

    def test_no_stale_rename_references(self):
        self.assertEqual(b.stale_rename_references(self.cfg, self.applied), [])

    def test_tab_order_covers_every_template_sheet(self):
        self.assertEqual(set(self.wb.sheetnames) - set(self.cfg["tab_order"]), set())
        self.assertFalse(any("DataDive" in n for n in self.cfg["tab_order"]))


if __name__ == "__main__":
    unittest.main()
