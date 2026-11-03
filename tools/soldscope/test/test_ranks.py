"""Tests for tools/soldscope/ranks.py on synthetic fixtures (no client data)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
TOOL = HERE.parent / "ranks.py"
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

import ranks  # noqa: E402

ORG = str(FIX / "heatmap-organic-page-001.json")
SPO = str(FIX / "heatmap-sponsored-page-001.json")
HIST = str(FIX / "history-organic.json")


def run_cli(*args):
    out = Path(tempfile.mkdtemp(prefix="soldscope-rank-")) / "out.json"
    proc = subprocess.run([sys.executable, str(TOOL), *args, "--out", str(out)],
                          capture_output=True, text=True)
    data = json.loads(out.read_text()) if out.exists() else None
    return proc, data, out


def by_kw(series):
    return {s["keyword"]: s for s in series}


def day(series_row, d):
    return next(r for r in series_row["ranks"] if r["date"] == d)


class HeatmapTest(unittest.TestCase):
    def test_organic_series(self):
        proc, data, _ = run_cli("--organic", ORG, "--marketplace", "US")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        s = by_kw(data)
        self.assertEqual(list(s), ["widget cleaner", "widget spray"])
        wc = s["widget cleaner"]
        self.assertEqual(wc["searchVolume"], 1000)
        self.assertEqual(wc["ranks"][0], {"date": "2026-10-04", "organicRank": 5, "sponsoredRank": None})
        self.assertEqual(len(wc["ranks"]), 21)        # 2026-10-03 predates the group and is clipped
        self.assertEqual(day(s["widget spray"], "2026-10-06")["organicRank"], 101)   # rank 0

    def test_keep_before_group(self):
        proc, data, _ = run_cli("--organic", ORG, "--keep-before-group")
        self.assertEqual(by_kw(data)["widget cleaner"]["ranks"][0]["date"], "2026-10-03")

    def test_sponsored_merges_into_the_same_rows(self):
        proc, data, _ = run_cli("--organic", ORG, "--sponsored", SPO)
        wc = by_kw(data)["widget cleaner"]
        self.assertEqual(day(wc, "2026-10-23"), {"date": "2026-10-23", "organicRank": 1, "sponsoredRank": 45})
        self.assertEqual(day(wc, "2026-10-24")["sponsoredRank"], 19)
        self.assertEqual(day(wc, "2026-10-10")["sponsoredRank"], 101)

    def test_sponsored_only_leaves_organic_null(self):
        proc, data, _ = run_cli("--sponsored", SPO)
        wc = by_kw(data)["widget cleaner"]
        self.assertIsNone(wc["ranks"][0]["organicRank"])

    def test_date_window(self):
        proc, data, _ = run_cli("--organic", ORG, "--date-from", "2026-10-18", "--date-to", "2026-10-20")
        self.assertEqual([r["date"] for r in by_kw(data)["widget cleaner"]["ranks"]],
                         ["2026-10-18", "2026-10-19", "2026-10-20"])

    def test_marketplace_mismatch_fails(self):
        proc, data, out = run_cli("--organic", ORG, "--marketplace", "DE")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("marketplace", proc.stderr)
        self.assertFalse(out.exists())

    def test_incomplete_read_fails(self):
        tmp = Path(tempfile.mkdtemp()) / "p.json"
        page = json.loads(Path(ORG).read_text())
        page["meta"]["total"] = 3
        tmp.write_text(json.dumps(page))
        proc, _, _ = run_cli("--organic", str(tmp))
        self.assertEqual(proc.returncode, 2)
        proc, _, _ = run_cli("--organic", str(tmp), "--allow-partial")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_mixed_groups_fail(self):
        tmp = Path(tempfile.mkdtemp()) / "p.json"
        page = json.loads(Path(ORG).read_text())
        page["group"]["id"] = 9002
        tmp.write_text(json.dumps(page))
        proc, _, _ = run_cli("--organic", ORG, "--sponsored", str(tmp))
        self.assertEqual(proc.returncode, 2)


class HistoryTest(unittest.TestCase):
    def test_daily_upper_median_utc(self):
        proc, data, _ = run_cli("--history", f"widget cleaner={HIST}", "--product-id", "501")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        wc = by_kw(data)["widget cleaner"]
        self.assertIsNone(wc["searchVolume"])
        self.assertEqual([(r["date"], r["organicRank"]) for r in wc["ranks"]],
                         [("2026-10-20", 6), ("2026-10-21", 5), ("2026-10-22", 101)])

    def test_product_picked_by_asin(self):
        proc, data, _ = run_cli("--history", f"widget cleaner={HIST}", "--asin", "B0TEST0002")
        self.assertEqual(by_kw(data)["widget cleaner"]["ranks"], [
            {"date": "2026-10-20", "organicRank": 9, "sponsoredRank": None}])

    def test_ambiguous_product_fails(self):
        proc, _, _ = run_cli("--history", f"widget cleaner={HIST}")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--product-id", proc.stderr)

    def test_unknown_asin_with_one_product_warns(self):
        hist = json.loads(Path(HIST).read_text())
        data = hist.get("data", hist)
        only = sorted(data["history"])[0]
        data["history"] = {only: data["history"][only]}
        tmp = Path(tempfile.mkdtemp()) / "one-product.json"
        tmp.write_text(json.dumps(hist))
        proc, out, _ = run_cli("--history", f"widget cleaner={tmp}", "--asin", "B0TEST9999")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("not in the history snapshots", proc.stderr)
        self.assertIn("widget cleaner", by_kw(out))

    def test_history_takes_heatmap_search_volume(self):
        proc, data, _ = run_cli("--organic", ORG, "--history-sponsored", f"widget cleaner={HIST}",
                                "--product-id", "501")
        wc = by_kw(data)["widget cleaner"]
        self.assertEqual(wc["searchVolume"], 1000)
        self.assertEqual(day(wc, "2026-10-20")["sponsoredRank"], 6)


class ExportTest(unittest.TestCase):
    def test_provisional_export_rows(self):
        proc, data, _ = run_cli("--export", str(FIX / "export-desktop.json"), "--asin", "B0TEST0001")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        s = by_kw(data)
        self.assertEqual(s["widget cleaner"]["ranks"], [
            {"date": "2026-10-20", "organicRank": 4, "sponsoredRank": None}])   # upper median of 2, 4
        self.assertEqual(s["widget cleaner"]["searchVolume"], 1000)
        self.assertEqual(s["widget spray"]["ranks"][0]["organicRank"], 101)


class FoldTest(unittest.TestCase):
    def test_fold_rank(self):
        for raw, want in ((0, 101), (None, 101), ("7", 101), (150, 101), (101, 101), (1, 1), (100, 100),
                          (True, 101)):
            self.assertEqual(ranks.fold_rank(raw), want, raw)

    def test_week_start_is_sunday(self):
        self.assertEqual(ranks.week_start("2026-10-24").isoformat(), "2026-10-18")   # Saturday
        self.assertEqual(ranks.week_start("2026-10-18").isoformat(), "2026-10-18")   # Sunday
        self.assertEqual(ranks.week_start("2026-10-19").isoformat(), "2026-10-18")   # Monday


class WeeklyRowsTest(unittest.TestCase):
    def test_weekly_rows(self):
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        r = {x["keyword"]: x for x in rows}
        self.assertEqual({k: r["widget cleaner"][k] for k in ("rank_now", "rank_prev", "weeks_stable")},
                         {"rank_now": 1, "rank_prev": 2, "weeks_stable": 3})
        self.assertEqual({k: r["widget spray"][k] for k in ("rank_now", "rank_prev", "weeks_stable")},
                         {"rank_now": 101, "rank_prev": 14, "weeks_stable": 0})
        self.assertEqual(r["widget cleaner"]["week_start"], "2026-10-18")

    def test_graduate_rank_max(self):
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows", "--graduate-rank-max", "1")
        self.assertEqual({x["keyword"]: x["weeks_stable"] for x in rows}["widget cleaner"], 1)

    def test_partial_trailing_week_is_dropped(self):
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows", "--date-to", "2026-10-21")
        wc = {x["keyword"]: x for x in rows}["widget cleaner"]
        self.assertEqual((wc["week_start"], wc["rank_now"], wc["rank_prev"]), ("2026-10-11", 2, 3))
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows", "--date-to", "2026-10-21",
                                "--include-partial-week")
        self.assertEqual({x["keyword"]: x for x in rows}["widget cleaner"]["week_start"], "2026-10-18")

    def test_weekly_rows_need_organic(self):
        proc, _, _ = run_cli("--sponsored", SPO, "--weekly-rows")
        self.assertEqual(proc.returncode, 2)

    def test_agrees_with_supa_load_rank(self):
        path = REPO / "tools" / "sqp-supa" / "build_supa_workbook.py"
        try:
            spec = importlib.util.spec_from_file_location("build_supa_workbook_under_test", path)
            supa = importlib.util.module_from_spec(spec)
            with contextlib.redirect_stdout(io.StringIO()):
                spec.loader.exec_module(supa)
        except Exception as exc:  # openpyxl or repo helpers missing in this interpreter
            self.skipTest(f"cannot import SUPA builder: {exc}")
        proc, series, series_path = run_cli("--organic", ORG)
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows")
        weeks = ["2026-10-04", "2026-10-11", "2026-10-18"]
        cfg = {"weeks": weeks, "inputs": {"rank_jsons": {"B0TEST0001": str(series_path)}}}
        loaded = supa.load_rank(cfg)
        for row in rows:
            per_week = loaded[("B0TEST0001", row["keyword"].lower())]
            self.assertEqual(row["rank_now"], per_week["2026-10-18"], row["keyword"])
            self.assertEqual(row["rank_prev"], per_week["2026-10-11"], row["keyword"])

    def test_feeds_ads_monitor_normalizer(self):
        path = REPO / "tools" / "amazon-ads-monitor" / "recommendations.py"
        try:
            sys.path.insert(0, str(path.parent))
            spec = importlib.util.spec_from_file_location("recommendations_under_test", path)
            rec = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = rec          # dataclasses look the module up by name
            spec.loader.exec_module(rec)
        except Exception as exc:
            self.skipTest(f"cannot import ads-monitor recommendations: {exc}")
        finally:
            sys.path.remove(str(path.parent))
        proc, rows, _ = run_cli("--organic", ORG, "--weekly-rows")
        norm = getattr(rec, "normalize_rank_rows", None) or rec.normalize_rank_radar
        got = norm(rows)
        self.assertEqual(got["widget cleaner"], {"keyword": "widget cleaner", "rank_now": 1, "rank_prev": 2,
                                                 "weeks_stable": 3})


if __name__ == "__main__":
    unittest.main()
