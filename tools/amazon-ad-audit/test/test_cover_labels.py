import sys
import unittest
from pathlib import Path


TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

import render_branded  # noqa: E402


BLOCKS = [("h2", "Wo ihr organisch steht"), ("h2", "Quellen und Methodik")]


class CoverLabelsTest(unittest.TestCase):
    def test_defaults_keep_english_cover(self):
        kw = render_branded._cover_kwargs({"client": "Fixture", "marketplaces": ["US"]}, {}, BLOCKS, Path("."))
        self.assertIsNone(kw["labels"])
        self.assertTrue(kw["prepared_by"].startswith("By "))
        self.assertTrue(kw["footer_left"].startswith("Confidential"))

    def test_branding_overrides_localise_cover(self):
        cfg = {"client": "Fixture", "marketplaces": ["DE"], "branding": {
            "cover_labels": {"prepared_for": "ERSTELLT FÜR", "inside": "INHALT"},
            "cover_prepared_by_line": "Von Ecom Wizards",
            "cover_footer_left": "Vertraulich · ecomwizards.agency"}}
        kw = render_branded._cover_kwargs(cfg, {}, BLOCKS, Path("."))
        self.assertEqual({"prepared_for": "ERSTELLT FÜR", "inside": "INHALT"}, kw["labels"])
        self.assertEqual("Von Ecom Wizards", kw["prepared_by"])
        self.assertEqual("Vertraulich · ecomwizards.agency", kw["footer_left"])

    def test_german_sources_section_stays_off_cover(self):
        kw = render_branded._cover_kwargs({"client": "Fixture", "marketplaces": ["DE"]}, {}, BLOCKS, Path("."))
        self.assertEqual([("01", "Wo ihr organisch steht")], kw["inside"])


if __name__ == "__main__":
    unittest.main()
