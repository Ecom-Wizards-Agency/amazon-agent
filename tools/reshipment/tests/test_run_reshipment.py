import datetime
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_reshipment


class BrowserTaskIdTests(unittest.TestCase):
    def test_task_ids_are_stable_per_profile_and_operation_across_runs(self):
        account = {"key": "test", "profile_key": "test-us", "brand": "Test",
                   "market": "US", "country": "US"}
        asins = [f"B{i:09d}" for i in range(121)]
        run_times = [datetime.datetime(2026, 9, 14, 10, 11, 12, 123456).astimezone(),
                     datetime.datetime(2026, 9, 15, 13, 14, 15, 654321).astimezone()]
        task_ids_by_run = []
        with tempfile.TemporaryDirectory() as tmp:
            work_dir = Path(tmp)
            config_path = work_dir / "config.json"
            for profile_key, now in [("test-us", run_times[0]),
                                     ("test-us", run_times[1]),
                                     ("other-us", run_times[1])]:
                account["profile_key"] = profile_key
                config_path.write_text(json.dumps({"inventory_questions": {"profiles": {
                    profile_key: {"account_name": "Test", "marketplace": "US"}
                }}}), encoding="utf-8")
                run_date = now.date().isoformat()
                run_stamp = now.strftime("%H%M%S%f")
                task_ids = []

                def fake_run(cmd, **kwargs):
                    task_ids.append(cmd[cmd.index("--task-id") + 1])
                    payload = {"status": "complete"}
                    if "--all-skus" in cmd:
                        payload.update(account="Test", marketplace="US",
                                       checked_at=now.isoformat(), fba={"skus": []})
                    elif "--search-terms" in cmd:
                        terms = cmd[cmd.index("--search-terms") + 1].split(",")
                        payload["searches"] = [
                            {"term": asin, "rows": [{"asin": asin, "seller_sku": asin,
                                                     "fba_offer": True}]}
                            for asin in terms
                        ]
                    else:
                        out = Path(cmd[cmd.index("--out") + 1])
                        self.assertEqual(out.parent.name, run_date)
                        self.assertIn(run_stamp, out.name)
                        out.write_text("Child ASIN,Units Ordered\n" + "".join(
                            f"{asin},1\n" for asin in asins), encoding="utf-8")
                    return subprocess.CompletedProcess(cmd, 0, json.dumps(payload), "")

                with patch.object(run_reshipment, "run", side_effect=fake_run), \
                        patch.object(run_reshipment, "provider_script", return_value=Path("provider.mjs")), \
                        patch.object(run_reshipment.datetime, "datetime", wraps=datetime.datetime) as clock:
                    clock.now.return_value = now
                    entry = run_reshipment.pull_account(
                        account, {"marketplace": "us"}, run_date, {}, config_path,
                        work_dir, reconcile_shipments=False)

                self.assertIsNone(entry["blocker"])
                self.assertEqual(entry["business_kept"], len(asins))
                self.assertEqual(task_ids, [f"reshipment:{profile_key}:{operation}" for operation in
                                           ("inventory", "demand", "search-0", "search-40",
                                            "search-80", "search-120", "recent-demand")])
                for task_id in task_ids:
                    self.assertNotIn(run_date, task_id)
                    self.assertNotIn(run_stamp, task_id)
                for field in ("fba", "business", "business_7d"):
                    evidence = Path(entry[field])
                    self.assertTrue(evidence.exists())
                    self.assertEqual(evidence.parent.name, run_date)
                    self.assertIn(run_stamp, evidence.name)
                task_ids_by_run.append(task_ids)

        self.assertEqual(task_ids_by_run[0], task_ids_by_run[1])
        self.assertTrue(set(task_ids_by_run[0]).isdisjoint(task_ids_by_run[2]))


class SlackThreadReuseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        repo = patch.object(run_reshipment, "REPO", self.root)
        repo.start()
        self.addCleanup(repo.stop)
        helper = patch.object(run_reshipment.slack_helper, "run_helper", side_effect=self.helper)
        self.send = helper.start()
        self.addCleanup(helper.stop)
        self.manifest = self.make_manifest("first")
        self.date = "2026-09-15"

    def helper(self, *args):
        if args[0] == "permalink":
            return json.dumps({"permalink": "https://slack.example/" + args[2]})
        return json.dumps({"ok": True, "ts": str(self.send.call_count)})

    def make_manifest(self, directory):
        directory = self.root / directory
        directory.mkdir()
        slack = directory / "plan_slack.txt"
        slack.write_text("Source: checked now\n\n*Reshipment*\nSend 10 units of A\n", encoding="utf-8")
        csv_path = directory / "plan.csv"
        csv_path.write_text("ASIN,Reshipment Units\nA,10\nB,0\n", encoding="utf-8")
        return {"account": "test-us", "sendUnits": 10, "effectiveCoverageDays": 60,
                "excessUnits": 0, "actionable": True, "csv": str(csv_path),
                "xlsx": str(directory / "plan.xlsx"), "slack": str(slack),
                "sources": [str(directory / "source.csv")], "notes": "Inventory checked now",
                "_entry": {"brand": "Test", "market": "US", "checked_at": "now"},
                "_slack": slack}

    def post(self, manifests=None, blocked=None, region="US", date=None):
        return run_reshipment.post(region, manifests or [self.manifest], blocked or [], date or self.date)

    def parents(self):
        return [call.args for call in self.send.call_args_list
                if call.args[0] == "post" and len(call.args) == 3]

    def ledger(self):
        return json.loads(next((self.root / "output/reshipment-slack-receipts").glob("*.json")).read_text())

    def test_unchanged_rerun_reuses_parent_and_keeps_all_receipts(self):
        link = self.post()
        ledger = self.ledger()
        self.send.reset_mock()
        self.assertEqual(self.post(), link)
        self.send.assert_not_called()
        self.assertEqual(self.ledger(), ledger)
        self.assertEqual(ledger[0]["parent"]["ts"], "1")
        self.assertEqual(len(ledger[0]["replies"]), 1)

    def test_fresh_paths_timestamps_and_csv_row_order_do_not_change_plan(self):
        link = self.post()
        fresh = self.make_manifest("second")
        fresh["notes"] = "Inventory checked later"
        fresh["_entry"]["checked_at"] = "later"
        fresh["_slack"].write_text("Source: checked later\n\n*Reshipment*\nSend 10 units of A\n", encoding="utf-8")
        Path(fresh["csv"]).write_text("ASIN,Reshipment Units\nB,0\nA,10\n", encoding="utf-8")
        self.assertEqual(self.post([fresh]), link)
        self.assertEqual(len(self.parents()), 1)

    def test_changed_manifest_posts_new_parent_and_preserves_history(self):
        first = self.post()
        self.manifest["effectiveCoverageDays"] = 90
        second = self.post()
        self.assertNotEqual(first, second)
        self.assertEqual(len(self.parents()), 2)
        self.assertEqual(len(self.ledger()), 2)
        self.assertEqual(self.ledger()[0]["permalink"], first)
        self.assertEqual(self.post(), second)
        self.assertEqual(len(self.parents()), 2)

    def test_product_reallocation_beyond_slack_preview_changes_plan(self):
        first = self.post()
        Path(self.manifest["csv"]).write_text("ASIN,Reshipment Units\nA,0\nB,10\n", encoding="utf-8")
        self.assertNotEqual(self.post(), first)
        self.assertEqual(len(self.parents()), 2)

    def test_quiet_plan_and_changed_blockers_are_compared(self):
        self.manifest["sendUnits"] = 0
        blocked = [{"brand": "Blocked", "market": "US", "blocker": "Report missing"}]
        first = self.post(blocked=blocked)
        self.assertEqual(self.post(blocked=blocked), first)
        blocked[0]["blocker"] = "Login unavailable"
        self.assertNotEqual(self.post(blocked=blocked), first)
        self.manifest["excessUnits"] = 20
        self.post(blocked=blocked)
        self.assertEqual(len(self.parents()), 3)

    def test_day_region_and_channel_have_separate_threads(self):
        links = {self.post(), self.post(date="2026-09-16"), self.post(region="EU")}
        with patch.object(run_reshipment, "CHANNEL", "other-channel"):
            links.add(self.post())
        self.assertEqual(len(links), 4)
        self.assertEqual(len(self.parents()), 4)

    def test_account_order_does_not_change_plan(self):
        second = copy.deepcopy(self.manifest)
        second["account"] = "other-us"
        second["_entry"]["brand"] = "Other"
        link = self.post([self.manifest, second])
        self.assertEqual(self.post([second, self.manifest]), link)
        self.assertEqual(len(self.parents()), 1)

    def test_failed_reply_retries_same_parent_without_repeating_confirmed_reply(self):
        blocked = [{"brand": "Blocked", "market": "US", "blocker": "Report missing"}]

        def fail_last_reply(*args):
            if args[0] == "post" and args[2].startswith("*Not planned"):
                raise subprocess.CalledProcessError(3, "guarded helper")
            return self.helper(*args)

        self.send.side_effect = fail_last_reply
        with self.assertRaises(subprocess.CalledProcessError):
            self.post(blocked=blocked)
        self.assertEqual(len(self.ledger()[0]["replies"]), 1)
        self.send.side_effect = self.helper
        self.send.reset_mock()
        self.post(blocked=blocked)
        self.assertEqual(self.parents(), [])
        self.assertEqual(self.send.call_count, 2)
        self.assertEqual(len(self.ledger()[0]["replies"]), 2)

    def test_failed_parent_does_not_record_success_or_bypass_guard(self):
        self.send.side_effect = subprocess.CalledProcessError(3, "guarded helper")
        with self.assertRaises(subprocess.CalledProcessError):
            self.post()
        self.assertEqual(list((self.root / "output/reshipment-slack-receipts").glob("*.json")), [])
        self.send.assert_called_once()

    def test_failed_permalink_retries_lookup_without_posting(self):
        def fail_permalink(*args):
            if args[0] == "permalink":
                raise subprocess.CalledProcessError(1, "guarded helper")
            return self.helper(*args)

        self.send.side_effect = fail_permalink
        with self.assertRaises(subprocess.CalledProcessError):
            self.post()
        self.send.side_effect = self.helper
        self.send.reset_mock()
        self.post()
        self.send.assert_called_once_with("permalink", run_reshipment.CHANNEL, "1")


if __name__ == "__main__":
    unittest.main()
