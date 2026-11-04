"""Tests for tools/synq/convert.py on synthetic fixtures (no client data)."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
TOOL = HERE.parent / "convert.py"
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))

import convert  # noqa: E402

SQP = FIX / "sqp-weeks.json"
SQP_CUT = FIX / "sqp-truncated.json"
ST = FIX / "search-terms.json"
INV = FIX / "inventory-history.json"
MET = FIX / "metrics-7d.json"
CAMP = FIX / "campaigns.json"
ADS_TOTAL = FIX / "ads-total.json"
ST_TOTAL = FIX / "sales-traffic-total.json"


def tmpdir() -> Path:
    return Path(tempfile.mkdtemp(prefix="synq-convert-"))


def run_cli(*args):
    return subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                          capture_output=True, text=True)


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write(path: Path, data) -> Path:
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def rows_of(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data["rows"] if isinstance(data, dict) else data


class InputTests(unittest.TestCase):
    def test_three_input_forms(self):
        d = tmpdir()
        rows = rows_of(SQP)[:2]
        plain = write(d / "plain.json", rows)
        wrapped = write(d / "wrapped.json", {"note": None, "rows": rows})
        raw = write(d / "raw.txt", "NOTE — ROW LIMIT REACHED: 2 rows returned\n\n" + json.dumps(rows))
        for p in (plain, wrapped):
            src = convert.load_source(str(p))
            self.assertEqual(len(src.rows), 2)
            self.assertFalse(src.truncated)
        src = convert.load_source(str(raw))
        self.assertEqual(len(src.rows), 2)
        self.assertTrue(src.truncated)
        self.assertIn("ROW LIMIT REACHED", src.note)

    def test_object_without_rows_exits_2(self):
        d = tmpdir()
        bad = write(d / "bad.json", {"data": []})
        proc = run_cli("sqp", "--pages", bad, "--out-dir", d / "out")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("without 'rows'", proc.stderr)

    def test_truncated_note_exits_2_and_writes_receipt_only(self):
        d = tmpdir()
        proc = run_cli("sqp", "--pages", SQP_CUT, "--out-dir", d)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["sqp-receipt.json"])
        receipt = json.loads((d / "sqp-receipt.json").read_text())
        self.assertFalse(receipt["ok"])
        self.assertTrue(receipt["inputs"][0]["truncated"])

    def test_allow_truncated_passes_with_warning(self):
        d = tmpdir()
        proc = run_cli("sqp", "--pages", SQP_CUT, "--out-dir", d, "--allow-truncated")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads((d / "sqp-receipt.json").read_text())
        self.assertTrue(receipt["ok"])
        self.assertTrue(any("NOT complete" in w for w in receipt["warnings"]))

    def test_grouped_truncated_note_also_exits_2(self):
        d = tmpdir()
        cut = write(d / "cut.json", {"note": "NOTE: TRUNCATED: showing the top 2 of 493 groups",
                                     "rows": rows_of(MET)[:2]})
        proc = run_cli("entities", "--metrics", cut, "--campaigns", CAMP, "--out", d / "e.json")
        self.assertEqual(proc.returncode, 2)

    def test_overlapping_pages_dedupe_and_conflicts_exit_2(self):
        d = tmpdir()
        proc = run_cli("sqp", "--pages", SQP, SQP, "--out-dir", d / "ok")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads((d / "ok" / "sqp-receipt.json").read_text())
        self.assertEqual(receipt["rows_deduped"], len(rows_of(SQP)))
        changed = rows_of(SQP)
        changed[0]["clicks"] += 1
        alt = write(d / "alt.json", changed)
        proc = run_cli("sqp", "--pages", SQP, alt, "--out-dir", d / "bad")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("different contents", proc.stderr)

    def test_mixed_clients_exit_2(self):
        d = tmpdir()
        other = rows_of(SQP)
        for r in other:
            r["id"] = "x-" + r["id"]
            r["client_id"] = "CTEST0002"
        alt = write(d / "other.json", other)
        proc = run_cli("sqp", "--pages", SQP, alt, "--out-dir", d / "out")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("mix client_id", proc.stderr)
        proc = run_cli("sqp", "--pages", SQP, "--out-dir", d / "out2", "--client-id", "CTEST0002")
        self.assertEqual(proc.returncode, 2)

    def test_receipt_carries_sha256_and_counts(self):
        d = tmpdir()
        proc = run_cli("totals", "--ads-total", ADS_TOTAL, "--out", d / "totals.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads((d / "totals-receipt.json").read_text())
        self.assertEqual(receipt["inputs"][0]["sha256"], hashlib.sha256(ADS_TOTAL.read_bytes()).hexdigest())
        self.assertEqual(receipt["inputs"][0]["rows"], 1)
        self.assertEqual(receipt["outputs"][0]["rows"], 1)


class SqpTests(unittest.TestCase):
    def setUp(self):
        self.d = tmpdir()
        proc = run_cli("sqp", "--pages", SQP, "--out-dir", self.d)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_one_csv_per_sunday_with_exact_columns(self):
        names = sorted(p.name for p in self.d.glob("sqp_*.csv"))
        self.assertEqual(names, ["sqp_2026-10-18.csv", "sqp_2026-10-25.csv"])
        with open(self.d / names[0], encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
        self.assertEqual(header, convert.SQP_COLUMNS)

    def test_field_mapping_and_market_columns_once_per_query(self):
        rows = read_csv(self.d / "sqp_2026-10-25.csv")
        by = {(r["asin"], r["search_query"]): r for r in rows}
        a = by[("B0TEST0001", "test widget")]
        b = by[("B0TEST0002", "test widget")]
        self.assertEqual((a["asin_click_count"], a["asin_purchase_count"], a["asin_impression_count"]),
                         ("35", "6", "2100"))
        self.assertEqual((b["asin_click_count"], b["asin_purchase_count"]), ("9", "0"))
        for col in ("total_click_count", "total_purchase_count", "search_query_volume",
                    "total_query_impression_count"):
            self.assertEqual(a[col], b[col])
        self.assertEqual((a["total_click_count"], a["search_query_volume"]), ("320", "1100"))
        self.assertEqual((a["search_query_score"], b["search_query_score"]), ("1", "4"))

    def test_asin_filter(self):
        d = tmpdir()
        run_cli("sqp", "--pages", SQP, "--out-dir", d, "--asins", "B0TEST0002")
        self.assertEqual({r["asin"] for r in read_csv(d / "sqp_2026-10-25.csv")}, {"B0TEST0002"})

    def test_non_sunday_and_non_week_exit_2(self):
        d = tmpdir()
        rows = rows_of(SQP)[:1]
        rows[0]["period_start"], rows[0]["period_end"] = "2026-10-19", "2026-10-25"
        proc = run_cli("sqp", "--pages", write(d / "mon.json", rows), "--out-dir", d / "a")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not a Sunday", proc.stderr)
        rows = rows_of(SQP)[:1]
        rows[0]["report_period"] = "MONTH"
        proc = run_cli("sqp", "--pages", write(d / "month.json", rows), "--out-dir", d / "b")
        self.assertEqual(proc.returncode, 2)

    def test_brand_level_rows_exit_2(self):
        d = tmpdir()
        rows = rows_of(SQP)[:1]
        rows[0]["asin"] = None
        proc = run_cli("sqp", "--pages", write(d / "brand.json", rows), "--out-dir", d / "a")
        self.assertEqual(proc.returncode, 2)


class SearchTermTests(unittest.TestCase):
    def setUp(self):
        self.d = tmpdir()
        proc = run_cli("search-terms", "--pages", ST, "--out-dir", self.d, "--ad-products", "SP,SB")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.receipt = json.loads((self.d / "search-terms-receipt.json").read_text())

    def test_weekly_sums(self):
        rows = read_csv(self.d / "search_terms_2026-10-25.csv")
        self.assertEqual(list(rows[0].keys()), convert.ST_CSV_COLUMNS)
        by = {r["search_term"]: r for r in rows}
        self.assertEqual(by["test widget"]["impressions"], "700")
        self.assertEqual(by["test widget"]["spend"], "28.8638")
        self.assertEqual(by["test widget"]["orders"], "7")
        self.assertEqual(by["cheap widget"]["match_type"], "PHRASE")
        self.assertNotIn("widget for desk", by)  # SD row filtered out
        self.assertEqual(self.receipt["rows_skipped_ad_product"], 1)

    def test_monitor_json_named_by_week_end(self):
        data = json.loads((self.d / "searchterms_weekly_2026-10-31.json").read_text())
        self.assertEqual(set(data[0]), {"term", "campaign", "ad group", "match type", "impressions",
                                        "clicks", "spend", "sales", "orders"})
        self.assertEqual(data[0]["term"], "test widget")  # spend desc

    def test_partial_week_flagged(self):
        weeks = self.receipt["weeks"]
        self.assertTrue(weeks["2026-10-18"]["partial"])
        self.assertFalse(weeks["2026-10-25"]["partial"])
        self.assertEqual(weeks["2026-10-25"]["days_seen"], 7)

    def test_monday_weeks(self):
        d = tmpdir()
        proc = run_cli("search-terms", "--pages", ST, "--out-dir", d, "--week-start", "monday")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((d / "search_terms_2026-10-26.csv").exists())
        self.assertTrue((d / "searchterms_weekly_2026-11-01.json").exists())


class StockTests(unittest.TestCase):
    def setUp(self):
        self.d = tmpdir()
        proc = run_cli("stock", "--history", INV, "--out-dir", self.d)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_out_of_stock_days_per_week(self):
        w1 = {r["asin"]: r["out_of_stock_days"] for r in read_csv(self.d / "stock_2026-10-18.csv")}
        w2 = {r["asin"]: r["out_of_stock_days"] for r in read_csv(self.d / "stock_2026-10-25.csv")}
        self.assertEqual(w1, {"B0TEST0001": "2", "B0TEST0002": "2"})
        # the stock-out runs across the week boundary; the missing 10-29 snapshot is not counted
        self.assertEqual(w2, {"B0TEST0001": "0", "B0TEST0002": "3"})

    def test_missing_day_recorded(self):
        receipt = json.loads((self.d / "stock-receipt.json").read_text())
        self.assertEqual(receipt["weeks"]["2026-10-25"]["B0TEST0002"]["days_observed"], 6)
        self.assertTrue(any("6 of 7 days" in w for w in receipt["warnings"]))

    def test_shared_fnsku_pool_counted_once(self):
        d = tmpdir()
        rows = [r for r in rows_of(INV) if r["snapshot_date"] == "2026-10-19" and r["asin"] == "B0TEST0001"]
        self.assertEqual(len(rows), 3)  # two SKUs on one fnsku plus one FBM SKU
        run = convert.Run("stock", convert.parse_args(["stock", "--history", "x", "--out-dir", str(d)]))
        run.args.history = [str(write(d / "day.json", rows))]
        info = convert.build_stock(run)
        # three rows, two pools: counting the shared fnsku pool per SKU row would give 3
        self.assertEqual(info["2026-10-18"]["B0TEST0001"]["max_pools_per_day"], 2)
        self.assertEqual(info["2026-10-18"]["B0TEST0001"]["out_of_stock_days"], 0)
        self.assertFalse(any("rows disagree" in w for w in run.warnings))

    def test_disagreeing_rows_of_one_pool_merge_with_a_warning(self):
        d = tmpdir()
        rows = [r for r in rows_of(INV) if r["snapshot_date"] == "2026-10-19" and r["asin"] == "B0TEST0001"]
        rows[1]["fulfillable_quantity"] = 0  # one SKU row of the shared pool disagrees
        run = convert.Run("stock", convert.parse_args(["stock", "--history", "x", "--out-dir", str(d)]))
        run.args.history = [str(write(d / "day.json", rows))]
        info = convert.build_stock(run)
        self.assertEqual(info["2026-10-18"]["B0TEST0001"]["max_pools_per_day"], 2)
        self.assertEqual(info["2026-10-18"]["B0TEST0001"]["out_of_stock_days"], 0)
        self.assertTrue(any("rows disagree" in w for w in run.warnings))

    def test_current_state_pull_exits_2(self):
        d = tmpdir()
        rows = [{k: v for k, v in rows_of(INV)[0].items() if k != "snapshot_date"}]
        proc = run_cli("stock", "--history", write(d / "cur.json", rows), "--out-dir", d / "o")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("history: true", proc.stderr)


class EntityTests(unittest.TestCase):
    def setUp(self):
        self.d = tmpdir()
        proc = run_cli("entities", "--metrics", MET, "--campaigns", CAMP, "--search-terms", ST,
                       "--out", self.d / "entities.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.rows = json.loads((self.d / "entities.json").read_text())
        self.by = {r["entity_id"]: r for r in self.rows}

    def test_row_keys_match_run_weekly_contract(self):
        want = {"entity_type", "name", "campaign_name", "campaign_id", "category", "match_type",
                "impressions", "clicks", "spend", "sales", "orders", "daily_budget",
                "budget_capped_days", "time_in_budget"}
        for r in self.rows:
            self.assertTrue(want <= set(r), set(r) ^ want)
            self.assertIsNone(r["daily_budget"])
            self.assertIsNone(r["budget_capped_days"])

    def test_placement_skipped_and_counted(self):
        self.assertNotIn("placement", {r["entity_type"] for r in self.rows})
        receipt = json.loads((self.d / "entities-receipt.json").read_text())
        self.assertEqual(receipt["rows_skipped_by_entity_type"], {"placement": 1})

    def test_names_and_match_type_join(self):
        t1 = self.by["3000000001"]
        self.assertEqual((t1["name"], t1["campaign_name"], t1["match_type"]),
                         ("test widget", "CTEST Rank Exact", "EXACT"))
        self.assertEqual(t1["spend"], 28.8638)
        t2 = self.by["3000000002"]  # no keyword_text on the metric row: name from search terms
        self.assertEqual((t2["name"], t2["match_type"]), ("widget", "PHRASE"))
        t3 = self.by["3000000003"]  # product target, no search-term match
        self.assertEqual((t3["campaign_name"], t3["match_type"]), ("CTEST Profit ASIN", None))
        t4 = self.by["3000000004"]  # campaign in neither list
        self.assertIsNone(t4["campaign_name"])
        self.assertEqual(t4["name"], "target 3000000004")
        camp = self.by["1000000001"]
        self.assertEqual((camp["entity_type"], camp["name"]), ("campaign", "CTEST Rank Exact"))

    def test_mixed_windows_exit_2(self):
        rows = rows_of(MET)
        rows[1]["timeframe"] = "14d"
        bad = write(self.d / "mixed.json", rows)
        proc = run_cli("entities", "--metrics", bad, "--campaigns", CAMP, "--out", self.d / "x.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("mix windows", proc.stderr)

    def test_daily_rows_sum_and_grouped_need_entity_type(self):
        base = rows_of(MET)[0]
        daily = []
        for i, day in enumerate(("2026-10-25", "2026-10-26")):
            r = {k: v for k, v in base.items() if k != "timeframe"}
            r.update(id=f"d-{i}", report_date=day, cost=1.5, impressions=10, orders=1)
            daily.append(r)
        p = write(self.d / "daily.json", daily)
        proc = run_cli("entities", "--metrics", p, "--campaigns", CAMP, "--out", self.d / "d.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads((self.d / "d.json").read_text())
        self.assertEqual((out[0]["spend"], out[0]["impressions"], out[0]["orders"]), (3, 20, 2))
        grouped = [{"report_date": None, "campaign_id": "1000000001", "ad_group_id": "1100000001",
                    "entity_id": "3000000001", "cost": 2, "sales": 4, "orders": 1, "units": 1,
                    "impressions": 9, "clicks": 1, "total_groups": 1}]
        g = write(self.d / "grouped.json", grouped)
        proc = run_cli("entities", "--metrics", g, "--campaigns", CAMP, "--out", self.d / "g.json")
        self.assertEqual(proc.returncode, 2)
        proc = run_cli("entities", "--metrics", g, "--campaigns", CAMP, "--entity-type", "target",
                       "--search-terms", ST, "--out", self.d / "g.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads((self.d / "g.json").read_text())
        self.assertEqual((out[0]["name"], out[0]["match_type"]), ("test widget", "EXACT"))


class TotalsTests(unittest.TestCase):
    def test_totals_shape(self):
        d = tmpdir()
        proc = run_cli("totals", "--ads-total", ADS_TOTAL, "--sales-traffic", ST_TOTAL,
                       "--out", d / "totals.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads((d / "totals.json").read_text()),
                         {"ad_spend": 123.4567, "ad_sales": 456.78, "total_sales": 1500.5})
        receipt = json.loads((d / "totals-receipt.json").read_text())
        self.assertIn("attribution window unconfirmed", receipt["sales_label"])

    def test_without_sales_traffic_total_sales_is_null(self):
        d = tmpdir()
        run_cli("totals", "--ads-total", ADS_TOTAL, "--out", d / "t.json")
        self.assertIsNone(json.loads((d / "t.json").read_text())["total_sales"])

    def test_more_than_one_row_exits_2(self):
        d = tmpdir()
        two = write(d / "two.json", rows_of(ADS_TOTAL) * 2)
        proc = run_cli("totals", "--ads-total", two, "--out", d / "t.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("exactly one row", proc.stderr)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ConsumerParseTests(unittest.TestCase):
    """The converted files load in the real consumers."""

    @classmethod
    def setUpClass(cls):
        cls.d = tmpdir()
        for args in (("sqp", "--pages", SQP, "--out-dir", cls.d),
                     ("search-terms", "--pages", ST, "--out-dir", cls.d),
                     ("stock", "--history", INV, "--out-dir", cls.d),
                     ("entities", "--metrics", MET, "--campaigns", CAMP, "--search-terms", ST,
                      "--out", cls.d / "entities.json"),
                     ("totals", "--ads-total", ADS_TOTAL, "--sales-traffic", ST_TOTAL,
                      "--out", cls.d / "totals.json")):
            proc = run_cli(*args)
            assert proc.returncode == 0, proc.stderr

    def test_supa_loaders(self):
        try:
            supa = _load_module("build_supa_workbook", REPO / "tools" / "sqp-supa" / "build_supa_workbook.py")
        except ImportError as exc:  # openpyxl missing in this interpreter
            self.skipTest(f"SUPA builder not importable: {exc}")
        weeks = ["2026-10-18", "2026-10-25"]
        cfg = {"asins": ["B0TEST0001", "B0TEST0002"], "weeks": weeks, "inputs": {
            "sqp_csvs": {w: str(self.d / f"sqp_{w}.csv") for w in weeks},
            "search_term_csvs": {w: str(self.d / f"search_terms_{w}.csv") for w in weeks},
            "stock_csvs": {w: str(self.d / f"stock_{w}.csv") for w in weeks}}}
        sqp = supa.load_sqp(cfg)
        rec = sqp[("B0TEST0001", "2026-10-25")]["test widget"]
        self.assertEqual((rec["sv"], rec["t_clk"], rec["a_clk"], rec["a_imp"]), (1100, 320, 35, 2100))
        self.assertAlmostEqual(rec["cs"], 35 / 320)
        ppc = supa.load_ppc(cfg)
        self.assertAlmostEqual(ppc["2026-10-25"]["test widget"]["spend"], 28.8638)
        stock = supa.load_stock(cfg)
        self.assertEqual(stock[("B0TEST0002", "2026-10-25")], 3)

    def test_monitor_normalize_and_cross_check(self):
        sys.path.insert(0, str(REPO / "tools" / "amazon-ads-monitor"))
        from crosscheck import cross_check
        from recommendations import normalize_entities
        ents = normalize_entities(json.loads((self.d / "entities.json").read_text()))
        self.assertEqual(len(ents), 5)
        t1 = next(e for e in ents if e.name == "test widget")
        self.assertEqual((t1.match_type, t1.orders, t1.budget_capped_days), ("EXACT", 7, 0))
        totals = json.loads((self.d / "totals.json").read_text())
        # Independent Sellerboard figures for the same synthetic day, not the SYNQ figures
        # themselves: 123.4567 vs 120.00 (+2.9%), 456.78 vs 450.00 (+1.5%), 1500.50 vs 1520.00 (-1.3%).
        sellerboard = {"ad_spend": 120.0, "ad_sales": 450.0, "total_sales": 1520.0}
        result = cross_check(sellerboard, totals)
        self.assertEqual(result.headline_verdict, "verified")
        self.assertEqual([f.verdict for f in result.figures], ["verified"] * 3)
        # Sellerboard ad spend 100.00 vs SYNQ 123.4567 is +23%, outside the 7% tolerance.
        result = cross_check(dict(sellerboard, ad_spend=100.0), totals)
        self.assertEqual(result.headline_verdict, "mismatch")
        self.assertEqual([f.figure for f in result.mismatches()], ["ad_spend"])
        self.assertAlmostEqual(result.mismatches()[0].delta_pct, 0.234567)


def _monitor_modules():
    mon = str(REPO / "tools" / "amazon-ads-monitor")
    if mon not in sys.path:
        sys.path.insert(0, mon)
    import recommendations
    import run_monitor
    import run_weekly
    return recommendations, run_weekly, run_monitor


# Grouped get_daily_metrics rows for one week (no entity_type, no id), as the weekly
# recipe pulls them: group_by campaign and group_by target over the same window.
GROUPED_CAMPAIGNS = [
    {"report_date": None, "campaign_id": "1000000001", "ad_group_id": None, "entity_id": None,
     "cost": 28.8638, "sales": 87.5, "orders": 7, "units": 7, "impressions": 700, "clicks": 30,
     "total_groups": 2},
    {"report_date": None, "campaign_id": "1000000002", "ad_group_id": None, "entity_id": None,
     "cost": 11.25, "sales": 9.99, "orders": 1, "units": 1, "impressions": 260, "clicks": 9,
     "total_groups": 2},
]
GROUPED_TARGETS = [
    {"report_date": None, "campaign_id": "1000000001", "ad_group_id": "1100000001",
     "entity_id": "3000000001", "cost": 20.0, "sales": 60.0, "orders": 5, "units": 5,
     "impressions": 500, "clicks": 20, "total_groups": 3},
    {"report_date": None, "campaign_id": "1000000001", "ad_group_id": "1100000001",
     "entity_id": "3000000005", "cost": 8.8638, "sales": 27.5, "orders": 2, "units": 2,
     "impressions": 200, "clicks": 10, "total_groups": 3},
    {"report_date": None, "campaign_id": "1000000002", "ad_group_id": "1100000002",
     "entity_id": "3000000002", "cost": 11.25, "sales": 9.99, "orders": 1, "units": 1,
     "impressions": 260, "clicks": 9, "total_groups": 3},
]


class CampaignTotalTests(unittest.TestCase):
    """Campaign rows and target rows in one entities file: a campaign's spend counts once."""

    def test_mixed_grain_file_counts_campaign_spend_once(self):
        recommendations, run_weekly, _ = _monitor_modules()
        d = tmpdir()
        proc = run_cli("entities", "--metrics", MET, "--campaigns", CAMP, "--search-terms", ST,
                       "--out", d / "entities.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        raw, notes = run_weekly.load_ads_entities(str(d / "entities.json"))
        self.assertEqual(notes, [])
        self.assertEqual({r["entity_type"] for r in raw}, {"campaign", "target"})
        for order in (raw, list(reversed(raw))):
            totals = recommendations._campaign_totals(recommendations.normalize_entities(order))
            self.assertAlmostEqual(totals["1000000001"]["spend"], 28.8638)  # not 57.7276
            self.assertEqual(totals["1000000001"]["impressions"], 700)
            self.assertAlmostEqual(totals["1000000002"]["spend"], 11.25)  # target rows only

    def test_weekly_recipe_campaign_and_target_files(self):
        recommendations, run_weekly, _ = _monitor_modules()
        d = tmpdir()
        camp = write(d / "CAMPAIGNS_WEEK.json", {"note": None, "rows": GROUPED_CAMPAIGNS})
        tgt = write(d / "TARGETS_WEEK.json", {"note": None, "rows": GROUPED_TARGETS})
        out = d / "ENTITIES.json"
        proc = run_cli("entities", "--metrics", f"campaign:{camp}", f"target:{tgt}",
                       "--campaigns", CAMP, "--search-terms", ST, "--out", out)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads((d / "ENTITIES-receipt.json").read_text())
        self.assertEqual(receipt["entities_by_type"], {"campaign": 2, "target": 3})
        self.assertEqual(receipt["window"], "get_daily_metrics")
        self.assertEqual([i.get("grain") for i in receipt["inputs"] if i["role"] == "metrics"],
                         ["campaign", "target"])
        rows = json.loads(out.read_text())
        self.assertIsInstance(rows, list)
        by = {(r["entity_type"], r["entity_id"]): r for r in rows}
        self.assertEqual(by[("campaign", "1000000001")]["name"], "CTEST Rank Exact")
        self.assertEqual(by[("target", "3000000001")]["match_type"], "EXACT")
        raw, _ = run_weekly.load_ads_entities(str(out))
        totals = recommendations._campaign_totals(recommendations.normalize_entities(raw))
        self.assertAlmostEqual(totals["1000000001"]["spend"], 28.8638)
        self.assertAlmostEqual(totals["1000000002"]["spend"], 11.25)

    def test_unprefixed_file_falls_back_to_entity_type(self):
        d = tmpdir()
        camp = write(d / "c.json", GROUPED_CAMPAIGNS)
        tgt = write(d / "t.json", GROUPED_TARGETS)
        proc = run_cli("entities", "--metrics", f"campaign:{camp}", tgt, "--entity-type", "target",
                       "--campaigns", CAMP, "--out", d / "e.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        types = Counter_of(json.loads((d / "e.json").read_text()))
        self.assertEqual(types, {"campaign": 2, "target": 3})
        proc = run_cli("entities", "--metrics", f"campaign:{camp}", tgt, "--campaigns", CAMP,
                       "--out", d / "e2.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no entity_type", proc.stderr)

    def test_split_grain(self):
        self.assertEqual(convert.split_grain("campaign:a.json"), ("campaign", "a.json"))
        self.assertEqual(convert.split_grain("ad_group:dir/a.json"), ("ad_group", "dir/a.json"))
        self.assertEqual(convert.split_grain("placement:a.json"), (None, "placement:a.json"))
        self.assertEqual(convert.split_grain("C:/data/a.json"), (None, "C:/data/a.json"))
        self.assertEqual(convert.split_grain("a.json"), (None, "a.json"))

    def test_prefix_disagreeing_with_row_entity_type_exits_2(self):
        d = tmpdir()
        proc = run_cli("entities", "--metrics", f"campaign:{MET}", "--campaigns", CAMP,
                       "--out", d / "e.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("prefix campaign", proc.stderr)

    def test_genuinely_mixed_windows_still_exit_2(self):
        d = tmpdir()
        tgt = write(d / "t.json", GROUPED_TARGETS)
        # get_metrics 7d rows plus get_daily_metrics rows
        proc = run_cli("entities", "--metrics", MET, f"target:{tgt}", "--campaigns", CAMP,
                       "--out", d / "a.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("mix windows", proc.stderr)
        # one grain as raw daily rows and as grouped rows
        raw = [dict(GROUPED_TARGETS[0], id="d-1", entity_type="target", report_date="2026-10-25")]
        raw[0].pop("total_groups")
        rawp = write(d / "raw.json", raw)
        proc = run_cli("entities", "--metrics", rawp, f"target:{tgt}", "--campaigns", CAMP,
                       "--out", d / "b.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("raw daily rows and as grouped rows", proc.stderr)
        # the same grouped file twice
        proc = run_cli("entities", "--metrics", f"target:{tgt}", f"target:{tgt}", "--campaigns", CAMP,
                       "--out", d / "c.json")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("same file", proc.stderr)


def Counter_of(rows):
    out = {}
    for r in rows:
        out[r["entity_type"]] = out.get(r["entity_type"], 0) + 1
    return out


CUT_NOTE = "NOTE: ROW LIMIT REACHED: 2 rows returned = the requested limit (2)"


class PartialOutputTests(unittest.TestCase):
    """--allow-truncated output says it is partial, and the monitor surfaces the note."""

    def test_entities_wrapper_note_reaches_run_weekly(self):
        _, run_weekly, _ = _monitor_modules()
        d = tmpdir()
        cut = write(d / "cut.json", {"note": CUT_NOTE, "rows": rows_of(MET)[:2]})
        out = d / "e.json"
        proc = run_cli("entities", "--metrics", cut, "--campaigns", CAMP, "--out", out,
                       "--allow-truncated")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(out.read_text())
        self.assertEqual(set(data), {"note", "rows"})
        self.assertTrue(data["note"].startswith("PARTIAL"))
        self.assertIn("ROW LIMIT REACHED", data["note"])
        self.assertEqual(len(data["rows"]), 2)
        receipt = json.loads((d / "e-receipt.json").read_text())
        self.assertTrue(receipt["truncated"])
        rows, notes = run_weekly.load_ads_entities(str(out))
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(notes), 1)
        self.assertIn("PARTIAL", notes[0])

    def test_totals_wrapper_note_reaches_run_monitor(self):
        _, _, run_monitor = _monitor_modules()
        d = tmpdir()
        cut = write(d / "ads.json", {"note": CUT_NOTE, "rows": rows_of(ADS_TOTAL)})
        out = d / "t.json"
        proc = run_cli("totals", "--ads-total", cut, "--out", out, "--allow-truncated")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(out.read_text())
        self.assertEqual(data["rows"], [{"ad_spend": 123.4567, "ad_sales": 456.78, "total_sales": None}])
        self.assertTrue(data["note"].startswith("PARTIAL"))
        figures, notes = run_monitor.load_ads_figures(str(out))
        self.assertEqual(figures["ad_spend"], 123.4567)
        self.assertEqual(len(notes), 1)
        self.assertIn("PARTIAL", notes[0])
        # a complete run stays the plain object
        proc = run_cli("totals", "--ads-total", ADS_TOTAL, "--out", d / "plain.json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        figures, notes = run_monitor.load_ads_figures(str(d / "plain.json"))
        self.assertEqual((figures["ad_spend"], notes), (123.4567, []))

    def test_search_terms_partial_json_and_csv_receipt(self):
        d = tmpdir()
        cut = write(d / "st.json", {"note": CUT_NOTE, "rows": rows_of(ST)})
        proc = run_cli("search-terms", "--pages", cut, "--out-dir", d / "o", "--allow-truncated")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads((d / "o" / "searchterms_weekly_2026-10-31.json").read_text())
        self.assertTrue(data["note"].startswith("PARTIAL"))
        self.assertTrue(data["rows"])
        receipt = json.loads((d / "o" / "search-terms-receipt.json").read_text())
        self.assertTrue(receipt["truncated"])
        csvs = [o for o in receipt["outputs"] if o["path"].endswith(".csv")]
        self.assertTrue(csvs and all(o["truncated"] for o in csvs))
        for o in csvs:
            self.assertIn(f"WARNING: {o['path']} was written from truncated input", proc.stderr)

    def test_complete_run_writes_plain_outputs(self):
        d = tmpdir()
        proc = run_cli("search-terms", "--pages", ST, "--out-dir", d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIsInstance(json.loads((d / "searchterms_weekly_2026-10-31.json").read_text()), list)
        receipt = json.loads((d / "search-terms-receipt.json").read_text())
        self.assertFalse(receipt["truncated"])
        self.assertNotIn("truncated input", proc.stderr)


class BareListCapTests(unittest.TestCase):
    """A bare list at a row cap has no note to say it was cut."""

    def _rows(self, n):
        base = rows_of(ST)[0]
        return [dict(base, id=f"st-cap-{i:04d}", search_term=f"term {i}") for i in range(n)]

    def test_bare_list_at_each_cap_exits_2(self):
        d = tmpdir()
        for n in convert.CAP_SIZES:
            p = write(d / f"bare{n}.json", self._rows(n))
            proc = run_cli("search-terms", "--pages", p, "--out-dir", d / f"o{n}")
            self.assertEqual(proc.returncode, 2, n)
            self.assertIn(f"exactly a row-cap count of rows ({p}: {n})", proc.stderr)
            self.assertIn("note wrapper", proc.stderr)
            self.assertIn("raise limit", proc.stderr)
            self.assertEqual([x.name for x in (d / f"o{n}").iterdir()], ["search-terms-receipt.json"])

    def test_off_cap_bare_list_and_wrapped_cap_list_pass(self):
        d = tmpdir()
        proc = run_cli("search-terms", "--pages", write(d / "b49.json", self._rows(49)), "--out-dir", d / "a")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        wrapped = write(d / "w50.json", {"note": None, "rows": self._rows(50)})
        proc = run_cli("search-terms", "--pages", wrapped, "--out-dir", d / "b")
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_bare_cap_list_with_allow_truncated_is_marked_partial(self):
        d = tmpdir()
        p = write(d / "bare50.json", self._rows(50))
        proc = run_cli("search-terms", "--pages", p, "--out-dir", d / "o", "--allow-truncated")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        receipt = json.loads((d / "o" / "search-terms-receipt.json").read_text())
        self.assertTrue(receipt["truncated"])
        self.assertTrue(receipt["inputs"][0]["bare_at_cap"])
        data = json.loads((d / "o" / "searchterms_weekly_2026-10-31.json").read_text())
        self.assertIn("bare list of exactly 50 rows", data["note"])


if __name__ == "__main__":
    unittest.main()
