from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import build_knowledge_index as bki  # noqa: E402
import kb_frontmatter as kb  # noqa: E402

BODY = "\n".join(f"\n## {name}\n\nText." for name in kb.SECTION_ORDER) + "\n"


def unit_mapping(unit_id: str, topic: str, title: str, status: str = "draft", **extra: object) -> dict:
    mapping = {
        "id": unit_id,
        "title": title,
        "kind": "diagnosis",
        "topic": topic,
        "status": status,
        "skills": ["amazon-catalog"],
        "marketplaces": ["US"],
        "marketplace_inferred": False,
        "surface": "Seller Central > Inventory",
        "surface_verified": False,
        "symptom_keywords": ["listing suppressed"],
        "error_text": [],
        "resolution_status": "unknown",
        "fix_source": "unknown",
        "evidence_location": "none",
        "confidence": "low",
        "verification": "unverified",
        "verified_on": "",
        "verified_how": "",
        "amazon_sources": [],
        "related_sops": [],
        "supersedes": [],
        "contradicts": [],
        "observed": "2026-10",
        "review_by": "2027-10",
        "provenance": f"ledger:{unit_id}",
    }
    mapping.update(extra)
    return mapping


class LibraryFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        knowledge = self.root / "knowledge"
        for folder in [*kb.TOPICS, "_retired", "_index"]:
            (knowledge / folder).mkdir(parents=True)
            (knowledge / folder / ".gitkeep").write_text("", encoding="utf-8")
        (knowledge / "TEMPLATE.md").write_text("not a unit\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_unit(self, folder: str, name: str, mapping: dict) -> Path:
        path = self.root / "knowledge" / folder / name
        path.write_text(kb.dump_frontmatter(mapping) + BODY, encoding="utf-8")
        return path

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = bki.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def populate(self) -> None:
        self.write_unit("catalog", "KC-0003_variation-rejected.md", unit_mapping("KC-0003", "catalog", "Variation rejected"))
        self.write_unit(
            "logistics",
            "KC-0001_shipment-stuck.md",
            unit_mapping("KC-0001", "logistics", "Shipment stuck [checked-in]", status="reviewed", verification="verified"),
        )
        self.write_unit("catalog", "KC-0002_listing-suppressed.md", unit_mapping("KC-0002", "catalog", "Listing suppressed"))
        # Frontmatter still says draft; the folder makes it retired.
        self.write_unit("_retired", "KC-0004_old-rule.md", unit_mapping("KC-0004", "ads", "Old rule"))


class BuildIndex(LibraryFixture):
    def test_empty_library(self) -> None:
        code, _out, _err = self.run_main("--readme")
        self.assertEqual(code, 0)
        index = json.loads((self.root / "knowledge/_index/knowledge-index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["unit_count"], 0)
        self.assertEqual(index["active_count"], 0)
        self.assertEqual(index["retired_count"], 0)
        self.assertEqual(index["units"], [])
        self.assertEqual(list(index["topics"]), kb.TOPICS)
        self.assertEqual(set(index["topics"].values()), {0})
        readme = (self.root / "knowledge/README.md").read_text(encoding="utf-8")
        self.assertIn("Units: **0**", readme)
        self.assertIn("--library kb --limit 5", readme)
        self.assertIn("docs/knowledge-library.md", readme)
        self.assertNotIn("## Retired", readme)

    def test_sorting_counts_and_fields(self) -> None:
        self.populate()
        index = bki.build_index(self.root)
        self.assertEqual(index["library"], "Amazon Knowledge")
        self.assertEqual(index["generated_by"], "tools/knowledge/build_knowledge_index.py")
        self.assertEqual([u["id"] for u in index["units"]], ["KC-0001", "KC-0002", "KC-0003", "KC-0004"])
        self.assertEqual(index["unit_count"], 4)
        self.assertEqual(index["active_count"], 3)
        self.assertEqual(index["retired_count"], 1)
        self.assertEqual(index["topics"]["catalog"], 2)
        self.assertEqual(index["topics"]["logistics"], 1)
        self.assertEqual(index["topics"]["ads"], 0)
        first = index["units"][0]
        self.assertEqual(first["file"], "knowledge/logistics/KC-0001_shipment-stuck.md")
        self.assertEqual(list(first), [*bki.UNIT_FIELDS, "file"])
        self.assertEqual(first["skills"], ["amazon-catalog"])
        self.assertNotIn("provenance", first)

    def test_retired_folder_overrides_status(self) -> None:
        self.populate()
        index = bki.build_index(self.root)
        retired = [u for u in index["units"] if u["id"] == "KC-0004"][0]
        self.assertEqual(retired["status"], "retired")
        self.assertEqual(retired["topic"], "ads")
        self.assertEqual(retired["file"], "knowledge/_retired/KC-0004_old-rule.md")

    def test_skips_template_readme_gitkeep(self) -> None:
        (self.root / "knowledge/catalog/README.md").write_text("# not a unit\n", encoding="utf-8")
        (self.root / "knowledge/catalog/TEMPLATE.md").write_text("# not a unit\n", encoding="utf-8")
        errors: list[str] = []
        index = bki.build_index(self.root, errors)
        self.assertEqual(errors, [])
        self.assertEqual(index["unit_count"], 0)

    def test_parse_error_skipped_exit_1(self) -> None:
        self.populate()
        bad = self.root / "knowledge/catalog/KC-0009_bad.md"
        bad.write_text("---\nid: KC-0009\ntitle: 'single'\n---\n", encoding="utf-8")
        code, _out, err = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("knowledge/catalog/KC-0009_bad.md", err)
        self.assertIn("single quotes", err)
        index = json.loads((self.root / "knowledge/_index/knowledge-index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["unit_count"], 4)

    def test_idempotent(self) -> None:
        self.populate()
        self.assertEqual(self.run_main("--readme")[0], 0)
        first = [
            (self.root / rel).read_bytes() for rel in (bki.INDEX_REL, bki.README_REL)
        ]
        self.assertEqual(self.run_main("--readme")[0], 0)
        second = [
            (self.root / rel).read_bytes() for rel in (bki.INDEX_REL, bki.README_REL)
        ]
        self.assertEqual(first, second)
        self.assertTrue(first[0].endswith(b"\n"))


class Readme(LibraryFixture):
    def test_readme_line_format(self) -> None:
        self.populate()
        readme = bki.build_readme(bki.build_index(self.root))
        self.assertIn("Units: **4** (3 active, 1 retired)", readme)
        self.assertIn("## catalog (2)", readme)
        self.assertIn("## logistics (1)", readme)
        self.assertNotIn("## ads", readme)
        self.assertIn(
            "- [KC-0002 Listing suppressed](catalog/KC-0002_listing-suppressed.md) · diagnosis · draft · unverified",
            readme,
        )
        self.assertIn(
            "- [KC-0001 Shipment stuck \\[checked-in\\]](logistics/KC-0001_shipment-stuck.md)"
            " · diagnosis · reviewed · verified",
            readme,
        )
        self.assertIn("## Retired (excluded from search)", readme)
        self.assertIn("- [KC-0004 Old rule](_retired/KC-0004_old-rule.md) · diagnosis · retired · unverified", readme)
        # Within a topic, units are listed by id.
        self.assertLess(readme.index("KC-0002 "), readme.index("KC-0003 "))
        # Retired section comes last.
        self.assertGreater(readme.index("## Retired"), readme.index("## logistics"))
        self.assertNotIn(" \u2014 ", readme)


class Check(LibraryFixture):
    def test_check_clean_and_drift(self) -> None:
        self.populate()
        code, _out, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("missing", err)
        self.assertFalse((self.root / bki.INDEX_REL).exists(), "--check must not write")

        self.assertEqual(self.run_main("--readme")[0], 0)
        self.assertEqual(bki.check_drift(self.root), [])
        self.assertEqual(self.run_main("--check")[0], 0)

        self.write_unit("seo", "KC-0005_new.md", unit_mapping("KC-0005", "seo", "New unit"))
        before = [(self.root / rel).read_bytes() for rel in (bki.INDEX_REL, bki.README_REL)]
        drift = bki.check_drift(self.root)
        self.assertEqual(len(drift), 2)
        self.assertTrue(drift[0].startswith("knowledge/_index/knowledge-index.json"))
        self.assertTrue(drift[1].startswith("knowledge/README.md"))
        code, _out, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("out of date", err)
        after = [(self.root / rel).read_bytes() for rel in (bki.INDEX_REL, bki.README_REL)]
        self.assertEqual(before, after, "--check must not write")

    def test_check_detects_hand_edit_of_readme_only(self) -> None:
        self.populate()
        self.run_main("--readme")
        readme = self.root / bki.README_REL
        readme.write_text(readme.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8")
        drift = bki.check_drift(self.root)
        self.assertEqual(len(drift), 1)
        self.assertIn("knowledge/README.md", drift[0])


if __name__ == "__main__":
    unittest.main()
