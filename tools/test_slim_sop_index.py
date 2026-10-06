from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import slim_sop_index as slim  # noqa: E402

LEGACY_README = """# MAG SOP Library

Captured from My Amazon Guy SOP Library on `2026-05-12T07:07:49Z`.

This runtime tree is curated for Amazon work. Categories irrelevant to the
agent were removed: AI ChatGPT prompts, Product Development, parts of
Business Analysis, and the Walmart SOPs (dropped 2026-07-27). The complete
535-file capture with all assets lives in the pCloud visual archive
(see `docs/mag-sops-assets.md`).

Active SOP entries: **2** (plus 1 archived)

## Catalog (2)

- [Alpha](catalog/alpha.md)
- [Beta](catalog/beta.md)

## Archived (excluded from search)

### SEO (1)

- [Gamma](_archive/seo/gamma.md)
"""


def sample_data() -> dict:
    return {
        "captured_at": "2026-05-12T07:07:49Z",
        "captured": [
            {"title": "Beta", "category": "Catalog", "file": "catalog/beta.md"},
            {"title": "Alpha", "category": "Catalog", "file": "catalog/alpha.md"},
            {"title": "Gamma", "category": "SEO", "file": "_archive/seo/gamma.md", "archived": True},
        ],
    }


def build_root(root: Path, entries: list[dict], files: list[str], extra: dict | None = None) -> Path:
    sop_root = root / "MAG SOPs"
    for rel in files:
        path = sop_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# x\n", encoding="utf-8")
    (sop_root / "_index").mkdir(parents=True, exist_ok=True)
    data = {"captured_at": "2026-05-12T07:07:49Z", "captured": entries, **(extra or {})}
    index = sop_root / "_index" / "sop-index.json"
    index.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return index


class KeepFieldsTests(unittest.TestCase):
    def test_new_fields_are_kept(self) -> None:
        for field in (
            "status", "superseded_by", "merge_into", "triaged_on", "flags",
            "knowledge_value", "revised_at", "revision_checked_at",
        ):
            self.assertIn(field, slim.KEEP_FIELDS)
        self.assertEqual(slim.KEEP_FIELDS[:8], [
            "title", "category", "chapter", "url", "captured_at", "file", "body_length", "image_count",
        ])

    def test_slim_entry_keeps_triage_fields_and_drops_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sop_root = Path(tmp)
            (sop_root / "catalog").mkdir()
            (sop_root / "catalog" / "a.md").write_text("x", encoding="utf-8")
            entry = {
                "title": "A", "file": "catalog/a.md", "body": "long", "images": ["x"],
                "status": "superseded", "superseded_by": "docs/x.md", "flags": ["old-nav"],
                "triaged_on": "2026-10-06", "revised_at": "2026-10-01",
            }
            slimmed = slim.slim_entry(entry, sop_root)
            self.assertNotIn("body", slimmed)
            self.assertNotIn("images", slimmed)
            self.assertEqual(slimmed["status"], "superseded")
            self.assertEqual(slimmed["flags"], ["old-nav"])
            self.assertEqual(slimmed["revised_at"], "2026-10-01")


class ReadmeTests(unittest.TestCase):
    def test_legacy_text_is_byte_identical_without_dropped_key(self) -> None:
        self.assertEqual(slim.build_readme(sample_data()), LEGACY_README)

    def test_dropped_list_replaces_the_hard_coded_sentence(self) -> None:
        data = sample_data()
        data["dropped"] = slim.DEFAULT_DROPPED + [{"what": "12 SOPs triaged as unusable", "date": "2026-10-06"}]
        readme = slim.build_readme(data)
        self.assertNotIn("Categories irrelevant", readme)
        flat = " ".join(readme.split())
        self.assertIn(
            "removed: AI ChatGPT prompts, Product Development and parts of Business Analysis"
            " (dropped 2026-07-08), the Walmart SOPs (dropped 2026-07-27), and 12 SOPs triaged"
            " as unusable (dropped 2026-10-06).",
            flat,
        )
        self.assertIn("(see `docs/mag-sops-assets.md`).", flat)
        self.assertTrue(all(len(line) <= slim.WRAP_WIDTH for line in readme.splitlines()[4:9]))

    def test_empty_dropped_list(self) -> None:
        data = sample_data()
        data["dropped"] = []
        readme = slim.build_readme(data)
        self.assertNotIn("removed:", readme)
        self.assertIn("This runtime tree is curated for Amazon work. The complete", readme)

    def test_superseded_and_merged_rendering(self) -> None:
        data = sample_data()
        data["captured"][0].update(status="superseded", superseded_by="skills/x/SKILL.md")
        data["captured"][2].update(status="merged", merge_into="catalog/alpha.md")
        data["captured"].append(
            {"title": "Delta", "category": "SEO", "file": "seo/delta.md", "status": "merged", "merge_into": "catalog/alpha.md"}
        )
        readme = slim.build_readme(data)
        self.assertIn("- [Beta](catalog/beta.md) (superseded by `skills/x/SKILL.md`)", readme)
        self.assertIn("Active SOP entries: **3** (1 superseded) (plus 1 archived)", readme)
        archived_part = readme.split("## Archived (excluded from search)", 1)[1]
        self.assertIn("- [Gamma](_archive/seo/gamma.md) (merged into `catalog/alpha.md`)", archived_part)
        # a merged entry whose file is not archived stays out of the archived section
        self.assertNotIn("Delta", archived_part)


class RunTests(unittest.TestCase):
    def test_run_seeds_dropped_once_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = build_root(
                root,
                [
                    {"title": "A", "category": "Catalog", "file": "catalog/a.md", "body": "x"},
                    {"title": "B", "category": "Catalog", "file": "catalog/b.md"},
                    {"title": "Gone", "category": "Catalog", "file": "catalog/gone.md"},
                    {"title": "Moved", "category": "SEO", "file": "seo/moved.md"},
                ],
                ["catalog/a.md", "catalog/b.md", "_archive/seo/moved.md"],
            )
            first = slim.run(write_readme=True, root=root)
            self.assertTrue(first["dropped_seeded"])
            self.assertEqual((first["before"], first["after"], first["archived"]), (4, 3, 1))
            data = json.loads(index.read_text(encoding="utf-8"))
            self.assertEqual(data["dropped"], slim.DEFAULT_DROPPED)
            self.assertEqual(
                [e["file"] for e in data["captured"]], ["catalog/a.md", "catalog/b.md", "_archive/seo/moved.md"]
            )
            index_bytes = index.read_bytes()
            readme_bytes = (root / "MAG SOPs" / "README.md").read_bytes()
            second = slim.run(write_readme=True, root=root)
            self.assertFalse(second["dropped_seeded"])
            self.assertEqual(index.read_bytes(), index_bytes)
            self.assertEqual((root / "MAG SOPs" / "README.md").read_bytes(), readme_bytes)

    def test_run_rejects_missing_targets_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "real.md").write_text("x", encoding="utf-8")
            index = build_root(
                root,
                [
                    {"title": "A", "category": "Catalog", "file": "catalog/a.md",
                     "status": "superseded", "superseded_by": "docs/real.md"},
                    {"title": "B", "category": "Catalog", "file": "catalog/b.md",
                     "status": "superseded", "superseded_by": "docs/missing.md"},
                    {"title": "C", "category": "Catalog", "file": "catalog/c.md",
                     "status": "merged", "merge_into": "catalog/a.md"},
                    {"title": "D", "category": "Catalog", "file": "catalog/d.md",
                     "status": "merged", "merge_into": "catalog/nowhere.md"},
                ],
                ["catalog/a.md", "catalog/b.md", "catalog/c.md", "catalog/d.md"],
            )
            before = index.read_bytes()
            with self.assertRaises(slim.MissingTargets) as ctx:
                slim.run(write_readme=True, root=root)
            self.assertEqual(
                ctx.exception.missing,
                ["catalog/b.md: superseded_by docs/missing.md", "catalog/d.md: merge_into catalog/nowhere.md"],
            )
            self.assertEqual(index.read_bytes(), before)
            self.assertFalse((root / "MAG SOPs" / "README.md").exists())


if __name__ == "__main__":
    unittest.main()
