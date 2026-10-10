from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import ask  # noqa: E402

UNIT = """---
id: KC-0001
title: "Labeling required defect on an inbound shipment: dispute it with the receiving events"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics]
symptom_keywords: ["labeling required defect", "inbound performance defect"]
error_text: []
verification: unverified
---

## Answer

Dispute the labeling required defect from the shipment's Problems tab.
"""


class AskLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        files = {
            "knowledge/logistics/KC-0001_labeling.md": UNIT,
            "skills/amazon-logistics/SKILL.md": "# Amazon Logistics\n\nBrowser: CDP\n\nDispute a labeling required defect from the shipment Problems tab before the window closes.\n",
            "skills/amazon-logistics/references/defects.md": "# Inbound defects\n\nLabeling required defect: open Problems, choose Resolve, then Submit dispute.\n",
            "skills/amazon-logistics/agents/openai.yaml": "labeling required defect dispute\n",
            "Amazon Seller Help/articles/001-inbound-defects.md": "# Inbound performance\n\nA labeling required defect appears when a unit arrives without a scannable label; disputes are reviewed.\n",
            "sop-drafts/2026-05-25_defects.md": "# Draft\n\nLabeling required defect handling notes.\n",
            "MAG SOPs/catalog/catalog-sop-labeling-required-defect.md": "# Catalog SOP: Labeling required defect\n\nLabeling required defect dispute steps: Problems, Resolve, Submit dispute, labeling required defect reason.\n",
            "MAG SOPs/_index/sop-index.json": json.dumps({"captured": [{"file": "catalog/catalog-sop-labeling-required-defect.md", "status": "needs-update", "captured_at": "2026-05-12", "revised_at": "2026-09-15"}]}),
        }
        for rel, text in files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_layers_follow_authority_order_whatever_the_scores(self) -> None:
        result = ask.answer("labeling required defect dispute", self.root)
        layers = result["layers"]
        self.assertEqual(layers["units"][0]["id"], "KC-0001")
        self.assertTrue(all(h["library"] == "Skills" for h in layers["skills"]))
        self.assertEqual({Path(h["path"]).name for h in layers["skills"]}, {"SKILL.md", "defects.md"})
        self.assertEqual(layers["first-party"][0]["library"], "Amazon Seller Help")
        self.assertEqual(layers["drafts"][0]["library"], "SOP Drafts")
        mag = layers["mag"][0]
        self.assertTrue(mag["external"])
        self.assertEqual(mag["sop_status"], "needs-update")
        self.assertTrue(mag["changed_since_capture"])
        self.assertTrue(result["guidance"][0].startswith("Answer from KC-0001 (draft, unverified)"))
        self.assertTrue(result["guidance"][-1].startswith("External fallback only:"))
        self.assertIn("changed on the site since our capture", result["guidance"][-1])
        text = ask.render("labeling required defect dispute", layers)
        self.assertLess(text.index("## Knowledge units"), text.index("## Our skills"))
        self.assertLess(text.index("## Our skills"), text.index("## MAG SOPs (external)"))

    def test_readme_retired_and_index_files_never_enter_the_layers(self) -> None:
        for rel, text in {
            "knowledge/README.md": "# Knowledge\n\nlabeling required defect dispute listed here\n",
            "knowledge/_retired/KC-0002_old.md": UNIT.replace("KC-0001", "KC-0002").replace("status: draft", "status: retired"),
            "MAG SOPs/_index/category-notes.txt": "labeling required defect dispute\n",
        }.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        layers = ask.answer("labeling required defect dispute", self.root)["layers"]
        self.assertEqual([h["id"] for h in layers["units"]], ["KC-0001"])
        self.assertFalse(any("_index" in h["path"] for hits in layers.values() for h in hits))

    def test_nothing_matching_says_so(self) -> None:
        result = ask.answer("zzqxwv", self.root)
        self.assertIn("Nothing in the libraries matches", result["guidance"][0])

    def test_no_unit_gives_the_add_a_unit_hint(self) -> None:
        (self.root / "knowledge/logistics/KC-0001_labeling.md").unlink()
        result = ask.answer("labeling required defect dispute", self.root)
        self.assertEqual(result["layers"]["units"], [])
        self.assertIn("No knowledge unit matches yet", result["guidance"][0])

    def test_empty_question_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            ask.answer("???", self.root)


if __name__ == "__main__":
    unittest.main()
