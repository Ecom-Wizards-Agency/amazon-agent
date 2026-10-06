from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import build_knowledge_index as bki  # noqa: E402
import kb_frontmatter as kb  # noqa: E402
import lint_knowledge as lk  # noqa: E402

SOURCE = "Amazon Seller Help/articles/001-listing-suppressed.md"
SECTIONS = {name: f"Plain text for {name.lower()}." for name in kb.SECTION_ORDER}


def unit_mapping(unit_id: str = "KC-0001", topic: str = "catalog", **extra: object) -> dict:
    mapping = {
        "id": unit_id,
        "title": "Listing suppressed after a category change",
        "kind": "diagnosis",
        "topic": topic,
        "status": "draft",
        "skills": ["amazon-catalog"],
        "marketplaces": ["US"],
        "marketplace_inferred": False,
        "surface": "Seller Central > Inventory > Manage All Inventory",
        "surface_verified": False,
        "symptom_keywords": ["listing suppressed"],
        "error_text": [],
        "resolution_status": "resolved",
        "fix_source": "agency",
        "evidence_location": "slack",
        "confidence": "medium",
        "verification": "unverified",
        "verified_on": "",
        "verified_how": "",
        "amazon_sources": [SOURCE],
        "related_sops": [],
        "supersedes": [],
        "contradicts": [],
        "observed": "2026-09",
        "review_by": "2027-09",
        "provenance": f"ledger:{unit_id}",
    }
    mapping.update(extra)
    return mapping


def render_body(sections: dict[str, str]) -> str:
    return "".join(f"\n## {name}\n\n{text}\n" for name, text in sections.items())


class LintFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        knowledge = self.root / "knowledge"
        for folder in [*kb.TOPICS, "_retired", "_index"]:
            (knowledge / folder).mkdir(parents=True)
        (self.root / "skills" / "amazon-catalog").mkdir(parents=True)
        source = self.root / SOURCE
        source.parent.mkdir(parents=True)
        source.write_text("# Captured help page\n", encoding="utf-8")
        template = kb.dump_frontmatter(unit_mapping("KC-0000")) + render_body(SECTIONS)
        (knowledge / "TEMPLATE.md").write_text(template, encoding="utf-8")
        self.terms = self.root / "_local" / "knowledge-redaction-terms.txt"
        self.terms.parent.mkdir()
        self.terms.write_text("# test denylist\nNordwind Labs\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_unit(
        self,
        mapping: dict | None = None,
        sections: dict[str, str] | None = None,
        folder: str = "catalog",
        name: str | None = None,
        rebuild: bool = True,
    ) -> Path:
        mapping = mapping or unit_mapping()
        name = name or f"{mapping['id']}_listing-suppressed-after-category-change.md"
        path = self.root / "knowledge" / folder / name
        path.write_text(kb.dump_frontmatter(mapping) + render_body(sections or SECTIONS), encoding="utf-8")
        if rebuild:
            self.rebuild()
        return path

    def rebuild(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            bki.main(["--readme", "--root", str(self.root)])

    def lint(self, strict: bool = True) -> list[str]:
        return lk.lint_knowledge(self.root, strict=strict, terms_path=self.terms)

    def assert_problem(self, needle: str) -> list[str]:
        problems = self.lint()
        self.assertTrue(any(needle in p for p in problems), f"{needle!r} not in {problems}")
        return problems


class ValidUnitTests(LintFixture):
    def test_valid_unit_passes_strict(self) -> None:
        self.write_unit()
        self.assertEqual(self.lint(), [])

    def test_empty_library_passes(self) -> None:
        self.rebuild()
        self.assertEqual(self.lint(), [])

    def test_verified_unit_with_date_passes(self) -> None:
        self.write_unit(unit_mapping(verification="verified", verified_on="2026-10-01", verified_how="live-ui"))
        self.assertEqual(self.lint(), [])

    def test_retired_unit_passes_under_retired(self) -> None:
        self.write_unit(unit_mapping(status="retired"), folder="_retired")
        self.assertEqual(self.lint(), [])

    def test_cli_prints_clean_with_unit_count(self) -> None:
        self.write_unit()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lk.main(["--strict", "--terms", str(self.terms), "--root", str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(buf.getvalue().strip(), "lint_knowledge: clean (1 units)")


class FailureTests(LintFixture):
    def test_wrong_key_order(self) -> None:
        mapping = unit_mapping()
        reordered = {"title": mapping.pop("title"), **mapping}
        self.write_unit(reordered)
        self.assert_problem("out of order")

    def test_bad_enum(self) -> None:
        self.write_unit(unit_mapping(kind="guess"))
        self.assert_problem("kind 'guess' not in")

    def test_bad_marketplace(self) -> None:
        self.write_unit(unit_mapping(marketplaces=["US", "XX"]))
        self.assert_problem("marketplace 'XX' not in")

    def test_id_mismatch_with_file_name(self) -> None:
        self.write_unit(unit_mapping("KC-0001"), name="KC-0002_listing-suppressed.md")
        self.assert_problem("does not match file name prefix 'KC-0002'")

    def test_duplicate_id(self) -> None:
        self.write_unit(unit_mapping("KC-0001"), rebuild=False)
        self.write_unit(unit_mapping("KC-0001"), name="KC-0001_second-copy.md")
        self.assert_problem("duplicate id 'KC-0001'")

    def test_topic_must_match_folder(self) -> None:
        self.write_unit(unit_mapping(topic="logistics"), folder="catalog")
        self.assert_problem("does not match folder 'catalog'")

    def test_retired_folder_requires_retired_status(self) -> None:
        self.write_unit(unit_mapping(), folder="_retired")
        self.assert_problem("must have status retired")

    def test_missing_section(self) -> None:
        sections = dict(SECTIONS)
        del sections["Gaps"]
        self.write_unit(sections=sections)
        self.assert_problem("missing section '## Gaps'")

    def test_extra_section(self) -> None:
        self.write_unit(sections={**SECTIONS, "Notes": "Extra."})
        self.assert_problem("unexpected section '## Notes'")

    def test_empty_section(self) -> None:
        self.write_unit(sections={**SECTIONS, "Cause": ""})
        self.assert_problem("section '## Cause' is empty")

    def test_sections_out_of_order(self) -> None:
        names = list(SECTIONS)
        names[0], names[1] = names[1], names[0]
        self.write_unit(sections={name: SECTIONS[name] for name in names})
        self.assert_problem("sections out of order")

    def test_too_long(self) -> None:
        filler = "\n".join(f"Line {i}." for i in range(kb.LINE_CAP))
        self.write_unit(sections={**SECTIONS, "Gaps": filler})
        self.assert_problem(f"cap is {kb.LINE_CAP}")

    def test_spaced_em_dash(self) -> None:
        self.write_unit(sections={**SECTIONS, "Answer": "Check this \u2014 then that."})
        self.assert_problem("spaced em-dash")

    def test_planted_slack_id(self) -> None:
        slack_id = "U0" + "ABCDE1234"
        self.write_unit(sections={**SECTIONS, "Answer": f"Ask {slack_id} first."})
        self.assert_problem(f"scrub slack_id {slack_id}")

    def test_planted_denylist_term(self) -> None:
        self.write_unit(sections={**SECTIONS, "Answer": "This happened on nordwind-labs."})
        self.assert_problem("scrub term:Nordwind Labs nordwind-labs")

    def test_denylist_skipped_without_terms_file_unless_strict(self) -> None:
        self.write_unit(sections={**SECTIONS, "Answer": "This happened on nordwind-labs."})
        self.terms.unlink()
        self.assertEqual(lk.lint_knowledge(self.root, strict=False, terms_path=self.terms), [])
        problems = lk.lint_knowledge(self.root, strict=True, terms_path=self.terms)
        self.assertTrue(any("terms file missing" in p for p in problems), problems)

    def test_missing_source_path(self) -> None:
        missing = "Amazon Seller Help/articles/999-missing.md"
        self.write_unit(unit_mapping(amazon_sources=[missing]))
        self.assert_problem(f"amazon_sources path does not exist in the repo: {missing}")

    def test_unknown_skill(self) -> None:
        self.write_unit(unit_mapping(skills=["amazon-nonexistent"]))
        self.assert_problem("skill 'amazon-nonexistent' is not a directory")

    def test_provenance_must_match_id(self) -> None:
        self.write_unit(unit_mapping(provenance="ledger:KC-9999"))
        self.assert_problem("provenance must be 'ledger:KC-0001'")

    def test_month_format(self) -> None:
        self.write_unit(unit_mapping(observed="2026-9"))
        self.assert_problem("observed '2026-9' is not YYYY-MM")

    def test_verified_needs_date(self) -> None:
        self.write_unit(unit_mapping(verification="verified", verified_how="live-ui"))
        self.assert_problem("verified_on must be YYYY-MM-DD")

    def test_unverified_needs_empty_date(self) -> None:
        self.write_unit(unit_mapping(verified_on="2026-10-01"))
        self.assert_problem("verified_on must be empty")

    def test_unparseable_frontmatter(self) -> None:
        path = self.root / "knowledge" / "catalog" / "KC-0001_broken.md"
        path.write_text("---\nid: KC-0001\ntitle: 'single'\n---\n" + render_body(SECTIONS), encoding="utf-8")
        self.rebuild()
        self.assert_problem("KC-0001_broken.md:3: frontmatter:")

    def test_template_key_order_checked(self) -> None:
        mapping = unit_mapping("KC-0000")
        reordered = {"kind": mapping.pop("kind"), **mapping}
        (self.root / "knowledge" / "TEMPLATE.md").write_text(
            kb.dump_frontmatter(reordered) + render_body(SECTIONS), encoding="utf-8"
        )
        self.rebuild()
        problems = self.assert_problem("TEMPLATE.md")
        self.assertTrue(all("TEMPLATE.md" in p for p in problems), problems)

    def test_unit_in_unknown_folder(self) -> None:
        (self.root / "knowledge" / "misc").mkdir()
        self.rebuild()
        self.assert_problem("knowledge/misc:1: unknown folder")

    def test_drift_when_index_is_stale(self) -> None:
        self.write_unit(rebuild=False)
        problems = self.lint()
        self.assertTrue(any("knowledge-index.json: out of date" in p or "missing, run" in p for p in problems), problems)
        self.rebuild()
        self.assertEqual(self.lint(), [])

    def test_cli_exits_1_on_problems(self) -> None:
        self.write_unit(unit_mapping(kind="guess"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = lk.main(["--terms", str(self.terms), "--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("kind 'guess'", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
