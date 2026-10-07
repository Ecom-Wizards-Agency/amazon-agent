import json
import os
import subprocess
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifactctl import ArtifactRegistry, archive_metadata, parser, sha

CTL = Path(__file__).resolve().parent / "artifactctl.py"
BUNDLE = {
    "client": "client", "dataset": "logistics", "market": "DE",
    "bundle_date": "2026-08-27", "bundle_scope": "DE to UK",
    "bundle_partner": "Partner", "bundle_carrier": "Carrier",
}
STUB_HELPER = """
import json, hashlib, sys
from pathlib import Path
args = sys.argv[1:]
sources = []
while args and not args[0].startswith("--"):
    sources.append(Path(args.pop(0)))
def digest(path, name):
    return hashlib.new(name, path.read_bytes()).hexdigest()
print(json.dumps({"provider": "pcloud", "verified": True, "mode": "stub", "argv": sys.argv[1:],
                  "files": [{"source": str(p.resolve()), "sha1": digest(p, "sha1"),
                             "sha256": digest(p, "sha256"), "remote_path": "remote/" + p.name}
                            for p in sources]}))
"""


class FakeClock:
    def __init__(self):
        self.value = datetime(2026, 8, 27, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, **kwargs):
        self.value += timedelta(**kwargs)


class ArtifactLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.work = self.root / "work"
        self.work.mkdir()
        self.clock = FakeClock()
        self.registry = ArtifactRegistry(
            self.root / "runtime",
            [self.work],
            self.clock,
            archive_runner=self.archive_receipt,
        )

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def archive_receipt(paths, _archive):
        return {
            "provider": "pcloud",
            "verified": True,
            "files": [
                {
                    "source": str(path.resolve()),
                    "sha1": sha(path, "sha1"),
                    "sha256": sha(path),
                    "remote_path": f"remote/{path.name}",
                }
                for path in paths
            ],
        }

    def make_run(self, disposition="reproducible", name="file.csv", **register):
        run = self.registry.start_run("test", "workflow", "client")
        path = self.work / name
        path.write_text("contents", encoding="utf-8")
        artifact = self.registry.register(run["id"], path, disposition, **register)
        return run, artifact, path

    def test_seven_day_eligibility_and_thirty_day_purge(self):
        run, artifact, path = self.make_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=6, hours=23)
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.clock.advance(hours=1)
        result = self.registry.cleanup()
        self.assertEqual("quarantined", result["actions"][0]["action"])
        self.assertFalse(path.exists())
        quarantine = Path(result["actions"][0]["quarantine_path"])
        self.assertTrue(quarantine.is_file())
        self.clock.advance(days=29, hours=23)
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.clock.advance(hours=1)
        self.assertEqual("purged", self.registry.cleanup()["actions"][0]["action"])
        self.assertFalse(quarantine.exists())
        self.assertEqual("purged", self.registry.get_artifact(artifact["id"])["state"])

    def test_failed_and_active_runs_are_preserved(self):
        run, _, path = self.make_run()
        self.clock.advance(days=60)
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.registry.complete_run(run["id"], "failed")
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.assertTrue(path.exists())

    def test_changed_file_returns_to_review(self):
        run, artifact, path = self.make_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        path.write_text("changed", encoding="utf-8")
        result = self.registry.cleanup()
        self.assertEqual("preserved", result["actions"][0]["action"])
        self.assertEqual("review", self.registry.get_artifact(artifact["id"])["state"])

    def test_restore_preserves_file_from_immediate_recleanup(self):
        run, artifact, path = self.make_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        self.registry.cleanup()
        restored = self.registry.restore(artifact["id"])
        self.assertEqual("preserved", restored["state"])
        self.assertTrue(path.is_file())
        self.clock.advance(days=60)
        self.assertEqual([], self.registry.cleanup()["actions"])

    def test_source_backed_requires_exact_flatfilepro_origin(self):
        run, artifact, path = self.make_run(
            disposition="source-backed",
            source_origin="https://example.com/export",
        )
        self.assertEqual("review", artifact["state"])
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.assertTrue(path.exists())

        run2, _, path2 = self.make_run(
            disposition="source-backed",
            name="flatfile.csv",
            source_origin="https://app.flatfile.pro/export?id=1",
        )
        self.registry.complete_run(run2["id"], "success")
        self.clock.advance(days=8)
        self.assertEqual("quarantined", self.registry.cleanup()["actions"][0]["action"])
        self.assertFalse(path2.exists())

    def test_drive_final_requires_verified_receipt_for_same_hash(self):
        run, _, path = self.make_run(disposition="verify-drive", name="final.xlsx")
        receipt = {
            "provider": "google-drive",
            "verified": True,
            "remote_id": "drive-file-id",
            "mime_type": "application/vnd.google-apps.spreadsheet",
            "parents": ["drive-folder-id"],
            "local_sha256": sha(path),
        }
        self.registry.register(run["id"], path, "verify-drive", receipt=receipt)
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        self.assertEqual("quarantined", self.registry.cleanup()["actions"][0]["action"])

    def test_pcloud_batch_is_verified_before_local_quarantine(self):
        run = self.registry.start_run("test", "poe", "client")
        archive = {
            "client": "client", "dataset": "opportunity-data", "market": "US",
            "month": "2026-08", "report_type": "POE", "scope": "ALL",
        }
        paths = []
        for name in ("one.csv", "two.csv"):
            path = self.work / name
            path.write_text(name, encoding="utf-8")
            paths.append(path)
            self.registry.register(run["id"], path, "archive-pcloud", archive=archive)
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        result = self.registry.cleanup()
        self.assertEqual(2, result["counts"]["quarantined"])
        self.assertTrue(all(not path.exists() for path in paths))

    def test_incomplete_pcloud_receipt_preserves_entire_batch(self):
        run = self.registry.start_run("test", "poe", "client")
        archive = {
            "client": "client", "dataset": "opportunity-data", "market": "US",
            "month": "2026-08", "report_type": "POE", "scope": "ALL",
        }
        paths = []
        for name in ("one.csv", "two.csv"):
            path = self.work / ("incomplete-" + name)
            path.write_text(name, encoding="utf-8")
            paths.append(path)
            self.registry.register(run["id"], path, "archive-pcloud", archive=archive)
        self.registry.archive_runner = lambda batch, spec: {
            "provider": "pcloud", "verified": True,
            "files": [{
                "source": str(batch[0].resolve()), "sha1": sha(batch[0], "sha1"),
                "sha256": sha(batch[0]), "remote_path": "remote/one.csv",
            }],
        }
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        result = self.registry.cleanup()
        self.assertEqual(2, result["counts"]["preserved"])
        self.assertTrue(all(path.exists() for path in paths))

    def test_bundle_metadata_needs_date_and_scope_not_monthly_keys(self):
        args = parser().parse_args([
            "register", "--run", "r", "--path", "f", "--disposition", "archive-pcloud",
            "--archive-client", "client", "--archive-dataset", "logistics", "--archive-market", "DE",
            "--archive-bundle-date", "2026-08-27", "--archive-bundle-scope", "DE to UK",
            "--archive-bundle-root", str(self.work),
        ])
        meta = archive_metadata(args)
        self.assertEqual("2026-08-27", meta["bundle_date"])
        self.assertEqual("DE to UK", meta["bundle_scope"])
        self.assertEqual(str(self.work.resolve()), meta["bundle_root"])
        self.assertIsNone(meta["scope"])
        self.assertIsNone(meta["month"])
        monthly = archive_metadata(parser().parse_args([
            "register", "--run", "r", "--path", "f", "--disposition", "archive-pcloud",
            "--archive-month", "2026-08",
        ]))
        self.assertEqual("ALL-SKUS", monthly["scope"])
        self.assertIsNone(archive_metadata(parser().parse_args([
            "register", "--run", "r", "--path", "f", "--disposition", "reproducible",
        ])))

        path = self.work / "2026-08-27_client_DE_labels.pdf"
        path.write_text("labels", encoding="utf-8")
        for key in ("bundle_date", "bundle_scope"):
            with self.assertRaisesRegex(ValueError, key):
                ArtifactRegistry._archive_pcloud(self.registry, [path], {**BUNDLE, key: None})
        with self.assertRaisesRegex(ValueError, "month"):
            ArtifactRegistry._archive_pcloud(self.registry, [path], {
                "client": "client", "dataset": "reporting", "market": "DE", "scope": "ALL-SKUS",
            })
        helper = self.root / "stub-archive-raw.py"
        helper.write_text(STUB_HELPER, encoding="utf-8")
        previous = os.environ.get("AMAZON_ARTIFACT_PCLOUD_HELPER")
        os.environ["AMAZON_ARTIFACT_PCLOUD_HELPER"] = str(helper)
        try:
            receipt = ArtifactRegistry._archive_pcloud(
                self.registry, [path], {**BUNDLE, "bundle_root": str(self.work), "scope": None, "month": None},
            )
        finally:
            if previous is None:
                os.environ.pop("AMAZON_ARTIFACT_PCLOUD_HELPER")
            else:
                os.environ["AMAZON_ARTIFACT_PCLOUD_HELPER"] = previous
        argv = receipt["argv"]
        for flag, value in (
            ("--bundle-date", "2026-08-27"), ("--bundle-scope", "DE to UK"),
            ("--bundle-partner", "Partner"), ("--bundle-carrier", "Carrier"),
            ("--bundle-root", str(self.work)), ("--dataset", "logistics"),
        ):
            self.assertEqual(value, argv[argv.index(flag) + 1])
        for flag in ("--month", "--report-type", "--scope"):
            self.assertNotIn(flag, argv)

    def make_bundle_run(self):
        run = self.registry.start_run("test", "logistics", "client")
        paths, ids = [], []
        for name in ("2026-08-27_client_DE_labels.pdf", "2026-08-27_client_DE_packing-plan.xlsx"):
            path = self.work / name
            path.write_text(name, encoding="utf-8")
            paths.append(path)
            ids.append(self.registry.register(run["id"], path, "archive-pcloud", archive=BUNDLE)["id"])
        return run, paths, ids

    def journal_actions(self):
        with self.registry.connect() as con:
            return [row[0] for row in con.execute("SELECT action FROM journal ORDER BY id")]

    def test_archive_stores_receipt_then_weekly_cleanup_quarantines_without_rerun(self):
        run, paths, ids = self.make_bundle_run()
        calls = []

        def runner(batch, spec):
            calls.append((list(batch), spec))
            receipt = self.archive_receipt(batch, spec)
            receipt["mode"] = "bundle"
            receipt["bundle"] = {"path": "1_Delivery/1.1_Clients/Client/_Data/logistics/2026-08-27 - DE to UK - Partner - Carrier", "folderid": 7}
            return receipt

        self.registry.archive_runner = runner
        result = self.registry.archive(run["id"])
        self.assertEqual(1, len(calls))
        self.assertEqual("DE to UK", calls[0][1]["bundle_scope"])
        self.assertEqual(sorted(ids), sorted(result["archived"]))
        self.assertEqual([], result["preserved"])
        self.assertEqual(2, len(result["remote_paths"]))
        self.assertEqual(1, len(result["bundles"]))
        self.assertEqual(2, result["bundles"][0]["files"])
        for artifact_id in ids:
            artifact = self.registry.get_artifact(artifact_id)
            self.assertEqual("registered", artifact["state"])
            self.assertIsNone(artifact["eligible_at"])
            self.assertTrue(artifact["receipt"]["verified"])
        self.assertEqual(2, self.journal_actions().count("archived"))

        again = self.registry.archive(run["id"])
        self.assertEqual(1, len(calls))
        self.assertEqual([], again["archived"])
        self.assertEqual(sorted(ids), sorted(again["already_archived"]))

        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=6)
        self.assertEqual([], self.registry.cleanup()["actions"])
        self.clock.advance(days=2)
        cleanup = self.registry.cleanup()
        self.assertEqual(2, cleanup["counts"]["quarantined"])
        self.assertEqual(1, len(calls))
        self.assertTrue(all(not path.exists() for path in paths))

    def test_archive_runner_failure_leaves_state_unchanged(self):
        run, paths, ids = self.make_bundle_run()
        self.registry.complete_run(run["id"], "success")
        before = {artifact_id: self.registry.get_artifact(artifact_id) for artifact_id in ids}

        def failing(_batch, _spec):
            raise RuntimeError("pCloud unavailable")

        self.registry.archive_runner = failing
        result = self.registry.archive(run["id"])
        self.assertEqual([], result["archived"])
        self.assertEqual(
            ["pcloud-archive-failed:RuntimeError"] * 2,
            [item["reason"] for item in result["preserved"]],
        )
        self.assertEqual(["pCloud unavailable"] * 2, [item["detail"] for item in result["preserved"]])
        for artifact_id in ids:
            after = self.registry.get_artifact(artifact_id)
            self.assertEqual(before[artifact_id]["state"], after["state"])
            self.assertEqual(before[artifact_id]["eligible_at"], after["eligible_at"])
            self.assertIsNone(after["receipt"])
            self.assertIsNone(after["claim_at"])
        self.assertNotIn("archived", self.journal_actions())
        self.assertTrue(all(path.exists() for path in paths))

    def test_archive_audit_only_calls_no_runner(self):
        run, _, ids = self.make_bundle_run()

        def forbidden(_batch, _spec):
            raise AssertionError("audit-only must not call the archive runner")

        self.registry.archive_runner = forbidden
        result = self.registry.archive(run["id"], audit_only=True)
        self.assertEqual(sorted(ids), sorted(result["would_archive"]))
        self.assertEqual([], result["archived"])
        self.assertEqual([], result["preserved"])
        self.assertEqual(2, self.journal_actions().count("would-archive"))
        for artifact_id in ids:
            artifact = self.registry.get_artifact(artifact_id)
            self.assertEqual("registered", artifact["state"])
            self.assertIsNone(artifact["receipt"])

    def test_interrupted_archive_claim_returns_to_previous_state(self):
        run, _, ids = self.make_bundle_run()
        old_claim = (self.clock() - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        with self.registry.connect() as con:
            con.execute(
                "UPDATE artifacts SET state='archiving',claim_prev_state='registered',claim_at=? WHERE id=?",
                (old_claim, ids[0]),
            )
        self.registry.cleanup()
        self.assertEqual("registered", self.registry.get_artifact(ids[0])["state"])

    def bundle_runner(self, calls, during=None):
        def runner(batch, spec):
            calls.append(list(batch))
            if during:
                during()
            receipt = self.archive_receipt(batch, spec)
            receipt["mode"] = "bundle"
            receipt["bundle"] = {"path": "bundle/2026-08-27 - DE to UK", "folderid": 7}
            return receipt
        return runner

    def test_claim_prev_state_column_is_added_to_an_existing_registry(self):
        run, _, ids = self.make_bundle_run()
        with self.registry.connect() as con:
            con.execute("ALTER TABLE artifacts DROP COLUMN claim_prev_state")
            self.assertNotIn("claim_prev_state", {row["name"] for row in con.execute("PRAGMA table_info(artifacts)")})
        calls = []
        reopened = ArtifactRegistry(self.root / "runtime", [self.work], self.clock, archive_runner=self.bundle_runner(calls))
        with reopened.connect() as con:
            self.assertIn("claim_prev_state", {row["name"] for row in con.execute("PRAGMA table_info(artifacts)")})
        self.assertEqual(sorted(ids), sorted(reopened.archive(run["id"])["archived"]))
        self.assertEqual(1, len(calls))

    def test_concurrent_archive_and_cleanup_call_the_runner_once(self):
        run, paths, ids = self.make_bundle_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        calls = []
        self.registry.archive_runner = self.bundle_runner(calls)
        original = self.registry.pending_archive
        cleanups = []

        def racing(run_id):
            rows = original(run_id)
            if not cleanups:
                cleanups.append(self.registry.cleanup())
            return rows

        self.registry.pending_archive = racing
        result = self.registry.archive(run["id"])
        self.assertEqual(1, len(calls))
        self.assertEqual(2, cleanups[0]["counts"]["quarantined"])
        self.assertEqual([], result["archived"])
        self.assertNotIn("archived", self.journal_actions())
        self.assertTrue(all(not path.exists() for path in paths))

    def test_concurrent_archive_calls_the_runner_once(self):
        run, _, ids = self.make_bundle_run()
        calls = []
        self.registry.archive_runner = self.bundle_runner(calls)
        original = self.registry.pending_archive
        inner = []

        def racing(run_id):
            rows = original(run_id)
            if not inner:
                inner.append(None)
                inner[0] = self.registry.archive(run_id)
            return rows

        self.registry.pending_archive = racing
        outer = self.registry.archive(run["id"])
        self.assertEqual(1, len(calls))
        self.assertEqual(sorted(ids), sorted(inner[0]["archived"]))
        self.assertEqual([], outer["archived"])
        self.assertEqual(sorted(ids), sorted(outer["already_archived"]))
        self.assertEqual(2, self.journal_actions().count("archived"))

    def test_run_completion_during_archive_keeps_the_receipt(self):
        run, _, ids = self.make_bundle_run()
        calls = []
        self.registry.archive_runner = self.bundle_runner(
            calls, during=lambda: self.registry.complete_run(run["id"], "success"),
        )
        result = self.registry.archive(run["id"])
        self.assertEqual(sorted(ids), sorted(result["archived"]))
        for artifact_id in ids:
            artifact = self.registry.get_artifact(artifact_id)
            self.assertEqual("eligible-pending", artifact["state"])
            self.assertIsNotNone(artifact["eligible_at"])
            self.assertTrue(artifact["receipt"]["verified"])
        self.clock.advance(days=8)
        self.assertEqual(2, self.registry.cleanup()["counts"]["quarantined"])
        self.assertEqual(1, len(calls))

    def test_failed_run_completion_during_archive_preserves_with_receipt(self):
        run, _, ids = self.make_bundle_run()
        self.registry.archive_runner = self.bundle_runner(
            [], during=lambda: self.registry.complete_run(run["id"], "failed"),
        )
        self.registry.archive(run["id"])
        for artifact_id in ids:
            artifact = self.registry.get_artifact(artifact_id)
            self.assertEqual("preserved", artifact["state"])
            self.assertTrue(artifact["receipt"]["verified"])

    def test_archive_reports_only_receipts_that_were_stored(self):
        run, _, ids = self.make_bundle_run()

        def steal_claim():
            with self.registry.connect() as con:
                con.execute("UPDATE artifacts SET state='registered',claim_at=NULL WHERE state='archiving'")

        self.registry.archive_runner = self.bundle_runner([], during=steal_claim)
        result = self.registry.archive(run["id"])
        self.assertEqual([], result["archived"])
        self.assertEqual(["pcloud-receipt-not-stored"] * 2, [item["reason"] for item in result["preserved"]])
        self.assertNotIn("archived", self.journal_actions())

    def test_archive_skips_failed_run_and_review_files(self):
        def forbidden(_batch, _spec):
            raise AssertionError("excluded states must not reach the runner")

        self.registry.archive_runner = forbidden
        run, _, ids = self.make_bundle_run()
        self.registry.complete_run(run["id"], "failed")
        result = self.registry.archive(run["id"])
        self.assertEqual([], result["archived"])
        self.assertEqual([], result["preserved"])
        self.assertEqual({"preserved"}, {item["state"] for item in result["skipped"]})
        self.assertEqual(sorted(ids), sorted(item["artifact_id"] for item in result["skipped"]))

        outside = self.root / "2026-08-27_client_DE_outside.pdf"
        outside.write_text("outside", encoding="utf-8")
        review_run = self.registry.start_run("test", "logistics", "client")
        artifact = self.registry.register(review_run["id"], outside, "archive-pcloud", archive=BUNDLE)
        self.assertEqual("review", artifact["state"])
        review = self.registry.archive(review_run["id"])
        self.assertEqual([{"artifact_id": artifact["id"], "path": str(outside.resolve()), "state": "review"}], review["skipped"])
        self.assertEqual([], self.registry.pending_archive(review_run["id"]))

    def test_run_complete_prints_archive_reminder(self):
        env = {
            **os.environ,
            "AMAZON_ARTIFACT_RUNTIME_DIR": str(self.root / "cli-runtime"),
            "AMAZON_ARTIFACT_ALLOWED_ROOTS": str(self.work),
        }

        def cli(*args):
            return subprocess.run(
                [sys.executable, str(CTL), *args], capture_output=True, text=True, env=env, check=False,
            )

        path = self.work / "2026-08-27_client_DE_labels.pdf"
        path.write_text("labels", encoding="utf-8")
        run_id = json.loads(cli("run", "start", "--owner", "test", "--workflow", "logistics").stdout)["id"]
        registered = cli(
            "register", "--run", run_id, "--path", str(path), "--disposition", "archive-pcloud",
            "--archive-client", "client", "--archive-dataset", "logistics", "--archive-market", "DE",
            "--archive-bundle-date", "2026-08-27", "--archive-bundle-scope", "DE to UK",
        )
        self.assertEqual(0, registered.returncode, registered.stderr)
        self.assertEqual("DE to UK", json.loads(registered.stdout)["archive"]["bundle_scope"])
        completed = cli("run", "complete", "--run", run_id)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])
        self.assertIn(f"artifactctl archive --run {run_id}", completed.stderr)

        other = self.work / "plain.csv"
        other.write_text("plain", encoding="utf-8")
        plain_run = json.loads(cli("run", "start", "--owner", "test", "--workflow", "reporting").stdout)["id"]
        cli("register", "--run", plain_run, "--path", str(other), "--disposition", "reproducible")
        quiet = cli("run", "complete", "--run", plain_run)
        self.assertEqual("", quiet.stderr)

        failed_path = self.work / "2026-08-27_client_DE_failed.pdf"
        failed_path.write_text("failed", encoding="utf-8")
        failed_run = json.loads(cli("run", "start", "--owner", "test", "--workflow", "logistics").stdout)["id"]
        cli(
            "register", "--run", failed_run, "--path", str(failed_path), "--disposition", "archive-pcloud",
            "--archive-client", "client", "--archive-dataset", "logistics", "--archive-market", "DE",
            "--archive-bundle-date", "2026-08-27", "--archive-bundle-scope", "DE to UK",
        )
        failed = cli("run", "complete", "--run", failed_run, "--outcome", "failed")
        self.assertEqual(0, failed.returncode, failed.stderr)
        self.assertEqual("", failed.stderr)

    def test_cli_archive_exits_2_with_ok_false_when_a_file_is_preserved(self):
        helper = self.root / "must-not-run.py"
        helper.write_text("import sys\nsys.exit('archive helper must not run')\n", encoding="utf-8")
        env = {
            **os.environ,
            "AMAZON_ARTIFACT_RUNTIME_DIR": str(self.root / "cli-runtime"),
            "AMAZON_ARTIFACT_ALLOWED_ROOTS": str(self.work),
            "AMAZON_ARTIFACT_PCLOUD_HELPER": str(helper),
        }

        def cli(*args):
            return subprocess.run(
                [sys.executable, str(CTL), *args], capture_output=True, text=True, env=env, check=False,
            )

        path = self.work / "2026-08-27_client_DE_labels.pdf"
        path.write_text("labels", encoding="utf-8")
        run_id = json.loads(cli("run", "start", "--owner", "test", "--workflow", "logistics").stdout)["id"]
        cli("register", "--run", run_id, "--path", str(path), "--disposition", "archive-pcloud")
        result = cli("archive", "--run", run_id)
        self.assertEqual(2, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual("pcloud-archive-metadata-missing", payload["preserved"][0]["reason"])
        audit = cli("archive", "--run", run_id, "--audit-only")
        self.assertEqual(2, audit.returncode)
        self.assertFalse(json.loads(audit.stdout)["ok"])

    def test_concurrent_cleanup_claims_each_file_once(self):
        run, _, _ = self.make_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        outputs = []
        errors = []

        def worker():
            try:
                outputs.append(self.registry.cleanup())
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual([], errors)
        actions = [item for result in outputs for item in result["actions"]]
        self.assertEqual(1, sum(item["action"] == "quarantined" for item in actions))

    def test_interrupted_claim_is_recovered_after_one_hour(self):
        run, artifact, _ = self.make_run()
        self.registry.complete_run(run["id"], "success")
        self.clock.advance(days=8)
        old_claim = (self.clock() - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
        with self.registry.connect() as con:
            con.execute(
                "UPDATE artifacts SET state='processing',claim_at=? WHERE id=?",
                (old_claim, artifact["id"]),
            )
        result = self.registry.cleanup()
        self.assertEqual("quarantined", result["actions"][0]["action"])

    def test_legacy_inventory_never_adopts_files(self):
        (self.work / "legacy.csv").write_text("old", encoding="utf-8")
        report = self.registry.legacy_inventory()
        self.assertEqual(1, report["totals"]["files"])
        self.assertEqual(0, report["adopted"])
        with self.registry.connect() as con:
            self.assertEqual(0, con.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
