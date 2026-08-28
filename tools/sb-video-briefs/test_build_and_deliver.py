import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_and_deliver.py")
SPEC = importlib.util.spec_from_file_location("build_and_deliver", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildAndDeliverTests(unittest.TestCase):
    def valid_config(self):
        return {
            "client": {"name": "Acme", "product_line": "Widget", "marketplace": "US"},
            "seller_central": {
                "account_name": "Acme United States",
                "expected_partner_account_id": "PARTNER",
                "marketplace_label": "United States",
            },
            "delivery": {
                "drive_folder_id": "folder-id",
                "brief_title": "Acme US - Widget SB Video Briefing",
                "reference_title": "Acme US - Widget - Creative Reference & Asset Library",
            },
        }

    def test_config_accepts_new_account_shape(self):
        MODULE.validate_config(self.valid_config())

    def test_legacy_keys_warn(self):
        cfg = self.valid_config()
        cfg["client"]["amazon_account"] = "old"
        cfg["economics"] = {"break_even_acos": 0.5}
        cfg["testing"] = {}
        self.assertEqual(len(MODULE.legacy_warnings(cfg)), 3)

    def test_brief_rejects_claims_appendix(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text("## Claims and compliance (advisory)\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "forbidden"):
                MODULE.validate_markdown(path, "brief")

    def test_reference_requires_asset_section_five(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "reference.md"
            path.write_text("# Reference\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "section 5"):
                MODULE.validate_markdown(path, "reference")

    def test_existing_document_bounds_leave_final_newline(self):
        structure = {
            "successful": True,
            "data": {
                "tabs": [{
                    "tabProperties": {"tabId": "t.0"},
                    "documentTab": {"body": {"content": [{"endIndex": 1}, {"endIndex": 42}]}},
                }]
            },
        }
        self.assertEqual(MODULE.first_tab_bounds(structure), ("t.0", 41))

    def test_markdown_body_drops_h1(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text("# Canonical title\n\nFirst line.\n", encoding="utf-8")
            self.assertEqual(MODULE.markdown_body(path), "First line.\n")

    def test_document_id_from_url(self):
        url = "https://docs.google.com/document/d/abc_DEF-123/edit"
        self.assertEqual(MODULE.document_id_from_url(url), "abc_DEF-123")


if __name__ == "__main__":
    unittest.main()
