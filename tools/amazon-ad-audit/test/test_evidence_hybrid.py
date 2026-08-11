import sys
import unittest
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from narrative_scaffold import (  # noqa: E402
    _hybrid_findings,
    _hybrid_levers,
    _hybrid_summary,
    _market_decision,
)


class EvidenceHybridTest(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "comparison_windows": {
                "disruption": "2026-07-12..2026-08-08",
                "online_control": "2026-05-31..2026-06-27",
                "note": "Do not blend the windows.",
            },
            "inputs": {"ads_bulk_source_note": "Two-day directional snapshot only."},
        }
        self.totals = {
            "spend": 1000,
            "sales": 4000,
            "br_total_sales": 10000,
            "br_sessions": 1000,
        }
        self.buckets = {
            "Branded": {"spend": 300},
            "Generic": {"spend": 500},
        }
        self.placements = {
            "Top of Search": {"acos": 0.20},
            "Product Pages": {"acos": 0.80},
        }

    def test_hybrid_copy_has_no_operator_placeholders(self):
        blocks = [
            _hybrid_summary(self.cfg, self.totals, self.buckets, ["SP", "SD"], "USD"),
            str(_hybrid_findings(self.cfg, self.totals, self.buckets, self.placements, [], {})),
            str(_hybrid_levers(self.cfg, self.totals, self.placements, ["SP", "SD"], ["SB"])),
            _market_decision({
                "coverage": {"exact_relevancy_weekly_equivalent": 60000},
                "benchmark": {"median_reviews": 5000},
            }),
        ]
        rendered = "\n".join(blocks)
        self.assertNotIn("<!-- operator:", rendered)
        self.assertNotIn("<!-- short claim -->", rendered)
        self.assertIn("online control", rendered)
        self.assertIn("Restore the retail foundation", rendered)


if __name__ == "__main__":
    unittest.main()
