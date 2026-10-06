from __future__ import annotations

import contextlib
import io
import json
import os
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
import review  # noqa: E402
import slack_collect as sc  # noqa: E402
from test_extract_cards import DENY_TERM, filled_card  # noqa: E402
from test_slack_collect import CLIENT_CHANNEL, FAKE_ASIN, TS_TEAM, fake_config, make_store  # noqa: E402

SEP = " \u2014 "
UNIT_REL = "knowledge/logistics/KC-0001_inbound-shipment-shows-error.md"


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = review.main(argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.base = base
        self.root = make_store(base, config=fake_config())
        self.repo = base / "repo"
        (self.repo / "MAG SOPs" / "logistics").mkdir(parents=True)
        (self.repo / "MAG SOPs" / "logistics" / "present.md").write_text("# present\n", encoding="utf-8")
        for spec in sc.load_topics()["topics"].values():
            for skill in spec["skills"]:
                (self.repo / "skills" / skill).mkdir(parents=True, exist_ok=True)
        self.terms = base / "terms.txt"
        self.terms.write_text(f"{DENY_TERM}\n", encoding="utf-8")
        self.common = ["--root", str(self.root), "--repo", str(self.repo), "--terms", str(self.terms), "--today", "2026-10-06"]
        self.candidate = self.root / "cards" / "candidate"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def add_card(self, card: dict) -> Path:
        path = self.candidate / f"{card['card_id']}.json"
        ec.write_card(path, card)
        return path

    def state(self) -> dict:
        return json.loads((self.root / "cards" / "state.json").read_text(encoding="utf-8"))

    def queue_text(self) -> str:
        return (self.root / "review-queue.md").read_text(encoding="utf-8")


class QueueTests(Base):
    def test_queue_groups_flags_and_keeps_ticks(self) -> None:
        self.add_card(filled_card("CARD-0001", coverage_verdict="partial"))
        self.add_card(filled_card("CARD-0002", topic="ads", skills=["amazon-ads-console"], policy_risk=True,
                                  participants_external=True, title="Budget runs out before noon"))
        self.add_card(filled_card("CARD-0003", generic_lesson=f"Relist {FAKE_ASIN}."))
        code, out, _ = run(["queue", *self.common])
        self.assertEqual(code, 0)
        self.assertIn("queue: 2 card(s)", out)
        self.assertIn("left out because they fail validation: CARD-0003", out)
        text = self.queue_text()
        self.assertLess(text.index("## ads"), text.index("## logistics"))
        self.assertIn(
            "- [ ] CARD-0001 · logistics · Inbound shipment shows FBA_INB_0008 and units are not received"
            " · unknown · low · no flags · partial",
            text,
        )
        self.assertIn("- [ ] CARD-0002 · ads · Budget runs out before noon · unknown · low"
                      " · policy_risk, external · unchecked", text)

        (self.root / "review-queue.md").write_text(text.replace("- [ ] CARD-0001", "- [x] CARD-0001"), encoding="utf-8")
        self.add_card(filled_card("CARD-0004", title="Second inbound error"))
        run(["queue", *self.common])
        text = self.queue_text()
        self.assertIn("- [x] CARD-0001", text)
        self.assertIn("- [ ] CARD-0004", text)
        self.assertIn("- [ ] CARD-0002", text)

    def test_queue_topic_filter(self) -> None:
        self.add_card(filled_card("CARD-0001"))
        self.add_card(filled_card("CARD-0002", topic="ads", skills=["amazon-ads-console"]))
        run(["queue", "--topic", "ads", *self.common])
        text = self.queue_text()
        self.assertIn("CARD-0002", text)
        self.assertNotIn("CARD-0001", text)


class FakeTools:
    """Stands in for new_unit.py, build_knowledge_index.py and lint_knowledge.py.

    lint_codes and build_codes give the exit code per call in order; the last
    one repeats. lint_saw records the unit's status line at each lint call.
    """

    def __init__(self, repo: Path, lint_code: int = 0, lint_codes: list[int] | None = None,
                 build_codes: list[int] | None = None) -> None:
        self.repo = repo
        self.lint_codes = list(lint_codes or [lint_code])
        self.build_codes = list(build_codes or [0])
        self.lint_saw: list[str] = []
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    @staticmethod
    def _next(codes: list[int]) -> int:
        return codes.pop(0) if len(codes) > 1 else codes[0]

    def unit_status(self) -> str:
        unit = self.repo / UNIT_REL
        if not unit.is_file():
            return "missing"
        return next((line for line in unit.read_text(encoding="utf-8").splitlines() if line.startswith("status:")), "")

    def __call__(self, repo: Path, script: str, *extra: str) -> subprocess.CompletedProcess:
        self.calls.append((script, extra))
        if script == "new_unit.py":
            unit = self.repo / UNIT_REL
            unit.parent.mkdir(parents=True, exist_ok=True)
            unit.write_text("---\nid: KC-0001\nstatus: draft\n---\n", encoding="utf-8")
            staging = Path(extra[extra.index("--staging") + 1])
            with staging.open("a", encoding="utf-8") as fh:
                fh.write("| KC-0001 | staged row |\n")
            return subprocess.CompletedProcess([script], 0, stdout=f"wrote {UNIT_REL}\nstaged ledger rows: 1\n", stderr="")
        if script == "lint_knowledge.py":
            self.lint_saw.append(self.unit_status())
            code = self._next(self.lint_codes)
            return subprocess.CompletedProcess([script], code, stdout="knowledge lint: 1 problem\n" if code else "ok\n", stderr="")
        code = self._next(self.build_codes)
        return subprocess.CompletedProcess([script], code, stdout="index failed\n" if code else "index ok\n", stderr="")


class PromoteTests(Base):
    def setUp(self) -> None:
        super().setUp()
        card = filled_card("CARD-0001", channel_id=CLIENT_CHANNEL, parent_ts=TS_TEAM, channel_name="acme-test-amazon",
                           client_slug="acme-test", permalink="https://fake-workspace.example.test/archives/x/p1")
        self.add_card(card)
        self.add_card(filled_card("CARD-0002", policy_risk=True, policy_risk_reason="counterfeit claim"))
        run(["queue", *self.common])

    def tick(self, card_id: str) -> None:
        path = self.root / "review-queue.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn(f"- [ ] {card_id}", text)
        path.write_text(text.replace(f"- [ ] {card_id}", f"- [x] {card_id}"), encoding="utf-8")

    def promote(self, tools: FakeTools, *argv: str) -> tuple[int, str, str]:
        with mock.patch.object(review, "run_tool", side_effect=tools):
            return run(["promote", *argv, *self.common])

    def test_refuses_unticked_card(self) -> None:
        tools = FakeTools(self.repo)
        with mock.patch.object(review, "run_tool", side_effect=tools):
            code, _out, err = run(["promote", "--card", "CARD-0001", "--ticked-by", "operations-lead", *self.common])
        self.assertEqual(code, 2)
        self.assertIn("is not ticked [x]", err)
        self.assertEqual(tools.calls, [])

    def test_refuses_policy_risk_without_agency_lead_override(self) -> None:
        self.tick("CARD-0002")
        tools = FakeTools(self.repo)
        with mock.patch.object(review, "run_tool", side_effect=tools):
            code, _out, err = run(["promote", "--card", "CARD-0002", "--ticked-by", "operations-lead", *self.common])
            self.assertEqual(code, 2)
            self.assertIn("only the agency lead decides it", err)
            code, _out, err = run(["promote", "--card", "CARD-0002", "--ticked-by", "operations-lead", "--agency-lead-override", *self.common])
            self.assertEqual(code, 2)
        self.assertEqual(tools.calls, [])
        self.assertTrue((self.candidate / "CARD-0002.json").is_file())

    def test_refuses_publishable_false_even_with_override(self) -> None:
        self.add_card(filled_card("CARD-0003", publishable=False))
        run(["queue", *self.common])
        self.tick("CARD-0003")
        tools = FakeTools(self.repo)
        code, _out, err = self.promote(tools, "--card", "CARD-0003", "--ticked-by", "agency-lead", "--agency-lead-override")
        self.assertEqual(code, 2)
        self.assertIn("new_unit.py refuses such cards", err)
        self.assertEqual(tools.calls, [])

    def test_refuses_role_outside_its_topics(self) -> None:
        self.tick("CARD-0001")
        code, _out, err = run(["promote", "--card", "CARD-0001", "--ticked-by", "ads-lead", *self.common])
        self.assertEqual(code, 2)
        self.assertIn("ads-lead does not tick logistics cards", err)

    def test_promote_success(self) -> None:
        self.tick("CARD-0001")
        tools = FakeTools(self.repo)
        with mock.patch.object(review, "run_tool", side_effect=tools):
            code, out, err = run(["promote", "--card", "CARD-0001", "--ticked-by", "operations-lead", *self.common])
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip().splitlines()[-1], UNIT_REL)
        self.assertEqual([c[0] for c in tools.calls], ["new_unit.py", "build_knowledge_index.py", "lint_knowledge.py",
                                                       "build_knowledge_index.py", "lint_knowledge.py"])
        self.assertEqual(tools.lint_saw, ["status: draft", "status: reviewed"])
        self.assertIn("--strict", tools.calls[4][1])
        self.assertEqual(tools.unit_status(), "status: reviewed")
        new_unit_args = tools.calls[0][1]
        self.assertEqual(new_unit_args[:2], ("--from-card", str(self.candidate / "CARD-0001.json")))
        self.assertIn("--root", new_unit_args)
        self.assertIn("--readme", tools.calls[1][1])
        self.assertIn("--strict", tools.calls[2][1])
        self.assertFalse((self.candidate / "CARD-0001.json").exists())
        self.assertTrue((self.root / "cards" / "accepted" / "CARD-0001.json").is_file())
        entry = self.state()["cards"]["CARD-0001"]
        self.assertEqual(entry["unit_path"], UNIT_REL)
        self.assertEqual(entry["unit_id"], "KC-0001")
        self.assertEqual(entry["ticked_by"], "operations-lead")
        self.assertEqual(entry["promoted_on"], "2026-10-06")
        self.assertEqual(self.state()["threads"][f"{CLIENT_CHANNEL}:{TS_TEAM}"]["status"], "promoted")
        ledger = [json.loads(line) for line in (self.root / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger[0]["card"], "CARD-0001")
        self.assertEqual(ledger[0]["unit_id"], "KC-0001")
        self.assertEqual(ledger[0]["client_slug"], "acme-test")

    def test_tick_source_is_recorded(self) -> None:
        self.tick("CARD-0001")
        queue = self.root / "review-queue.md"
        code, _out, err = self.promote(FakeTools(self.repo), "--card", "CARD-0001", "--ticked-by", "operations-lead")
        self.assertEqual(code, 0, err)
        entry = self.state()["cards"]["CARD-0001"]
        self.assertEqual(entry["tick_source"], "queue")
        self.assertEqual(entry["queue_path"], str(queue))
        ledger = json.loads((self.root / "ledger.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(ledger["tick_source"], "queue")
        self.assertEqual(ledger["queue_path"], str(queue))

    def test_tick_in_custom_queue_file(self) -> None:
        other = self.base / "elsewhere-queue.md"
        other.write_text("- [x] CARD-0001 · logistics · hand-ticked\n", encoding="utf-8")
        code, _out, err = self.promote(FakeTools(self.repo), "--card", "CARD-0001", "--ticked-by", "operations-lead",
                                       "--queue", str(other))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.state()["cards"]["CARD-0001"]["queue_path"], str(other))

    def test_agent_only_promote_is_refused(self) -> None:
        tools = FakeTools(self.repo)
        # The old --confirm-tick bypass no longer exists; argparse rejects it.
        with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(io.StringIO()):
            self.promote(tools, "--card", "CARD-0001", "--ticked-by", "agency-lead", "--confirm-tick")
        self.assertEqual(caught.exception.code, 2)
        # No combination of flags stands in for the queue tick.
        code, _out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "agency-lead", "--agency-lead-override")
        self.assertEqual(code, 2)
        self.assertIn("is not ticked [x]", err)
        self.assertEqual(tools.calls, [])
        self.assertTrue((self.candidate / "CARD-0001.json").is_file())
        self.assertFalse((self.root / "ledger.jsonl").exists())

    def test_override_without_tick_is_refused(self) -> None:
        tools = FakeTools(self.repo)
        code, _out, err = self.promote(tools, "--card", "CARD-0002", "--ticked-by", "agency-lead", "--agency-lead-override")
        self.assertEqual(code, 2)
        self.assertIn("--agency-lead-override needs that tick too", err)
        self.tick("CARD-0002")
        code, _out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "operations-lead", "--agency-lead-override")
        self.assertEqual(code, 2)
        self.assertIn("is not ticked [x]", err)
        self.tick("CARD-0001")
        code, _out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "operations-lead", "--agency-lead-override")
        self.assertEqual(code, 2)
        self.assertIn("accepted only with --ticked-by agency-lead", err)
        self.assertEqual(tools.calls, [])

    def test_agency_lead_override_with_queue_tick(self) -> None:
        self.tick("CARD-0002")
        code, _out, err = self.promote(FakeTools(self.repo), "--card", "CARD-0002", "--ticked-by", "agency-lead",
                                       "--agency-lead-override")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / "cards" / "accepted" / "CARD-0002.json").is_file())

    def test_unattended_refusal(self) -> None:
        self.tick("CARD-0001")
        tools = FakeTools(self.repo)
        with mock.patch.dict(os.environ, {"WIZARDS_AI_MODE": "1"}):
            code, _out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "agency-lead")
        self.assertEqual(code, 2)
        self.assertIn("WIZARDS_AI_MODE=1", err)
        self.assertEqual(tools.calls, [])
        self.assertTrue((self.candidate / "CARD-0001.json").is_file())

    def test_post_tick_lint_failure_restores_draft(self) -> None:
        self.tick("CARD-0001")
        tools = FakeTools(self.repo, lint_codes=[0, 1])
        code, out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "operations-lead")
        self.assertEqual(code, 1)
        self.assertIn("lint_knowledge.py --strict failed after setting", err)
        self.assertIn("knowledge lint: 1 problem", out)
        self.assertEqual(tools.lint_saw, ["status: draft", "status: reviewed"])
        self.assertEqual(tools.unit_status(), "status: draft")
        self.assertEqual([c[0] for c in tools.calls][-1], "build_knowledge_index.py")
        self.assertTrue((self.candidate / "CARD-0001.json").is_file())
        self.assertFalse((self.root / "cards" / "accepted" / "CARD-0001.json").exists())
        self.assertFalse((self.root / "ledger.jsonl").exists())
        self.assertFalse((self.root / "cards" / "state.json").exists())

    def test_post_tick_index_failure_returns_nonzero(self) -> None:
        self.tick("CARD-0001")
        tools = FakeTools(self.repo, build_codes=[0, 1, 0])
        code, _out, err = self.promote(tools, "--card", "CARD-0001", "--ticked-by", "operations-lead")
        self.assertEqual(code, 1)
        self.assertIn("build_knowledge_index.py failed after setting", err)
        self.assertEqual([c[0] for c in tools.calls], ["new_unit.py", "build_knowledge_index.py", "lint_knowledge.py",
                                                       "build_knowledge_index.py", "build_knowledge_index.py"])
        self.assertEqual(tools.unit_status(), "status: draft")
        self.assertTrue((self.candidate / "CARD-0001.json").is_file())
        self.assertFalse((self.root / "ledger.jsonl").exists())

    def test_lint_failure_rolls_back(self) -> None:
        self.tick("CARD-0001")
        staging = self.root / "ledger-staging.md"
        staging.write_text("| header |\n", encoding="utf-8")
        tools = FakeTools(self.repo, lint_code=1)
        with mock.patch.object(review, "run_tool", side_effect=tools):
            code, out, err = run(["promote", "--card", "CARD-0001", "--ticked-by", "agency-lead", *self.common])
        self.assertEqual(code, 1)
        self.assertIn("knowledge lint: 1 problem", out)
        self.assertIn("lint_knowledge.py --strict failed", err)
        self.assertFalse((self.repo / UNIT_REL).exists())
        self.assertEqual(staging.read_text(encoding="utf-8"), "| header |\n")
        self.assertTrue((self.candidate / "CARD-0001.json").is_file())
        self.assertEqual([c[0] for c in tools.calls][-1], "build_knowledge_index.py")
        self.assertFalse((self.root / "ledger.jsonl").exists())

    def test_invalid_card_is_not_promoted(self) -> None:
        self.add_card(filled_card("CARD-0004", generic_lesson=f"Relist {FAKE_ASIN}."))
        # The queue leaves invalid cards out; a hand-written tick still meets validation.
        with (self.root / "review-queue.md").open("a", encoding="utf-8") as fh:
            fh.write("- [x] CARD-0004 · logistics · hand-ticked\n")
        tools = FakeTools(self.repo)
        with mock.patch.object(review, "run_tool", side_effect=tools):
            code, _out, err = run(["promote", "--card", "CARD-0004", "--ticked-by", "agency-lead", *self.common])
        self.assertEqual(code, 1)
        self.assertIn("scrub hit asin", err)
        self.assertEqual(tools.calls, [])


class RejectTests(Base):
    def test_reject_moves_card_and_records_reason(self) -> None:
        self.add_card(filled_card("CARD-0001", channel_id=CLIENT_CHANNEL, parent_ts=TS_TEAM))
        code, _out, _ = run(["reject", "--card", "CARD-0001", "--reason", "client-only arrangement", *self.common])
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "cards" / "rejected" / "CARD-0001.json").is_file())
        self.assertFalse((self.candidate / "CARD-0001.json").exists())
        state = self.state()
        self.assertEqual(state["cards"]["CARD-0001"]["reason"], "client-only arrangement")
        self.assertEqual(state["threads"][f"{CLIENT_CHANNEL}:{TS_TEAM}"]["status"], "rejected")
        code, _out, _ = run(["reject", "--card", "CARD-0001", "--reason", "again", *self.common])
        self.assertEqual(code, 2)


LESSONS = "\n".join([
    "---",
    "type: lessons",
    "---",
    "",
    "## Lessons",
    f"- 2026-10-03{SEP}[agent-test]{SEP}A flat file upload that shows accepted only means Amazon received it. Check the"
    f" displayed attribute on the detail page before an appeal.{SEP}Fakebrand run, {FAKE_ASIN} checked 03.10.2026",
    f"- 2026-10-02{SEP}[agent-test]{SEP}In the design tool, a bound paint drops its opacity; clone it and set opacity again.{SEP}design file",
    f"- 2026-01-05{SEP}[agent-test]{SEP}Inbound shipment stuck at checked-in needs a case with the carrier proof.{SEP}older run",
    f"- 2026-10-01{SEP}[agent-test]{SEP}Error 8541 on a flat file means the contribution conflicts with catalog data.",
    "",
])


class ImportLessonsTests(Base):
    def setUp(self) -> None:
        super().setUp()
        self.vault = self.base / "vault"
        (self.vault / "Lessons").mkdir(parents=True)
        self.lessons = self.vault / "Lessons" / "wizards-ai-lessons.md"
        self.lessons.write_text(LESSONS, encoding="utf-8")
        self.terms.write_text("Fakebrand\n", encoding="utf-8")

    def test_import_filters_and_scaffolds(self) -> None:
        before = self.lessons.read_bytes()
        code, out, _ = run(["import-lessons", "--vault", str(self.vault), "--since", "2026-09-01", *self.common])
        self.assertEqual(code, 0)
        self.assertIn("import-lessons: 2 card(s); 0 already imported; 1 not Amazon-operational", out)
        cards = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(self.candidate.glob("CARD-*.json"))}
        self.assertEqual(sorted(cards), ["CARD-0001", "CARD-0002"])
        first = cards["CARD-0001"]
        self.assertEqual(first["source_kind"], "lesson")
        self.assertEqual(first["topic"], "catalog")
        self.assertEqual(first["title"], "A flat file upload that shows accepted only means Amazon received it")
        self.assertTrue(first["generic_lesson"].startswith("A flat file upload"))
        self.assertTrue(first["generic_lesson"].endswith("before an appeal."))
        self.assertEqual(first["notes"], f"Fakebrand run, {FAKE_ASIN} checked 03.10.2026")
        self.assertEqual(first["evidence_location"], "run-note")
        self.assertEqual(first["identifiers"], [FAKE_ASIN])
        self.assertIn("Fakebrand", first["client_specific_to_strip"])
        self.assertEqual(first["date_first_seen"], "2026-10-03")
        second = cards["CARD-0002"]
        self.assertEqual(second["error_text"], ["Error 8541"])
        self.assertEqual(second["evidence_location"], "none")
        self.assertEqual(second["notes"], "")
        self.assertEqual(self.lessons.read_bytes(), before)

        code, out, _ = run(["import-lessons", "--vault", str(self.vault), "--since", "2026-09-01", *self.common])
        self.assertIn("import-lessons: 0 card(s); 2 already imported", out)

    def test_parse_lesson_keeps_inner_separators(self) -> None:
        lesson = review.parse_lesson(f"- 2026-10-03{SEP}[a]{SEP}one{SEP}two{SEP}evidence")
        self.assertEqual(lesson["text"], f"one{SEP}two")
        self.assertEqual(lesson["evidence"], "evidence")
        self.assertIsNone(review.parse_lesson("- not a lesson"))


class RunNoteTests(Base):
    def setUp(self) -> None:
        super().setUp()
        ledger = self.root / "ledger.jsonl"
        rows = [
            {"card": "CARD-0001", "unit_id": "KC-0001", "unit_path": UNIT_REL, "topic": "logistics", "channel_id": CLIENT_CHANNEL,
             "channel_name": "acme-test-amazon", "client_slug": "acme-test", "parent_ts": TS_TEAM,
             "permalink": "https://fake-workspace.example.test/archives/x/p1", "ticked_by": "operations-lead", "promoted_on": "2026-10-06"},
            {"card": "CARD-0009", "unit_id": "KC-0009", "topic": "ads", "promoted_on": "2026-09-01"},
        ]
        ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        state_dir = self.root / "cards"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "state.json").write_text(json.dumps({"cards": {"CARD-0005": {"status": "rejected", "rejected_on": "2026-10-06"}}}),
                                              encoding="utf-8")
        self.vault = self.base / "vault"
        (self.vault / "Runs").mkdir(parents=True)

    def test_run_note_content(self) -> None:
        code, out, err = run(["run-note", "--date", "2026-10-06", "--vault", str(self.vault), *self.common])
        self.assertEqual(code, 0, err)
        note = (self.vault / "Runs" / "2026-10-06-knowledge-sweep.md").read_text(encoding="utf-8")
        self.assertTrue(note.startswith("---\ntype: run\ndate: 2026-10-06\nworkflow: knowledge-sweep\n"))
        self.assertIn("| CARD-0001 | KC-0001 | logistics | acme-test-amazon | acme-test | https://fake-workspace.example.test/archives/x/p1 | operations-lead |", note)
        self.assertNotIn("KC-0009", note)
        self.assertIn("Rejected: CARD-0005.", note)
        self.assertNotIn(" \u2014 ", note)
        code, _out, err = run(["run-note", "--date", "2026-10-06", "--vault", str(self.vault), *self.common])
        self.assertEqual(code, 1)
        self.assertIn("pass --force", err)

    def test_out_path_and_unattended_refusal(self) -> None:
        out_path = self.base / "elsewhere" / "note.md"
        code, _out, _ = run(["run-note", "--date", "2026-10-06", "--vault", str(self.vault), "--out", str(out_path), *self.common])
        self.assertEqual(code, 0)
        self.assertTrue(out_path.is_file())
        self.assertFalse((self.vault / "Runs" / "2026-10-06-knowledge-sweep.md").exists())
        with mock.patch.dict(os.environ, {"WIZARDS_AI_MODE": "1"}):
            code, _out, err = run(["run-note", "--date", "2026-10-07", "--vault", str(self.vault), *self.common])
        self.assertEqual(code, 2)
        self.assertIn("WIZARDS_AI_MODE=1", err)
        self.assertFalse((self.vault / "Runs" / "2026-10-07-knowledge-sweep.md").exists())


if __name__ == "__main__":
    unittest.main()
