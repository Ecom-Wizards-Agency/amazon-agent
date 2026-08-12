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
    run_preflight,
)


AGENT_NAMES = ("Claude", "Codex", "ChatGPT")


class AgentNeutralKeywordPreflightTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, mcp_present: bool, browser_present: bool, setup_present: bool = True) -> str:
        cfg = {
            "product_anchor": {
                "client": "Example",
                "product": "Example Product",
                "marketplace": "US",
                "datadive_niche": "niche-123",
                "asin": "B000000000",
            }
        }
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

    def test_mcp_only_missing(self):
        rendered = self._run(mcp_present=False, browser_present=True)
        self.assertIn("MISSING DATADIVE MCP INPUTS", rendered)
        self.assertNotIn("MISSING BROWSER INPUTS", rendered)

    def test_browser_only_missing(self):
        rendered = self._run(mcp_present=True, browser_present=False)
        self.assertIn("MISSING BROWSER INPUTS", rendered)
        self.assertNotIn("MISSING DATADIVE MCP INPUTS", rendered)

    def test_both_capabilities_missing(self):
        rendered = self._run(mcp_present=False, browser_present=False)
        self.assertIn("MISSING DATADIVE MCP INPUTS", rendered)
        self.assertIn("MISSING BROWSER INPUTS", rendered)

    def test_ready_continues_current_run(self):
        rendered = self._run(mcp_present=True, browser_present=True)
        self.assertIn("continue the current run", rendered)


if __name__ == "__main__":
    unittest.main()
