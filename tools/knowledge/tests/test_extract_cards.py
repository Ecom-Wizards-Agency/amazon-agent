from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parents[2]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))
sys.path.insert(0, str(TESTS))

import extract_cards as ec  # noqa: E402
import slack_collect as sc  # noqa: E402
from test_slack_collect import (  # noqa: E402
    CLIENT_CHANNEL,
    FAKE_ASIN,
    FAKE_SHIPMENT,
    FORMER_CHANNEL,
    TEAM_A,
    TS_GERMAN,
    TS_TEAM,
    fake_config,
    make_store,
)

DENY_TERM = "Acmebrand"


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ec.main(argv)
    return code, out.getvalue(), err.getvalue()


def filled_card(card_id: str = "CARD-0001", **extra: object) -> dict:
    card = ec.empty_card(card_id, "slack-thread", "logistics", ["amazon-logistics"])
    card.update(
        {
            "title": "Inbound shipment shows FBA_INB_0008 and units are not received",
            "problem_as_asked": "The shipment shows an inbound error and no units are received.",
            "root_cause": "The carrier booked the delivery against a closed appointment.",
            "resolution_steps": ["Open the shipment in Send to Amazon.", "Open a case with the proof of delivery."],
            "verify": "Units move to Receiving within three days.",
            "generic_lesson": "Check the carrier appointment first, then open a case with the proof of delivery.",
            "symptom_keywords": ["units not received", "inbound error"],
            "error_text": ["FBA_INB_0008"],
            "evidence_location": "slack",
            "related_sop_paths": ["MAG SOPs/logistics/present.md"],
            "client_specific_to_strip": [FAKE_SHIPMENT, DENY_TERM],
            "identifiers": [FAKE_SHIPMENT],
        }
    )
    card.update(extra)
    return card


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = make_store(base, config=fake_config(workspace="fake-workspace.example.test"))
        self.repo = base / "repo"
        (self.repo / "MAG SOPs" / "logistics").mkdir(parents=True)
        (self.repo / "MAG SOPs" / "logistics" / "present.md").write_text("# present\n", encoding="utf-8")
        for spec in sc.load_topics()["topics"].values():
            for skill in spec["skills"]:
                (self.repo / "skills" / skill).mkdir(parents=True, exist_ok=True)
        self.terms = base / "terms.txt"
        self.terms.write_text(f"# fake denylist\n{DENY_TERM}\n", encoding="utf-8")
        self.common = ["--root", str(self.root), "--repo", str(self.repo), "--terms", str(self.terms)]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            sc.main(["candidates", "--root", str(self.root)])

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def state(self) -> dict:
        return json.loads((self.root / "cards" / "state.json").read_text(encoding="utf-8"))


class NextTests(Base):
    def test_next_prints_thread_and_scrubbed_preview(self) -> None:
        code, out, _ = run(["next", "--topic", "logistics", "--batch", "3", *self.common])
        self.assertEqual(code, 0)
        self.assertIn(f"=== {CLIENT_CHANNEL}:{TS_TEAM}", out)
        self.assertIn(f"UFAKE0002 {TS_TEAM}: Inbound shipment {FAKE_SHIPMENT}", out)
        self.assertIn(f"{TEAM_A} 1700000200.000300: Checked the carrier", out)
        preview = out.split("--- scrubbed preview")[1]
        self.assertIn("[REDACTED:shipment_id]", preview)
        self.assertIn("[REDACTED:asin]", preview)
        self.assertNotIn(FAKE_ASIN, preview)
        self.assertIn("next: 1 candidate(s)", out)

    def test_next_skips_scaffolded_threads(self) -> None:
        run(["scaffold", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", *self.common])
        code, out, _ = run(["next", "--topic", "logistics", "--batch", "3", *self.common])
        self.assertEqual(code, 0)
        self.assertIn("no uncarded candidates", out)


class ScaffoldTests(Base):
    def test_scaffold_prefills_provenance(self) -> None:
        code, out, err = run(["scaffold", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", *self.common])
        self.assertEqual(code, 0, err)
        path = self.root / "cards" / "candidate" / "CARD-0001.json"
        self.assertIn(str(path), out)
        card = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(card["source_kind"], "slack-thread")
        self.assertEqual(card["topic"], "logistics")
        self.assertEqual(card["skills"], ["amazon-logistics", "amazon-fba-inventory-planning"])
        self.assertEqual(card["channel_id"], CLIENT_CHANNEL)
        self.assertEqual(card["channel_name"], "acme-test-amazon")
        self.assertEqual(card["client_slug"], "acme-test")
        self.assertEqual(card["parent_ts"], TS_TEAM)
        self.assertEqual(card["permalink"], f"https://fake-workspace.example.test/archives/{CLIENT_CHANNEL}/p1700000100000200")
        self.assertFalse(card["participants_external"])
        self.assertEqual(card["language"], "en")
        self.assertEqual(card["date_first_seen"], "2023-11-14")
        self.assertEqual(card["who_answered"], TEAM_A)
        self.assertEqual(card["identifiers"], [FAKE_SHIPMENT, FAKE_ASIN])
        self.assertEqual(card["error_text"], ["FBA_INB_0008"])
        self.assertEqual(card["title"], "")
        self.assertEqual(card["generic_lesson"], "")
        self.assertEqual(self.state()["threads"][f"{CLIENT_CHANNEL}:{TS_TEAM}"]["status"], "scaffolded")
        # Every schema key is present.
        schema = json.loads(ec.CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(card), set(schema["properties"]))

    def test_numbering_spans_all_card_folders_and_external_flag(self) -> None:
        accepted = self.root / "cards" / "accepted"
        accepted.mkdir(parents=True)
        (accepted / "CARD-0007.json").write_text("{}", encoding="utf-8")
        (self.root / "cards" / "rejected").mkdir()
        (self.root / "cards" / "rejected" / "CARD-0003.json").write_text("{}", encoding="utf-8")
        code, _out, _err = run(["scaffold", "--thread", f"{FORMER_CHANNEL}:{TS_GERMAN}", *self.common])
        self.assertEqual(code, 0)
        card = json.loads((self.root / "cards" / "candidate" / "CARD-0008.json").read_text(encoding="utf-8"))
        self.assertTrue(card["participants_external"])
        self.assertEqual(card["language"], "de")
        self.assertEqual(card["topic"], "catalog")

    def test_permalink_without_workspace_falls_back_to_record(self) -> None:
        (self.root / "config.json").write_text(json.dumps(fake_config()), encoding="utf-8")
        run(["scaffold", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", *self.common])
        card = json.loads((self.root / "cards" / "candidate" / "CARD-0001.json").read_text(encoding="utf-8"))
        self.assertEqual(card["permalink"], "")

    def test_scaffold_twice_is_refused(self) -> None:
        run(["scaffold", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", *self.common])
        code, _out, err = run(["scaffold", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", *self.common])
        self.assertEqual(code, 1)
        self.assertIn("already has CARD-0001", err)


class ValidateTests(Base):
    def write(self, card: dict) -> Path:
        path = self.root / "cards" / "candidate" / f"{card['card_id']}.json"
        ec.write_card(path, card)
        return path

    def test_clean_card_passes(self) -> None:
        self.write(filled_card())
        code, out, _ = run(["validate", "CARD-0001", *self.common])
        self.assertEqual(code, 0, out)
        self.assertIn("CARD-0001: ok", out)

    def test_planted_asin_missing_path_and_terms_fail(self) -> None:
        self.write(filled_card(
            generic_lesson=f"Relist {FAKE_ASIN} after the carrier fix.",
            title=f"{DENY_TERM} shipment stuck",
            verify=f"Shipment {FAKE_SHIPMENT} shows Receiving.",
            related_sop_paths=["MAG SOPs/logistics/absent.md"],
            coverage_paths=["../outside.md"],
            problem_as_asked="",
            confidence="certain",
        ))
        code, out, _ = run(["validate", str(self.root / "cards" / "candidate" / "CARD-0001.json"), *self.common])
        self.assertEqual(code, 1)
        self.assertIn(f"$.generic_lesson: scrub hit asin '{FAKE_ASIN}'", out)
        self.assertIn(f"$.title: scrub hit term:{DENY_TERM}", out)
        self.assertIn(f"$.verify: contains client_specific_to_strip token '{FAKE_SHIPMENT}'", out)
        self.assertIn("$.related_sop_paths: path does not exist under the repo: 'MAG SOPs/logistics/absent.md'", out)
        self.assertIn("$.coverage_paths: path does not exist under the repo: '../outside.md'", out)
        self.assertIn("$.problem_as_asked: empty", out)
        self.assertIn("$.confidence: 'certain' not one of", out)

    def test_marketplace_and_skill_checks(self) -> None:
        self.write(filled_card(marketplaces=["DE", "XX"], skills=["amazon-logistics", "amazon-nonexistent"]))
        code, out, _ = run(["validate", "CARD-0001", *self.common])
        self.assertEqual(code, 1)
        self.assertIn("$.marketplaces: 'XX' not one of", out)
        self.assertNotIn("'DE' not one of", out)
        self.assertIn("$.skills: no skill folder skills/amazon-nonexistent", out)

    def test_missing_required_key(self) -> None:
        card = filled_card()
        del card["publishable"]
        self.write(card)
        code, out, _ = run(["validate", "CARD-0001", *self.common])
        self.assertEqual(code, 1)
        self.assertIn("missing required key 'publishable'", out)


def fake_search(results_by_query: dict[str, list[dict]], calls: list[list[str]]):
    def _run(cmd, **kwargs):
        calls.append(cmd)
        query = cmd[2]
        payload = {"query": query, "library": "all", "count": 0, "results": results_by_query.get(query, [])}
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
    return _run


class CoverageTests(Base):
    def setUp(self) -> None:
        super().setUp()
        refs = self.repo / "skills" / "amazon-logistics" / "references"
        refs.mkdir(parents=True)
        (refs / "inbound-appointments.md").write_text("Carrier appointment rules for inbound pallets.\n", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "other.md").write_text("Nothing relevant here, just an appointment.\n", encoding="utf-8")

    def coverage(self, results: dict[str, list[dict]], **card_extra: object) -> tuple[dict, list[list[str]], str]:
        path = self.root / "cards" / "candidate" / "CARD-0001.json"
        ec.write_card(path, filled_card(**card_extra))
        calls: list[list[str]] = []
        with mock.patch.object(ec.subprocess, "run", side_effect=fake_search(results, calls)):
            code, out, _ = run(["coverage", "CARD-0001", *self.common])
        self.assertEqual(code, 0)
        return json.loads(path.read_text(encoding="utf-8")), calls, out

    def test_full_when_a_unit_scores_high(self) -> None:
        unit = str(self.repo / "knowledge" / "logistics" / "KC-0001_x.md")
        card, calls, out = self.coverage({"FBA_INB_0008": [{"score": 420, "library": "Amazon Knowledge", "path": unit}]})
        self.assertEqual(card["coverage_verdict"], "full")
        self.assertEqual(card["coverage_paths"][0], "knowledge/logistics/KC-0001_x.md")
        queries = [c[2] for c in calls]
        self.assertEqual(queries, ["units not received inbound error", "FBA_INB_0008"])
        self.assertEqual(calls[0][0], "python3")
        self.assertIn("net_new is empty", out)

    def test_partial_from_mag_sop_score(self) -> None:
        sop = str(self.repo / "MAG SOPs" / "logistics" / "present.md")
        card, _calls, _ = self.coverage({"units not received inbound error": [{"score": 200, "library": "MAG SOPs", "path": sop}]},
                                        title="Shipment error with no units received")
        self.assertEqual(card["coverage_verdict"], "partial")
        self.assertEqual(card["coverage_paths"], ["MAG SOPs/logistics/present.md"])

    def test_partial_from_skill_reference_grep(self) -> None:
        card, _calls, out = self.coverage({}, title="Carrier appointment missed for inbound pallets")
        self.assertEqual(card["coverage_verdict"], "partial")
        self.assertEqual(card["coverage_paths"], ["skills/amazon-logistics/references/inbound-appointments.md"])
        self.assertIn("words ['carrier', 'inbound']", out)

    def test_none_and_first_party_below_full(self) -> None:
        card, _calls, _ = self.coverage({"FBA_INB_0008": [{"score": 120, "library": "Amazon Seller Help", "path": "/elsewhere/a.md"}]},
                                        title="Totally unrelated wording")
        self.assertEqual(card["coverage_verdict"], "none")
        self.assertEqual(card["coverage_paths"], [])


class MarkTests(Base):
    def test_mark_carded_and_skipped(self) -> None:
        code, _out, err = run(["mark", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", "--status", "carded", *self.common])
        self.assertEqual(code, 2)
        self.assertIn("--card is required", err)
        code, _out, _ = run(["mark", "--thread", f"{CLIENT_CHANNEL}:{TS_TEAM}", "--status", "carded", "--card", "CARD-0004", "--reason", "clear fix", *self.common])
        self.assertEqual(code, 0)
        code, _out, _ = run(["mark", "--thread", f"{FORMER_CHANNEL}:{TS_GERMAN}", "--status", "skipped", "--reason", "client-only", *self.common])
        self.assertEqual(code, 0)
        threads = self.state()["threads"]
        self.assertEqual(threads[f"{CLIENT_CHANNEL}:{TS_TEAM}"]["card"], "CARD-0004")
        self.assertEqual(threads[f"{CLIENT_CHANNEL}:{TS_TEAM}"]["status"], "carded")
        self.assertEqual(threads[f"{FORMER_CHANNEL}:{TS_GERMAN}"]["reason"], "client-only")
        code, out, _ = run(["next", "--topic", "catalog", "--batch", "3", *self.common])
        self.assertIn("no uncarded candidates", out)


if __name__ == "__main__":
    unittest.main()
