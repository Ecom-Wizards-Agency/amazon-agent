import datetime
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


if __name__ == "__main__":
    unittest.main()
