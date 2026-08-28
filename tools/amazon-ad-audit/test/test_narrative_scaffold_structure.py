import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from narrative_scaffold import build  # noqa: E402


class NarrativeScaffoldStructureTest(unittest.TestCase):
    def _render(self, mode=None):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        cfg = {
            "brand_tokens": ["fixture"],
            "competitor_tokens": ["rival"],
            "inputs": {},
            "narrative": {"include_levers": True},
        }
        if mode:
            cfg["narrative"]["mode"] = mode
        config_path = root / "config.json"
        config_path.write_text(json.dumps(cfg))
        metrics = {
            "client": "Fixture",
            "currency": "USD",
            "marketplaces": ["US"],
            "breakeven": 0.5,
            "channels_present": ["SP"],
            "windows": {"ads": "2026-01-01..2026-01-28", "business_report": "same", "sqp_weeks": []},
            "totals": {
                "spend": 100.0,
                "sales": 250.0,
                "br_total_sales": 500.0,
                "acos": 0.4,
                "tacos": 0.2,
                "ad_dependency": 0.5,
            },
            "searchterm_bucket": {
                "Branded": {"spend": 40.0, "sales": 120.0, "acos": 1 / 3, "cvr": 0.2},
                "Generic": {"spend": 60.0, "sales": 130.0, "acos": 60 / 130, "cvr": 0.1},
            },
            "placement": {
                "Top of Search": {"spend": 60.0, "sales": 200.0, "acos": 0.3},
                "Product Pages": {"spend": 40.0, "sales": 50.0, "acos": 0.8},
            },
            "business_report": {
                "rows": [{
                    "asin": "B0FIXTURE0",
                    "group": "Core",
                    "sessions": 100,
                    "units": 20,
                    "sales": 500.0,
                    "buybox": 0.95,
                }]
            },
        }
        (root / "metrics.json").write_text(json.dumps(metrics))
        (root / "internal").mkdir()
        (root / "internal" / "claim_matrix.json").write_text(json.dumps({
            "claims": [{
                "claim": "A call claim",
                "verdict": "Confirmed",
                "client_surface": True,
                "evidence": [{"reason": "Fixture evidence."}],
            }]
        }))
        output = build(config_path, root, force=True)
        rendered = output.read_text()
        tmp.cleanup()
        return rendered

    def test_standard_and_evidence_hybrid_have_one_combined_section(self):
        for mode in (None, "evidence_hybrid"):
            rendered = self._render(mode)
            self.assertEqual(1, rendered.count("## Problems and Solutions"))
            self.assertNotIn("## Good and Bad", rendered)
            self.assertNotIn("## Growth Levers", rendered)
            self.assertNotIn("## What I’d fix next", rendered)
            self.assertNotIn("## What changed after checking the call", rendered)


if __name__ == "__main__":
    unittest.main()
