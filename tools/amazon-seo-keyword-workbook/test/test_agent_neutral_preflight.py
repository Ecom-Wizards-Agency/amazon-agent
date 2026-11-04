import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from build_keyword_workbook import (  # noqa: E402
    BROWSER_INPUT_KEYS,
    MCP_INPUT_KEYS,
    SETUP_INPUT_KEYS,
    _seo_identity_status,
    _seo_semantic_evidence_status,
    run_preflight,
)


AGENT_NAMES = ("Claude", "Codex", "ChatGPT")


class AgentNeutralKeywordPreflightTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, mcp_present: bool, browser_present: bool, setup_present: bool = True,
             legacy: bool = False) -> str:
        anchor = {
            "client": "Example",
            "product": "Example Product",
            "marketplace": "US",
            "asin": "B0TEST0001",
        }
        if legacy:
            anchor["datadive_niche"] = "niche-123"
        else:
            anchor["research"] = {
                "asins": ["B0TEST0001", "B0TEST0002"],
                "marketplace": "US",
                "search_id": 12345,
                "date_from": "2026-10-01",
                "date_to": "2026-10-30",
            }
        cfg = {"product_anchor": anchor}
        args = {
            "config": str(self.root / "config.json"),
            "handoff_note": "",
            "out": str(self.root / "workbook.xlsx"),
        }
        presence = {}
        presence.update({key: mcp_present for key in MCP_INPUT_KEYS})
        presence.update({key: browser_present for key in BROWSER_INPUT_KEYS})
        presence.update({key: setup_present for key in SETUP_INPUT_KEYS})
        for key, present in presence.items():
            path = self.root / f"{key}.input"
            if present:
                path.write_text("x", encoding="utf-8")
            args[key] = str(path)

        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(run_preflight(cfg, args), 0)
        rendered = out.getvalue()
        for name in AGENT_NAMES:
            self.assertNotIn(name, rendered)
        return rendered

    def test_expanded_pool_is_an_mcp_input(self):
        self.assertIn("expanded_mkl_csv", MCP_INPUT_KEYS)
        self.assertNotIn("expanded_mkl_csv", BROWSER_INPUT_KEYS)

    def test_mcp_only_missing(self):
        rendered = self._run(mcp_present=False, browser_present=True)
        self.assertIn("STATUS: MISSING SOLDSCOPE MCP INPUTS", rendered)
        self.assertNotIn("MISSING BROWSER INPUTS", rendered)
        for step in ("keyword_research_search_multi_asin", "keyword_research_get_search_progress",
                     "keyword_research_get_multi_results", "tools/soldscope/keywords.py",
                     "tools/soldscope/README.md", "--search-id 12345", "--asins B0TEST0001,B0TEST0002"):
            self.assertIn(step, rendered)
        self.assertIn("<run dir>/expanded.csv", rendered)
        self.assertNotIn("DataDive", rendered)
        self.assertNotIn("datadive_mcp_to_csv", rendered)

    def test_browser_only_missing(self):
        rendered = self._run(mcp_present=True, browser_present=False)
        self.assertIn("MISSING BROWSER INPUTS", rendered)
        self.assertNotIn("MISSING SOLDSCOPE MCP INPUTS", rendered)
        self.assertNotIn("DataDive", rendered)

    def test_both_capabilities_missing(self):
        rendered = self._run(mcp_present=False, browser_present=False)
        self.assertIn("MISSING SOLDSCOPE MCP INPUTS", rendered)
        self.assertIn("MISSING BROWSER INPUTS", rendered)

    def test_ready_continues_current_run(self):
        rendered = self._run(mcp_present=True, browser_present=True)
        self.assertIn("continue the current run", rendered)

    def test_legacy_datadive_config_still_reaches_ready(self):
        rendered = self._run(mcp_present=True, browser_present=True, legacy=True)
        self.assertIn("research=DataDive niche niche-123", rendered)
        self.assertIn("STATUS: READY", rendered)

    def test_legacy_datadive_config_missing_inputs_gets_soldscope_steps(self):
        rendered = self._run(mcp_present=False, browser_present=True, legacy=True)
        self.assertIn("STATUS: MISSING SOLDSCOPE MCP INPUTS", rendered)
        self.assertNotIn("get_niche_", rendered)
        # A legacy config rebuilt from SoldScope data must switch its labels too.
        self.assertIn('keyword_source: "SoldScope"', rendered)


class SeoEvidenceGateTest(unittest.TestCase):
    def test_identity_requires_brand_and_product_in_title_and_description(self):
        cfg = {"seo_identity": {"brand": "Acme", "product_name": "Example PEA"}}
        good = _seo_identity_status(cfg, {
            "title (≤75 char)": "Acme Example PEA Supplement – 60 Capsules",
            "description": "Acme Example PEA combines two labeled ingredients.",
        })
        self.assertTrue(good["title_brand"] and good["title_product"])
        self.assertTrue(good["description_brand"] and good["description_product"])

        generic = _seo_identity_status(cfg, {
            "title (≤75 char)": "Supplement Blend with PEA – 60 Capsules",
            "description": "A two-ingredient capsule supplement.",
        })
        self.assertFalse(generic["title_brand"] or generic["title_product"])
        self.assertFalse(generic["description_brand"] or generic["description_product"])

    def test_semantic_evidence_requires_search_and_shopper_signal(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "seo.json"
            path.write_text(
                '{"rows":[{"section":"Semantic / Alexa AI Direction","poe_evidence":['
                '{"source":"POE Search Terms","signal":"pea supplement"},'
                '{"source":"POE Reviews","signal":"dosage questions"}]}]}',
                encoding="utf-8",
            )
            status = _seo_semantic_evidence_status(str(path))
            self.assertEqual(status["count"], 2)
            self.assertTrue(status["has_search"])
            self.assertTrue(status["has_shopper"])


if __name__ == "__main__":
    unittest.main()
