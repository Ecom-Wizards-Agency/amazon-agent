import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from build_keyword_workbook import run_validations  # noqa: E402

CHECK = "Item Highlights add incremental SV over the other searchable fields"
MASTER = "3.1 MKL DataDive 30%"


class ItemHighlightsIncrementTest(unittest.TestCase):
    """The incremental-SV gate reads the other fields' whole cell, not only the
    first publishable line, so a term already present anywhere in a title,
    bullet, description or backend cell counts as covered."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _check(self, bullet_cell: str) -> dict:
        wb = Workbook()
        master = wb.active
        master.title = MASTER
        master.append(["#", "Search Terms", "SV"])
        master.append([1, "example widget", 5000])
        master.append([2, "travel case", 900])
        seo = wb.create_sheet("4.1 SEO Text")
        seo.append(["Section", "Current", "New Listing"])
        seo.append(["Title (≤75 chars)", "", "Example Brand Widget – Compact Example Widget"])
        seo.append(["Item Highlights", "", "Travel Case · Soft Grip"])
        seo.append(["Bullet 1", "", bullet_cell])
        seo.append(["Description", "", "Example Brand widget for daily use."])
        cfg = {
            "product_anchor": {"asin": "B000000001", "client": "Example Brand"},
            "tabs": {"exact_paste": {MASTER: "master_csv"}, "rebuild": []},
            "related_niche_filter": {"exclude_examples": [], "keep": []},
            "triage": {"brand_tokens": [], "form_tokens": [], "negative_tokens": []},
        }
        counts = {
            "_master_header": ["Search Terms", "SV", "B000000001"],
            "1. Root Keywords": 0, "_roots_csv": 0,
            MASTER: 2, "_master_csv": 2,
            "POE Raw - Products": 0, "_poe_products_csv": 0,
            "POE Raw - Search Terms": 0, "_poe_search_terms_csv": 0,
        }
        paths = {"master_csv": str(self.root / "core.csv"),
                 "expanded_mkl_csv": str(self.root / "expanded.csv"),
                 "seo_content": str(self.root / "seo.json")}
        checks = run_validations(wb, cfg, counts, {"kept": [], "dropped": []}, paths, [])
        return next(c for c in checks if c["check"] == CHECK)

    def test_term_only_in_bullet_rationale_counts_as_covered(self):
        check = self._check(
            "Soft Grip: Shaped to sit comfortably in the hand.\n"
            "Rationale: carries travel case for the zip pocket use case."
        )
        self.assertFalse(check["pass"], check["detail"])
        self.assertIn("incremental=0 ", check["detail"])

    def test_term_absent_from_other_fields_is_incremental(self):
        check = self._check("Soft Grip: Shaped to sit comfortably in the hand.")
        self.assertTrue(check["pass"], check["detail"])
        self.assertIn("incremental=900 ", check["detail"])


if __name__ == "__main__":
    unittest.main()
