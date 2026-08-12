import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

import branding  # noqa: E402
from build_audit import preflight  # noqa: E402


AGENT_NAMES = ("Claude", "Codex", "ChatGPT")


class AgentNeutralAuditPreflightTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _path(self, name: str, present: bool) -> str:
        path = self.root / name
        if present:
            path.write_text("x", encoding="utf-8")
        return str(path)

    def _run(self, browser_present: bool, mcp_present: bool, mismatched_windows: bool = False):
        cfg = {
            "client": "Example",
            "marketplaces": ["US"],
            "amazon_account": "Example Seller",
            "datadive_niche": "niche-123",
            "windows": {
                "ads": "2026-07-01..2026-07-31",
                "business_report": ("2026-06-01..2026-06-30" if mismatched_windows
                                    else "2026-07-01..2026-07-31"),
                "sqp_weeks": ["2026-07-04"],
            },
            "inputs": {
                "ads_bulk_xlsx": self._path("ads.xlsx", browser_present),
                "business_report_csv": self._path("business.csv", browser_present),
                "sqp_csvs": {"Main": self._path("sqp.csv", browser_present)},
                "search_catalog_performance_csv": self._path("scp.csv", browser_present),
                "datadive_niche_json": self._path("niche.json", mcp_present),
                "datadive_competitors_json": self._path("competitors.json", mcp_present),
            },
        }
        out = io.StringIO()
        with redirect_stdout(out):
            code = preflight(cfg, "config.example-us.json")
        rendered = out.getvalue()
        for name in AGENT_NAMES:
            self.assertNotIn(name, rendered)
        return code, rendered

    def test_browser_only_missing(self):
        code, rendered = self._run(browser_present=False, mcp_present=True)
        self.assertEqual(code, 1)
        self.assertIn("MISSING BROWSER INPUTS", rendered)
        self.assertNotIn("MISSING DATADIVE MCP INPUTS", rendered)

    def test_mcp_only_missing(self):
        code, rendered = self._run(browser_present=True, mcp_present=False)
        self.assertEqual(code, 1)
        self.assertIn("MISSING DATADIVE MCP INPUTS", rendered)
        self.assertNotIn("MISSING BROWSER INPUTS", rendered)

    def test_both_capabilities_missing(self):
        code, rendered = self._run(browser_present=False, mcp_present=False)
        self.assertEqual(code, 1)
        self.assertIn("MISSING BROWSER INPUTS", rendered)
        self.assertIn("MISSING DATADIVE MCP INPUTS", rendered)

    def test_ready_continues_current_run(self):
        code, rendered = self._run(browser_present=True, mcp_present=True)
        self.assertEqual(code, 0)
        self.assertIn("Continue the current run", rendered)

    def test_mismatched_windows_warn_without_blocking_ready(self):
        code, rendered = self._run(
            browser_present=True,
            mcp_present=True,
            mismatched_windows=True,
        )
        self.assertEqual(code, 0)
        self.assertIn("WARNING: Ads and Business Report source windows are mismatched", rendered)
        self.assertIn("Blended KPIs will render as N/A", rendered)


class AgentNeutralBrandingTest(unittest.TestCase):
    def test_runtime_environment_does_not_change_fallback(self):
        results = []
        environments = (
            {"CLAUDECODE": "1"},
            {"CODEX_THREAD_ID": "test"},
            {"CHATGPT_RUNTIME": "1"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing-branding.json"
            for environment in environments:
                branding._CACHE.clear()
                with patch.dict(os.environ, environment, clear=True):
                    loaded = branding.load_branding({"branding": {"branding_json": str(missing)}})
                self.assertEqual(loaded["_source"], "branding.EXAMPLE-neutral.json")
                results.append({k: v for k, v in loaded.items() if k != "_source"})
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_legacy_examples_match_neutral_values(self):
        def values(path: Path):
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.pop("_comment", None)
            return payload

        neutral = values(TOOL_DIR / "branding.EXAMPLE-neutral.json")
        self.assertEqual(neutral, values(TOOL_DIR / "branding.EXAMPLE-claude.json"))
        self.assertEqual(neutral, values(TOOL_DIR / "branding.EXAMPLE-codex.json"))


if __name__ == "__main__":
    unittest.main()
