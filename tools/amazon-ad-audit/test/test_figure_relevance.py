import sys
import tempfile
import unittest
import re
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from build_figures import (  # noqa: E402
    _clear_standard_figures,
    _material_branded_leak_query,
)


class FigureRelevanceTest(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "brand_tokens": ["rovina"],
            "_brand_re": re.compile("rovina", re.I),
            "_competitor_re": None,
        }
        self.asins = {"B0CLIENT"}

    def _query(self, client_rank, competitor_rank, volume=22000):
        return {
            "keyword": "rovina",
            "searchVolume": volume,
            "asinRanks": {
                "B0CLIENT": client_rank,
                "B0RIVAL": competitor_rank,
            },
        }

    def test_rank_one_client_suppresses_brand_graph(self):
        self.assertIsNone(
            _material_branded_leak_query(
                self.cfg, [self._query(client_rank=1, competitor_rank=2)], self.asins
            )
        )

    def test_competitor_outranking_client_produces_brand_graph(self):
        query = self._query(client_rank=4, competitor_rank=1)
        self.assertIs(
            query,
            _material_branded_leak_query(self.cfg, [query], self.asins),
        )

    def test_stale_generated_charts_are_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp)
            stale = outdir / "fig_brand_name_leak.png"
            unrelated = outdir / "operator_screenshot.png"
            stale.write_bytes(b"stale")
            unrelated.write_bytes(b"preserve")

            removed = _clear_standard_figures(outdir)

            self.assertEqual([stale], removed)
            self.assertFalse(stale.exists())
            self.assertTrue(unrelated.exists())


if __name__ == "__main__":
    unittest.main()
