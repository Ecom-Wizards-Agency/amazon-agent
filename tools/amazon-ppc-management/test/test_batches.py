#!/usr/bin/env python3
"""CLI tests for tools/amazon-ppc-management/batches.py (synthetic ids only)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "batches.py"
CLIENT = "testclient"


def row(entity_id="1000000001", field="bid", old=1.00, new=0.93, **extra):
    r = {"entity_type": "keyword", "entity_id": entity_id, "field": field,
         "old": old, "new": new, "name": f"kw {entity_id}"}
    r.update(extra)
    return r


class BatchesCliTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.base = self.tmp / "store"

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--base-dir", str(self.base), *args],
            capture_output=True, text=True, check=False)

    def rows_file(self, rows, name="rows.json"):
        p = self.tmp / name
        p.write_text(json.dumps(rows))
        return str(p)

    def snapshot(self, tag, rows, date, *extra):
        return self.run_cli(
            "snapshot", "--client", CLIENT, "--tag", tag, "--lever", "bid-down",
            "--group", "profit", "--note", f"{tag} test", "--rows",
            self.rows_file(rows, f"{tag}.rows.json"), "--date", date, *extra)

    def batch(self, tag):
        return json.loads((self.base / CLIENT / "batches" / f"{tag}.json").read_text())

    # snapshot

    def test_snapshot_writes_batch_file(self):
        rows = [row(), row("1000000002", old=0.80, new=0.74)]
        res = self.snapshot("testclient-2026W45-profit", rows, "2026-11-02")
        self.assertEqual(res.returncode, 0, res.stderr)
        b = self.batch("testclient-2026W45-profit")
        self.assertEqual(b["status"], "applied")
        self.assertEqual(b["date"], "2026-11-02")
        self.assertEqual(b["tag"], "testclient-2026W45-profit")
        self.assertEqual(b["opt_group"], "profit")
        self.assertEqual(b["lever"], "bid-down")
        self.assertIsNone(b["score"])
        self.assertIsNone(b["cooldown_bypass"])
        self.assertEqual(b["rows"], rows)

    def test_snapshot_refuses_existing_tag_without_force(self):
        self.assertEqual(self.snapshot("t1", [row()], "2026-10-01").returncode, 0)
        again = self.snapshot("t1", [row("1000000009")], "2026-10-20")
        self.assertNotEqual(again.returncode, 0)
        self.assertIn("batch exists", again.stderr)
        forced = self.snapshot("t1", [row("1000000009")], "2026-10-20", "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(self.batch("t1")["rows"][0]["entity_id"], "1000000009")

    def test_snapshot_rejects_rows_missing_keys(self):
        res = self.snapshot("t1", [{"entity_type": "keyword", "entity_id": "1000000001"}],
                            "2026-11-02")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("missing keys", res.stderr)

    # cooldown

    def test_cooldown_blocks_reapply_within_seven_days(self):
        self.assertEqual(self.snapshot("t1", [row()], "2026-11-01").returncode, 0)
        res = self.snapshot("t2", [row(old=0.93, new=0.88)], "2026-11-04")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("inside the 7d cooldown", res.stderr)
        conflicts = json.loads(res.stdout)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["entity"], "keyword:1000000001")
        self.assertEqual(conflicts[0]["batch"], "t1")
        self.assertEqual(conflicts[0]["days_ago"], 3)
        self.assertEqual(conflicts[0]["free_on"], "2026-11-08")
        self.assertFalse((self.base / CLIENT / "batches" / "t2.json").exists())

    def test_cooldown_bypass_is_recorded(self):
        self.assertEqual(self.snapshot("t1", [row()], "2026-11-01").returncode, 0)
        res = self.snapshot("t2", [row(field="state", old="enabled", new="paused")],
                            "2026-11-03", "--bypass-cooldown", "stock_gate")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.batch("t2")["cooldown_bypass"], "stock_gate")

    def test_cooldown_frees_entity_on_day_seven(self):
        self.assertEqual(self.snapshot("t1", [row()], "2026-11-01").returncode, 0)
        res = self.snapshot("t2", [row(old=0.93, new=0.88)], "2026-11-08")
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_check_ids_and_reverted_batches_are_ignored(self):
        self.assertEqual(self.snapshot("t1", [row(), row("1000000002")],
                                       "2026-11-01").returncode, 0)
        res = self.run_cli("check", "--client", CLIENT, "--date", "2026-11-03",
                           "--ids", "keyword:1000000001,keyword:1000000003")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual([c["entity"] for c in json.loads(res.stdout)],
                         ["keyword:1000000001"])
        self.assertIn("1 of 2 candidate entities", res.stderr)

        res = self.run_cli("mark-reverted", "--client", CLIENT, "--tag", "t1",
                           "--date", "2026-11-03")
        self.assertEqual(res.returncode, 0, res.stderr)
        res = self.run_cli("check", "--client", CLIENT, "--date", "2026-11-03",
                           "--ids", "keyword:1000000001")
        self.assertEqual(json.loads(res.stdout), [])

    # validate: caps are ceilings

    def validate(self, rows, *extra):
        return self.run_cli("validate", "--rows", self.rows_file(rows),
                            "--max-increase", "0.25", "--max-decrease", "0.10", *extra)

    def test_validate_errors_on_over_cap_delta(self):
        res = self.validate([row(old=1.00, new=0.85), row("1000000002", old=1.00, new=1.20)])
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("OVER CAP (10%): keyword:1000000001", res.stdout)
        self.assertNotIn("1000000002", res.stdout)
        self.assertIn("a cap is a ceiling, never the step", res.stderr)

    def test_validate_flags_at_cap_but_passes(self):
        res = self.validate([row(old=1.00, new=0.90), row("1000000002", old=2.00, new=2.50)])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("AT CAP (10%): keyword:1000000001", res.stdout)
        self.assertIn("AT CAP (25%): keyword:1000000002", res.stdout)
        self.assertIn("2 numeric rows checked: 0 over cap, 2 flagged", res.stderr)

    def test_validate_strict_fails_on_at_cap(self):
        res = self.validate([row(old=1.00, new=0.90)], "--strict")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("--strict", res.stderr)

    def test_validate_skips_non_numeric_and_zero_old(self):
        res = self.validate([
            row(field="state", old="enabled", new="paused"),
            row("1000000002", old=0, new=0.50),
            row("1000000003", old=1.00, new=0.95),
        ])
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("1 numeric rows checked: 0 over cap, 0 flagged", res.stderr)

    def test_validate_off_formula_flag_with_tacos(self):
        # rpc = 20 / 10 = 2.00; x 0.30 = 0.60 expected; 0.95 is > 25% off
        res = self.validate([row(old=1.00, new=0.95, clicks=10, revenue=20.0)],
                            "--tacos", "0.30")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("OFF FORMULA (rpc x tacos = 0.60)", res.stdout)

    # revert, status, score

    def test_revert_payload_and_source_neutral_hint(self):
        rows = [row(), row("1000000002", entity_type="campaign", field="budget",
                           old=25.0, new=31.0)]
        self.assertEqual(self.snapshot("t1", rows, "2026-11-01").returncode, 0)
        out = self.tmp / "revert.json"
        res = self.run_cli("revert", "--client", CLIENT, "--tag", "t1", "--out", str(out))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("revert payload (2 rows)", res.stdout)
        payload = json.loads(out.read_text())
        self.assertEqual(payload, [
            {"entity_type": "keyword", "entity_id": "1000000001", "name": "kw 1000000001",
             "field": "bid", "value": 1.00, "reverts": 0.93},
            {"entity_type": "campaign", "entity_id": "1000000002", "name": "kw 1000000002",
             "field": "budget", "value": 25.0, "reverts": 31.0},
        ])
        self.assertIn("SYNQ web app", res.stderr)
        self.assertIn("Campaign Manager", res.stderr)
        self.assertIn("AdLabs carve-out: AdLabs update_entities", res.stderr)
        self.assertIn("mark-reverted --client testclient --tag t1", res.stderr)

        stdout_res = self.run_cli("revert", "--client", CLIENT, "--tag", "t1")
        self.assertEqual(json.loads(stdout_res.stdout), payload)

        res = self.run_cli("mark-reverted", "--client", CLIENT, "--tag", "t1",
                           "--date", "2026-11-04", "--note", "test revert")
        self.assertEqual(res.returncode, 0, res.stderr)
        b = self.batch("t1")
        self.assertEqual(b["status"], "reverted")
        self.assertEqual(b["reverted"], {"date": "2026-11-04", "note": "test revert"})

    def test_revert_unknown_tag_fails(self):
        res = self.run_cli("revert", "--client", CLIENT, "--tag", "missing")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("no batch tagged missing", res.stderr)

    def test_status_due_for_scoring_then_scored(self):
        self.assertEqual(self.snapshot("t1", [row()], "2026-10-20").returncode, 0)
        self.assertEqual(self.snapshot("t2", [row("1000000002")], "2026-11-02").returncode, 0)
        res = self.run_cli("status", "--client", CLIENT, "--date", "2026-11-04")
        self.assertEqual(res.returncode, 0, res.stderr)
        lines = dict(line.split("  ", 1) for line in res.stdout.strip().splitlines())
        self.assertIn("DUE FOR SCORING", lines["t1"])
        self.assertIn("open", lines["t2"])

        res = self.run_cli("score", "--client", CLIENT, "--tag", "t1",
                           "--verdict", "worked: ACOS down, rank held", "--date", "2026-11-04")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.batch("t1")["score"],
                         {"date": "2026-11-04", "verdict": "worked: ACOS down, rank held"})
        res = self.run_cli("status", "--client", CLIENT, "--date", "2026-11-04")
        self.assertIn("scored", res.stdout.splitlines()[0])

    def test_status_empty_client(self):
        res = self.run_cli("status", "--client", CLIENT)
        self.assertEqual(res.returncode, 0)
        self.assertIn("no batches for testclient", res.stdout)


if __name__ == "__main__":
    unittest.main()
