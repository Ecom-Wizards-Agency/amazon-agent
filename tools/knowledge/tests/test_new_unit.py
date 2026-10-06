from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import kb_frontmatter as kb  # noqa: E402
import ledger  # noqa: E402
import new_unit  # noqa: E402

TEMPLATE = REPO / "knowledge" / "TEMPLATE.md"


def sample_card(**extra: object) -> dict:
    card = {
        "card_id": "CARD-0001",
        "source_kind": "slack-thread",
        "topic": "logistics",
        "kind": "diagnosis",
        "title": "Inbound shipment stuck at Checked-in for weeks",
        "skills": ["amazon-logistics"],
        "surface": "Seller Central > Shipments",
        "marketplaces": ["DE"],
        "marketplace_inferred": False,
        "symptom_keywords": ["shipment stuck checked in", "units not received"],
        "error_text": ["FBA_INB_0008"],
        "problem_as_asked": "The shipment shows Checked-in but no units are received.",
        "root_cause": "The carrier delivered the pallets to a different dock.",
        "resolution_steps": ["1. Open the shipment.", "Check the tracking events.", "- Open a case with the POD."],
        "verify": "Units move to Receiving within 72 hours.",
        "generic_lesson": "Wait for the receiving window, then open a case with proof of delivery.",
        "first_party_source_paths": ["Amazon Seller Help/articles/present.md", "Amazon Seller Help/articles/absent.md"],
        "related_sop_paths": ["MAG SOPs/logistics/sop.md"],
        "contradicts_paths": [],
        "resolution_status": "resolved",
        "fix_source": "amazon-support",
        "evidence_location": "case",
        "confidence": "medium",
        "coverage_verdict": "partial",
        "coverage_paths": ["MAG SOPs/logistics/sop.md"],
        "net_new": "The SOP does not cover the dock mix-up.",
        "publishable": True,
        "policy_risk": False,
        "client_specific_to_strip": ["Brandxplaceholder"],
        "who_answered": "ops-lead-role",
        "who_executed": "SAS manager",
        "date_first_seen": "2026-03-14",
        "date_resolved": "2026-03-30",
        "client_slug": "brandx",
        "channel_name": "client-brandx",
        "channel_id": "chan-placeholder",
        "parent_ts": "1710000000.000100",
        "related_ts": ["1710000001.000200"],
        "permalink": "https://example.invalid/thread",
        "identifiers": ["shipment-id-placeholder", "case-id a|b"],
        "notes": "Sibling thread in the same week",
    }
    card.update(extra)
    return card


class NewUnitFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        for folder in [*kb.TOPICS, "_retired"]:
            (self.root / "knowledge" / folder).mkdir(parents=True)
        (self.root / "Amazon Seller Help" / "articles").mkdir(parents=True)
        (self.root / "Amazon Seller Help" / "articles" / "present.md").write_text("x", encoding="utf-8")
        (self.root / "MAG SOPs" / "logistics").mkdir(parents=True)
        (self.root / "MAG SOPs" / "logistics" / "sop.md").write_text("x", encoding="utf-8")
        self.staging = self.root / "_local" / "knowledge-sweep" / "ledger-staging.md"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = new_unit.main(["--root", str(self.root), "--today", "2026-10-06", *args])
        return code, out.getvalue(), err.getvalue()

    def write_card(self, card: dict) -> Path:
        path = self.root / "card.json"
        path.write_text(json.dumps(card), encoding="utf-8")
        return path

    def unit_files(self) -> list[Path]:
        return sorted(self.root.glob("knowledge/*/KC-*.md"))


class IdAndSlugTests(NewUnitFixture):
    def test_first_id_is_one(self) -> None:
        self.assertEqual(new_unit.next_id(self.root), "KC-0001")

    def test_next_id_spans_topics_and_retired(self) -> None:
        (self.root / "knowledge" / "ads" / "KC-0004_a.md").write_text("", encoding="utf-8")
        (self.root / "knowledge" / "catalog" / "KC-0002_b.md").write_text("", encoding="utf-8")
        (self.root / "knowledge" / "_retired" / "KC-0009_c.md").write_text("", encoding="utf-8")
        (self.root / "knowledge" / "ads" / "notes.md").write_text("", encoding="utf-8")
        self.assertEqual(new_unit.next_id(self.root), "KC-0010")

    def test_forced_id_must_be_unused(self) -> None:
        (self.root / "knowledge" / "_retired" / "KC-0003_old.md").write_text("", encoding="utf-8")
        code, _out, err = self.run_main("--title", "A title", "--topic", "ads", "--id", "KC-0003", "--no-ledger")
        self.assertEqual(code, 1)
        self.assertIn("already used", err)
        code, out, _err = self.run_main("--title", "A title", "--topic", "ads", "--id", "KC-0042", "--no-ledger")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "knowledge" / "ads" / "KC-0042_a-title.md").is_file())

    def test_slug_rules(self) -> None:
        self.assertEqual(new_unit.slugify("  FBA: Shipment -- stuck @ Checked-in!! "), "fba-shipment-stuck-checked-in")
        self.assertEqual(new_unit.slugify("Ünits über"), "nits-ber")
        long = new_unit.slugify("word " * 40)
        self.assertLessEqual(len(long), 60)
        self.assertFalse(long.endswith("-"))
        self.assertFalse(long.startswith("-"))
        self.assertNotIn("--", long)
        self.assertEqual(new_unit.slugify("!!!"), "unit")


class CardMappingTests(NewUnitFixture):
    def build(self, **extra: object) -> tuple[dict, str]:
        return new_unit.build_unit(sample_card(**extra), "KC-0007", self.root, new_unit.dt.date(2026, 10, 6))

    def test_frontmatter_mapping(self) -> None:
        mapping, _body = self.build()
        self.assertEqual(list(mapping), kb.KEY_ORDER)
        self.assertEqual(mapping["title"], "Inbound shipment stuck at Checked-in for weeks")
        self.assertEqual(mapping["kind"], "diagnosis")
        self.assertEqual(mapping["topic"], "logistics")
        self.assertEqual(mapping["status"], "draft")
        self.assertEqual(mapping["skills"], ["amazon-logistics"])
        self.assertEqual(mapping["marketplaces"], ["DE"])
        self.assertIs(mapping["marketplace_inferred"], False)
        self.assertEqual(mapping["surface"], "Seller Central > Shipments")
        self.assertIs(mapping["surface_verified"], False)
        self.assertEqual(mapping["error_text"], ["FBA_INB_0008"])
        self.assertEqual(mapping["resolution_status"], "resolved")
        self.assertEqual(mapping["fix_source"], "amazon-support")
        self.assertEqual(mapping["evidence_location"], "case")
        self.assertEqual(mapping["confidence"], "medium")
        self.assertEqual(mapping["verification"], "unverified")
        self.assertEqual(mapping["verified_on"], "")
        self.assertEqual(mapping["verified_how"], "")
        self.assertEqual(mapping["amazon_sources"], ["Amazon Seller Help/articles/present.md"])
        self.assertEqual(mapping["related_sops"], ["MAG SOPs/logistics/sop.md"])
        self.assertEqual(mapping["supersedes"], [])
        self.assertEqual(mapping["contradicts"], [])
        self.assertEqual(mapping["observed"], "2026-03")
        self.assertEqual(mapping["review_by"], "2027-03")
        self.assertEqual(mapping["provenance"], "ledger:KC-0007")

    def test_defaults_without_optional_fields(self) -> None:
        card = sample_card()
        for key in ("skills", "marketplaces", "marketplace_inferred", "surface", "date_first_seen", "kind"):
            card.pop(key)
        mapping, _body = new_unit.build_unit(card, "KC-0001", self.root, new_unit.dt.date(2026, 10, 6))
        self.assertEqual(mapping["skills"], [])
        self.assertEqual(mapping["marketplaces"], ["all"])
        self.assertIs(mapping["marketplace_inferred"], True)
        self.assertEqual(mapping["surface"], "")
        self.assertEqual(mapping["kind"], "diagnosis")
        self.assertEqual(mapping["observed"], "2026-10")
        self.assertEqual(mapping["review_by"], "2027-10")

    def test_sections(self) -> None:
        _mapping, body = self.build()
        sections = dict(kb.split_sections(body))
        self.assertEqual([h for h, _t in kb.split_sections(body)], kb.SECTION_ORDER)
        self.assertEqual(sections["Question"], "The shipment shows Checked-in but no units are received.")
        self.assertTrue(sections["Answer"].startswith("Wait for the receiving window"))
        self.assertEqual(sections["Cause"], "The carrier delivered the pallets to a different dock.")
        self.assertEqual(
            sections["Fix"],
            "1. Open the shipment.\n2. Check the tracking events.\n3. Open a case with the POD.",
        )
        self.assertEqual(sections["Verify"], "Units move to Receiving within 72 hours.")
        template = dict(kb.split_sections(TEMPLATE.read_text(encoding="utf-8")))
        self.assertEqual(sections["Stop before"], template["Stop before"])
        self.assertIn("- First-party: `Amazon Seller Help/articles/present.md`", sections["Sources"])
        self.assertIn("- Also in: `MAG SOPs/logistics/sop.md`", sections["Sources"])
        self.assertIn("- Evidence: team vault ledger row for this id.", sections["Sources"])

    def test_missing_source_goes_to_gaps(self) -> None:
        mapping, body = self.build()
        gaps = dict(kb.split_sections(body))["Gaps"]
        self.assertNotIn("Amazon Seller Help/articles/absent.md", mapping["amazon_sources"])
        self.assertIn("not captured locally: `Amazon Seller Help/articles/absent.md`", gaps)
        self.assertIn("The SOP does not cover the dock mix-up.", gaps)
        self.assertIn("Existing coverage: partial", gaps)
        self.assertNotIn("None known.", gaps)

    def test_empty_fallbacks(self) -> None:
        card = sample_card(root_cause="", resolution_steps=[], verify="", net_new="", coverage_verdict="")
        card["first_party_source_paths"] = []
        card["related_sop_paths"] = []
        _mapping, body = new_unit.build_unit(card, "KC-0001", self.root, new_unit.dt.date(2026, 10, 6))
        sections = dict(kb.split_sections(body))
        self.assertEqual(sections["Cause"], "Not established in the source.")
        self.assertEqual(sections["Fix"], "1. See Answer.")
        self.assertEqual(sections["Verify"], "Not stated in the source.")
        self.assertEqual(sections["Gaps"], "None known.")
        self.assertIn("- Evidence: team vault ledger row for this id.", sections["Sources"])

    def test_output_parses_back(self) -> None:
        mapping, body = self.build()
        parsed, parsed_body, error = kb.parse_frontmatter(new_unit.render_unit(mapping, body))
        self.assertIsNone(error)
        self.assertEqual(parsed, mapping)
        self.assertEqual([h for h, _t in kb.split_sections(parsed_body)], kb.SECTION_ORDER)


class CliTests(NewUnitFixture):
    def test_dry_run_writes_nothing(self) -> None:
        card = self.write_card(sample_card(client_specific_to_strip=[]))
        with mock.patch.object(new_unit, "scrub_hits", return_value=[]):
            code, out, _err = self.run_main("--from-card", str(card), "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("---\nid: KC-0001\n"))
        self.assertEqual(self.unit_files(), [])
        self.assertFalse(self.staging.exists())

    def test_write_and_stage(self) -> None:
        card = self.write_card(sample_card())
        with mock.patch.object(new_unit, "scrub_hits", return_value=[]):
            code, out, err = self.run_main("--from-card", str(card))
        self.assertEqual(code, 0, err)
        path = self.root / "knowledge" / "logistics" / "KC-0001_inbound-shipment-stuck-at-checked-in-for-weeks.md"
        self.assertTrue(path.is_file())
        self.assertIn("wrote knowledge/logistics/KC-0001_", out)
        self.assertIn("staged ledger rows: 1", out)
        mapping, body, error = kb.read_unit(path)
        self.assertIsNone(error)
        self.assertEqual(mapping["id"], "KC-0001")
        self.assertEqual([h for h, _t in kb.split_sections(body)], kb.SECTION_ORDER)

        text = self.staging.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(lines[0], "| " + " | ".join(ledger.LEDGER_COLUMNS) + " |")
        self.assertEqual(len(lines), 3)
        self.assertEqual(
            lines[2],
            "| KC-0001 | brandx | client-brandx | 1710000000.000100 | https://example.invalid/thread"
            " | 2026-03-14 | 2026-03-30 | resolved | ops-lead-role | SAS manager | amazon-support | case"
            " | shipment-id-placeholder; case-id a/b | Sibling thread in the same week; related_ts: 1710000001.000200 |",
        )
        row = ledger.parse_table(text).rows[0]
        self.assertEqual(list(row), ledger.LEDGER_COLUMNS)
        self.assertEqual(row["channel"], "client-brandx")

        card2 = self.write_card(sample_card(title="Second problem", channel_name="", parent_ts="2"))
        with mock.patch.object(new_unit, "scrub_hits", return_value=[]):
            code, out, _err = self.run_main("--from-card", str(card2))
        self.assertEqual(code, 0)
        self.assertIn("KC-0002_second-problem.md", out)
        self.assertIn("staged ledger rows: 2", out)
        rows = ledger.parse_table(self.staging.read_text(encoding="utf-8")).rows
        self.assertEqual(rows[1]["channel"], "chan-placeholder")

    def test_no_ledger(self) -> None:
        code, out, _err = self.run_main("--title", "Bid changes not applied", "--topic", "ads", "--no-ledger")
        self.assertEqual(code, 0)
        self.assertFalse(self.staging.exists())
        self.assertIn("--no-ledger", out)

    def test_title_mode_fields(self) -> None:
        code, _out, _err = self.run_main(
            "--title", "Bid changes not applied", "--topic", "ads", "--kind", "procedure",
            "--skills", "amazon-ads-console, amazon-audit", "--marketplaces", "US,DE", "--no-ledger",
        )
        self.assertEqual(code, 0)
        mapping, _body, error = kb.read_unit(self.root / "knowledge" / "ads" / "KC-0001_bid-changes-not-applied.md")
        self.assertIsNone(error)
        self.assertEqual(mapping["kind"], "procedure")
        self.assertEqual(mapping["skills"], ["amazon-ads-console", "amazon-audit"])
        self.assertEqual(mapping["marketplaces"], ["US", "DE"])
        self.assertIs(mapping["marketplace_inferred"], False)

    def test_refuses_on_scrub_hit(self) -> None:
        card = self.write_card(sample_card(client_specific_to_strip=[]))
        with mock.patch.object(new_unit, "scrub_hits", return_value=["asin"]):
            code, _out, err = self.run_main("--from-card", str(card))
        self.assertEqual(code, 1)
        self.assertIn("asin", err)
        self.assertEqual(self.unit_files(), [])
        self.assertFalse(self.staging.exists())

    def test_refuses_on_card_strip_token(self) -> None:
        card = self.write_card(sample_card(generic_lesson="Brandxplaceholder saw this first."))
        with mock.patch.object(new_unit, "scrub_hits", return_value=[]):
            code, _out, err = self.run_main("--from-card", str(card))
        self.assertEqual(code, 1)
        self.assertIn("client-specific", err)
        self.assertEqual(self.unit_files(), [])

    def test_refuses_unpublishable_card(self) -> None:
        card = self.write_card(sample_card(publishable=False))
        code, _out, err = self.run_main("--from-card", str(card))
        self.assertEqual(code, 1)
        self.assertIn("publishable", err)

    def test_missing_scrub_module_is_skipped(self) -> None:
        err = io.StringIO()
        with mock.patch.object(new_unit, "_load_scrub", return_value=None), contextlib.redirect_stderr(err):
            self.assertIsNone(new_unit.scrub_hits("text"))
        self.assertIn("scrub check skipped", err.getvalue())

    def test_scrub_pattern_table_adapter(self) -> None:
        fake = mock.Mock(spec=["PATTERNS"])
        fake.PATTERNS = {"asin": r"\bB0[A-Z0-9]{8}\b"}
        with mock.patch.object(new_unit, "_load_scrub", return_value=fake):
            self.assertEqual(new_unit.scrub_hits("see " + "B0" + "ABCDEFGH"), ["asin"])
            self.assertEqual(new_unit.scrub_hits("clean"), [])

    def test_real_scrub_refuses_id_shapes(self) -> None:
        if new_unit._load_scrub() is None:
            self.skipTest("scrub.py not present")
        fake_asin = "B0" + "ABCDEFGH"
        card = self.write_card(sample_card(client_specific_to_strip=[], root_cause=f"Listing {fake_asin} was merged."))
        code, _out, err = self.run_main("--from-card", str(card))
        self.assertEqual(code, 1)
        self.assertIn("asin", err)
        self.assertEqual(self.unit_files(), [])
        clean = self.write_card(sample_card(client_specific_to_strip=[]))
        code, _out, err = self.run_main("--from-card", str(clean), "--no-ledger")
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
