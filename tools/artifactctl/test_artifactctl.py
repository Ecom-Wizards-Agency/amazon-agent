import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifactctl import ArtifactRegistry, sha


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
