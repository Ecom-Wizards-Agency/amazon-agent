from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import strip_dead_paths as sdp  # noqa: E402

LIVE = "MAG SOPs/catalog/live-page.md"
DEAD = "MAG SOPs/catalog/dropped-page.md"
HELP = "Amazon Seller Help/articles/001-live-help.md"

UNIT = f"""---
id: KC-0001
title: "Example unit"
status: draft
related_sops: ["{LIVE}", "{DEAD}"]
---

## Sources

- First-party: `{HELP}` (read 01.10.2026).
- Also in: `{DEAD}`
- Also in: `{LIVE}` and `{DEAD}`
"""


class StripDeadPathsCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for rel in (LIVE, HELP):
            (self.root / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.root / rel).write_text("x", encoding="utf-8")
        unit_dir = self.root / "knowledge" / "catalog"
        unit_dir.mkdir(parents=True)
        self.unit = unit_dir / "KC-0001_example.md"
        self.unit.write_text(UNIT, encoding="utf-8")
        self.store = self.root / "cards"
        self.store.mkdir()
        self.card = self.store / "CARD-0001.json"
        self.card.write_text(json.dumps({
            "card_id": "CARD-0001",
            "coverage_paths": [LIVE, DEAD],
            "related_sop_paths": [DEAD],
            "first_party_source_paths": [HELP],
            "contradicts_paths": [],
            "verifier_notes": "",
        }), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_dry_run_changes_nothing_but_reports(self) -> None:
        result = sdp.run(self.root, "2026-10-08", dry_run=True, store=self.store)
        self.assertEqual(result["units_changed"], 1)
        self.assertEqual(result["cards_changed"], 1)
        self.assertEqual(result["card_paths_removed"], 2)
        self.assertEqual(self.unit.read_text(encoding="utf-8"), UNIT)
        self.assertIn(DEAD, json.loads(self.card.read_text(encoding="utf-8"))["coverage_paths"])

    def test_live_run_strips_and_notes(self) -> None:
        result = sdp.run(self.root, "2026-10-08", dry_run=False, store=self.store)
        self.assertEqual(result["unit_paths_removed"], 3)
        text = self.unit.read_text(encoding="utf-8")
        mapping, body, error = sdp.kb_frontmatter.parse_frontmatter(text)
        self.assertIsNone(error)
        self.assertEqual(mapping["related_sops"], [LIVE])
        self.assertNotIn(f"- Also in: `{DEAD}`\n", body)
        self.assertIn(f"- Also in: `{LIVE}` and a MAG SOP dropped on 08.10.2026", body)
        self.assertIn(f"`{HELP}`", body)
        card = json.loads(self.card.read_text(encoding="utf-8"))
        self.assertEqual(card["coverage_paths"], [LIVE])
        self.assertEqual(card["related_sop_paths"], [])
        self.assertEqual(card["first_party_source_paths"], [HELP])
        self.assertIn("dropped-page.md", card["verifier_notes"])
        self.assertFalse(result["index_rebuilt"])

    def test_nothing_to_strip_is_a_no_op(self) -> None:
        sdp.run(self.root, "2026-10-08", dry_run=False, store=self.store)
        before = self.unit.read_text(encoding="utf-8")
        result = sdp.run(self.root, "2026-10-09", dry_run=False, store=self.store)
        self.assertEqual(result["units_changed"], 0)
        self.assertEqual(result["cards_changed"], 0)
        self.assertEqual(self.unit.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
