from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import slack_collect as sc  # noqa: E402

TEAM_A = "UFAKE0001"
TEAM_B = "UFAKE0002"
BOT = "UFAKEBOT1"
EXTERNAL = "UFAKE0099"
CLIENT_CHANNEL = "CFAKE0001"
FORMER_CHANNEL = "CFAKE0002"
INTERNAL_CHANNEL = "CFAKE0003"
TS_BOT = "1700000000.000100"
TS_TEAM = "1700000100.000200"
TS_GERMAN = "1690000000.000300"
FAKE_ASIN = "B0FAKE0001"
FAKE_SHIPMENT = "FBA15ABCDE12"


def fake_config(**extra: object) -> dict:
    config = {
        "date_floor": "2023-10-01",
        "team": {"lead": [TEAM_A], "ops": [TEAM_B]},
        "bots_to_drop": {"note": "fake", "reporter": BOT},
        "resolution_markers": ["resolved", "erledigt"],
        "channel_families": {
            "client_current": [{"id": CLIENT_CHANNEL, "name": "acme-test-amazon", "slug": "acme-test"}],
            "client_former": [{"id": FORMER_CHANNEL, "name": "oldco-test", "slug": "oldco-test"}],
            "internal": [{"id": INTERNAL_CHANNEL, "name": "team-test"}],
            "excluded": [{"id": "CFAKE0009", "name": "alerts-test", "why": "bot alerts"}],
        },
    }
    config.update(extra)
    return config


def record(channel_id: str, ts: str, family: str, parent: dict, replies: list[dict], language: str = "en",
           topic_guess: str = "other", hint: bool = False, has_team: bool = False, slug: str = "") -> dict:
    users = []
    for m in [parent, *replies]:
        if m["user"] not in users:
            users.append(m["user"])
    return {
        "schema": "knowledge-sweep.thread.v1",
        "channel_id": channel_id,
        "channel_name": {CLIENT_CHANNEL: "acme-test-amazon", FORMER_CHANNEL: "oldco-test"}.get(channel_id, "team-test"),
        "family": family,
        "client_slug": slug,
        "thread_ts": ts,
        "parent": {"ts": ts, **parent},
        "replies": replies,
        "participants": users,
        "has_team_member": has_team,
        "first_glance": {"amazon_operational": True, "topic_guess": topic_guess, "has_resolution_hint": hint, "language": language},
        "collected_on": "2026-10-06",
        "collected_via": "mcp",
    }


def three_records() -> list[dict]:
    all_bot = record(
        CLIENT_CHANNEL, TS_BOT, "client_current",
        {"user": "bot:reporter", "text": "Daily report: ACOS 23%, budget used 80%"},
        [{"ts": "1700000000.000200", "user": BOT, "subtype": "bot_message", "text": "Campaign budget alert"}],
        topic_guess="ads", slug="acme-test",
    )
    team = record(
        CLIENT_CHANNEL, TS_TEAM, "client_current",
        {"user": TEAM_B, "text": f"Inbound shipment {FAKE_SHIPMENT} for {FAKE_ASIN} shows FBA_INB_0008, units not received"},
        [
            {"ts": "1700000200.000300", "user": TEAM_A, "text": "Checked the carrier tracking and opened a case. It is resolved now."},
        ],
        topic_guess="logistics", hint=True, has_team=True, slug="acme-test",
    )
    german = record(
        FORMER_CHANNEL, TS_GERMAN, "client_former",
        {"user": EXTERNAL, "text": "Das Listing ist gesperrt und die Variante wird als unterdrückt angezeigt. Was tun?"},
        [{"ts": "1690000100.000400", "user": TEAM_A, "text": "Attribut korrigiert, Hauptbild getauscht, erledigt."}],
        language="de", topic_guess="catalog", hint=True, has_team=True, slug="oldco-test",
    )
    return [all_bot, team, german]


def make_store(tmp: Path, config: dict | None = None, records: list[dict] | None = None) -> Path:
    """A fake sweep store under tmp/store with config, records and two checkpoints."""
    root = tmp / "store"
    root.mkdir(parents=True, exist_ok=True)
    (root / "config.json").write_text(json.dumps(config or fake_config()), encoding="utf-8")
    for rec in records if records is not None else three_records():
        path = root / "threads" / rec["channel_id"] / f"{rec['thread_ts']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    checkpoints = root / "checkpoints"
    checkpoints.mkdir(exist_ok=True)
    (checkpoints / f"{CLIENT_CHANNEL}-2024-H1.json").write_text(json.dumps({
        "channel_id": CLIENT_CHANNEL, "window": "2024-H1", "complete": True,
        "parents_seen": 10, "threads_stored": 2, "parents_skipped": 8,
    }), encoding="utf-8")
    (checkpoints / f"{CLIENT_CHANNEL}-2023-H2.json").write_text(json.dumps({
        "channel_id": CLIENT_CHANNEL, "window": "2023-H2", "complete": False,
        "parents_seen": 4, "threads_stored": 1, "parents_skipped": 3,
    }), encoding="utf-8")
    return root


def run(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sc.main(argv)
    return code, out.getvalue(), err.getvalue()


def ts_of(year: int, month: int, day: int) -> int:
    return int(dt.datetime(year, month, day, tzinfo=dt.timezone.utc).timestamp())


class PlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_half_year_windows_clamped_to_floor(self) -> None:
        windows = sc.windows_for("client_current", dt.date(2023, 10, 1), dt.date(2024, 8, 15))
        self.assertEqual([w["window"] for w in windows], ["2023-H2", "2024-H1", "2024-H2"])
        self.assertEqual(windows[0]["oldest"], ts_of(2023, 10, 1))
        self.assertEqual(windows[0]["latest"], ts_of(2024, 1, 1))
        self.assertEqual(windows[1]["oldest"], ts_of(2024, 1, 1))
        self.assertEqual(windows[1]["latest"], ts_of(2024, 7, 1))
        self.assertTrue(windows[2]["open"])
        self.assertEqual(windows[2]["latest"], ts_of(2024, 8, 16) - 1)

    def test_year_windows_for_low_volume_families(self) -> None:
        windows = sc.windows_for("client_former", dt.date(2023, 10, 1), dt.date(2024, 8, 15))
        self.assertEqual([w["window"] for w in windows], ["2023", "2024"])
        self.assertEqual(windows[0]["oldest"], ts_of(2023, 10, 1))
        self.assertEqual(windows[0]["latest"], ts_of(2024, 1, 1))

    def test_plan_reads_checkpoint_status_and_skips_excluded(self) -> None:
        code, out, _ = run(["plan", "--root", str(self.root), "--today", "2024-08-15", "--json"])
        self.assertEqual(code, 0)
        rows = json.loads(out)
        self.assertNotIn("CFAKE0009", {r["channel_id"] for r in rows})
        status = {(r["channel_id"], r["window"]): r["status"] for r in rows}
        self.assertEqual(status[(CLIENT_CHANNEL, "2023-H2")], "partial")
        self.assertEqual(status[(CLIENT_CHANNEL, "2024-H1")], "complete")
        self.assertEqual(status[(CLIENT_CHANNEL, "2024-H2")], "missing")
        self.assertEqual(status[(FORMER_CHANNEL, "2024")], "missing")
        self.assertEqual(len(rows), 3 + 2 + 3)

    def test_plan_family_since_and_text_output(self) -> None:
        code, out, _ = run(["plan", "--root", str(self.root), "--today", "2024-08-15", "--family", "client_current", "--since", "2024-03"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("windows: 2 across 1 channels"))
        self.assertIn("2024-H1", lines[1])
        self.assertIn("complete", lines[1])
        self.assertTrue(lines[2].endswith("missing open"))


class ValidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_store_records_are_valid(self) -> None:
        code, out, _ = run(["validate", "--root", str(self.root)])
        self.assertEqual(code, 0, out)
        self.assertIn("3 records, 0 with problems", out)

    def test_schema_errors_are_reported(self) -> None:
        bad = three_records()[1]
        del bad["participants"]
        bad["family"] = "clients"
        bad["thread_ts"] = "1700000100.2"
        bad["first_glance"]["language"] = "fr"
        bad["replies"][0].pop("user")
        bad["has_team_member"] = "yes"
        path = Path(self.tmp.name) / "bad.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        code, out, _ = run(["validate", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("missing required key 'participants'", out)
        self.assertIn("$.family: 'clients' not one of", out)
        self.assertIn("$.thread_ts: '1700000100.2' does not match", out)
        self.assertIn("$.first_glance.language: 'fr' not one of", out)
        self.assertIn("$.replies[0]: missing required key 'user'", out)
        self.assertIn("$.has_team_member: expected boolean", out)

    def test_file_name_must_match_thread_ts(self) -> None:
        rec = three_records()[1]
        path = Path(self.tmp.name) / CLIENT_CHANNEL / "1700000999.000000.json"
        path.parent.mkdir()
        path.write_text(json.dumps(rec), encoding="utf-8")
        code, out, _ = run(["validate", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("does not match the file name", out)


class StatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_stats_counts_windows_records_and_missing_channels(self) -> None:
        root = make_store(Path(self.tmp.name))
        code, out, _ = run(["stats", "--root", str(root), "--today", "2024-08-15"])
        self.assertEqual(code, 0)
        self.assertIn("[client_current] windows complete 1 / partial 1 / missing 1", out)
        self.assertIn("parents seen 14, stored 3 (records on disk 2), skipped 11, resolution hints 1, languages en 2", out)
        self.assertIn("[client_former] windows complete 0 / partial 0 / missing 2", out)
        self.assertIn("languages de 1", out)
        self.assertIn("channels in the config with no checkpoint: 2 of 3", out)
        self.assertIn(FORMER_CHANNEL, out.split("no checkpoint:")[1])
        self.assertIn(INTERNAL_CHANNEL, out.split("no checkpoint:")[1])
        self.assertNotIn("store is empty", out)

    def test_empty_store_says_so(self) -> None:
        root = Path(self.tmp.name) / "empty"
        root.mkdir()
        (root / "config.json").write_text(json.dumps(fake_config()), encoding="utf-8")
        code, out, _ = run(["stats", "--root", str(root), "--today", "2024-08-15"])
        self.assertEqual(code, 0)
        self.assertIn("store is empty", out)
        self.assertIn("no checkpoint: 3 of 3", out)


class CandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = make_store(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def read_candidates(self) -> list[dict]:
        text = (self.root / "candidates.jsonl").read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines()]

    def test_blocked_threads_never_become_candidates(self) -> None:
        blocked = {"channel_id": CLIENT_CHANNEL, "thread_ts": TS_TEAM, "reason": "fabricated evidence", "blocked_on": "2026-10-07"}
        (self.root / "blocked-threads.jsonl").write_text(json.dumps(blocked) + "\n# comment\nnot json\n", encoding="utf-8")
        code, out, err = run(["candidates", "--root", str(self.root)])
        self.assertEqual(code, 0)
        rows = self.read_candidates()
        self.assertNotIn(TS_TEAM, [r["thread_ts"] for r in rows])
        self.assertIn("blocked 1", out)
        self.assertIn("unreadable blocked-thread line", err)

    def test_scoring_order_flags_and_bot_drop(self) -> None:
        code, out, _ = run(["candidates", "--root", str(self.root)])
        self.assertEqual(code, 0)
        rows = self.read_candidates()
        self.assertEqual([r["thread_ts"] for r in rows], [TS_TEAM, TS_GERMAN])
        self.assertIn("dropped 1", out)
        team, german = rows
        self.assertEqual(team["topic"], "logistics")
        self.assertEqual(team["flags"], [])
        self.assertEqual(team["family"], "client_current")
        self.assertEqual(team["client_slug"], "acme-test")
        self.assertEqual(team["participants"], 2)
        self.assertTrue(team["has_resolution_hint"])
        self.assertTrue(team["parent_preview"].startswith("Inbound shipment"))
        self.assertGreater(team["score"], german["score"])
        self.assertEqual(german["topic"], "catalog")
        self.assertEqual(german["flags"], ["german", "external_participants"])
        self.assertIn("per topic: catalog 1, logistics 1", out)
        self.assertIn("per family: client_current 1, client_former 1", out)

    def test_score_components(self) -> None:
        lexicon = sc.Lexicon(sc.load_topics())
        team = three_records()[1]
        row = sc.score_record(team, fake_config(), lexicon)
        scores = lexicon.topic_scores([team["parent"]["text"], team["replies"][0]["text"]])
        # Keyword hits plus the double-weighted FBA_INB code, the resolution
        # marker bonus and one team reply.
        self.assertEqual(row["score"], scores["logistics"] + sc.RESOLUTION_BONUS + sc.TEAM_REPLY_BONUS)
        self.assertGreaterEqual(scores["logistics"], sc.ERROR_CODE_WEIGHT + 3)

    def test_filters_and_fallback_topic(self) -> None:
        code, _out, _ = run(["candidates", "--root", str(self.root), "--topic", "catalog"])
        self.assertEqual(code, 0)
        self.assertEqual([r["thread_ts"] for r in self.read_candidates()], [TS_GERMAN])
        run(["candidates", "--root", str(self.root), "--min-score", "999"])
        self.assertEqual(self.read_candidates(), [])

        lexicon = sc.Lexicon(sc.load_topics())
        plain = record(INTERNAL_CHANNEL, "1700000500.000000", "internal",
                       {"user": TEAM_A, "text": "hm?", "files": ["screenshot.png"]}, [],
                       topic_guess="seo", has_team=True)
        row = sc.score_record(plain, fake_config(), lexicon)
        self.assertEqual(row["topic"], "seo")
        self.assertEqual(row["flags"], ["attachments_only"])

    def test_no_team_and_no_hint_is_dropped(self) -> None:
        lexicon = sc.Lexicon(sc.load_topics())
        rec = record(CLIENT_CHANNEL, "1700000600.000000", "client_current",
                     {"user": EXTERNAL, "text": "Shipment question"}, [])
        self.assertIsNone(sc.score_record(rec, fake_config(), lexicon))

    def test_short_keywords_need_whole_words(self) -> None:
        lexicon = sc.Lexicon(sc.load_topics())
        self.assertNotIn("marke", lexicon.keyword_hits("the marketplace selector"))
        self.assertIn("marke", lexicon.keyword_hits("die Marke ist registriert"))
        self.assertIn("versand", lexicon.keyword_hits("der Versandplan fehlt"))
        self.assertEqual(lexicon.code_hits("we sold 8541 units"), [])
        self.assertEqual(lexicon.code_hits("Error 8541 on upload"), ["Error 8541"])


class TopicsFileTests(unittest.TestCase):
    def test_lexicon_shape(self) -> None:
        topics = sc.load_topics()
        names = set(topics["topics"])
        self.assertEqual(names, {"compliance", "logistics", "catalog", "support-cases", "ads", "account-health", "seo", "brand-registry", "reporting"})
        skills = {p.name for p in (REPO / "skills").iterdir() if p.is_dir()}
        for name, spec in topics["topics"].items():
            self.assertTrue(10 <= len(spec["keywords"]) <= 25, name)
            self.assertTrue(all(k == k.lower() for k in spec["keywords"]), name)
            self.assertTrue(set(spec["skills"]) <= skills, name)
        config_markers = ["resolved", "fixed", "works now", "erledigt", "gelöst", "funktioniert"]
        self.assertTrue(set(config_markers) <= set(topics["resolution_markers"]))


if __name__ == "__main__":
    unittest.main()
