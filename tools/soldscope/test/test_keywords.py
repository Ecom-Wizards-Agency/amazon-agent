"""Tests for tools/soldscope/keywords.py on synthetic fixtures (no client data)."""
from __future__ import annotations

import contextlib
import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
TOOL = HERE.parent / "keywords.py"
sys.path.insert(0, str(HERE.parent))

import keywords as kw  # noqa: E402

A = ["B0TEST0001", "B0TEST0002", "B0TEST0003", "B0TEST0004"]
PAGES = [str(FIX / "multi-page-001.json"), str(FIX / "multi-page-002.json")]


def run_cli(*args):
    out = tempfile.mkdtemp(prefix="soldscope-kw-")
    proc = subprocess.run([sys.executable, str(TOOL), *args, "--out-dir", out],
                          capture_output=True, text=True)
    return proc, Path(out)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def receipt(out):
    return json.loads((out / "keywords-receipt.json").read_text())


class CsvShapeTest(unittest.TestCase):
    def test_headers_and_asin_order(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native", "--marketplace", "US")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("core.csv", "expanded.csv"):
            self.assertEqual(read_csv(out / name)[0],
                             ["", "Search Terms", "SV", "Relev.", "Sugg. bid & range", *A])
        self.assertEqual(read_csv(out / "roots.csv")[0],
                         ["", "Normalized Root", "Frequency", "Broad Search Volume", ""])
        self.assertEqual(read_csv(out / "competitors.csv")[0],
                         ["asin", "brand", "seller country", "variations", "rating", "review count",
                          "price", "30d sales", "30d revenue", "fulfillment", "category"])
        for name in ("roots.csv", "core.csv", "expanded.csv", "competitors.csv", "research.json",
                     "keywords-receipt.json"):
            self.assertTrue((out / name).exists(), name)

    def test_anchor_goes_first(self):
        proc, out = run_cli("--pages", *PAGES, "--anchor", "B0TEST0003")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(read_csv(out / "core.csv")[0][5:],
                         ["B0TEST0003", "B0TEST0001", "B0TEST0002", "B0TEST0004"])
        research = json.loads((out / "research.json").read_text())
        self.assertEqual(research["anchor"], "B0TEST0003")
        self.assertEqual([c["asin"] for c in research["competitors"] if c["isAnchor"]], ["B0TEST0003"])

    def test_bid_column_and_sort(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native")
        rows = read_csv(out / "expanded.csv")[1:]
        self.assertEqual([r[1] for r in rows],
                         ["widget", "widget cleaner", "widget cleaner's kit", "widget cleaner spray"])
        self.assertEqual(rows[1][4], "1.25 (0.90-1.60)")


class RelevancyTest(unittest.TestCase):
    def test_native_is_divided_by_100(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native")
        rel = {r[1]: float(r[3]) for r in read_csv(out / "expanded.csv")[1:]}
        self.assertEqual(rel, {"widget": 1.0, "widget cleaner": 0.75, "widget cleaner's kit": 0.5,
                               "widget cleaner spray": 0.25})
        self.assertEqual(receipt(out)["relevancy"]["choice"], "native")

    def test_computed_is_top_n_share(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "computed")
        rel = {r[1]: float(r[3]) for r in read_csv(out / "expanded.csv")[1:]}
        self.assertEqual(rel["widget cleaner"], 0.75)       # ranks 3, 10, 40 of 4 ASINs
        self.assertEqual(rel["widget cleaner's kit"], 0.25)  # 60 is outside the top 50
        self.assertEqual([r[1] for r in read_csv(out / "core.csv")[1:]], ["widget cleaner"])

    def test_auto_falls_back_when_core_sets_disagree(self):
        proc, out = run_cli("--pages", *PAGES)
        r = receipt(out)["relevancy"]
        self.assertEqual(r["choice"], "computed")
        self.assertLess(r["agreement"]["core_membership_jaccard"], 0.9)

    def test_auto_keeps_native_when_it_tracks_computed(self):
        tmp = Path(tempfile.mkdtemp())
        pages = []
        for p in PAGES:
            page = json.loads(Path(p).read_text())
            for row in page["data"]["keywords"]:
                ranks = [(row["asinsPositions"].get(a) or {}).get("organicRank") for a in A]
                row["relevancy"] = 100 * sum(1 for x in ranks if x and x <= 50) / 4
            q = tmp / Path(p).name
            q.write_text(json.dumps(page))
            pages.append(str(q))
        proc, out = run_cli("--pages", *pages)
        self.assertEqual(receipt(out)["relevancy"]["choice"], "native", proc.stderr)

    def test_native_requested_without_native_fails(self):
        proc, out = run_cli("--asin-pages", f"B0TEST0001={FIX / 'kr-B0TEST0001-page-001.json'}",
                            f"B0TEST0002={FIX / 'kr-B0TEST0002-page-001.json'}", "--relevancy", "native")
        self.assertEqual(proc.returncode, 2)


class FilterTest(unittest.TestCase):
    def test_pool_needs_a_top_n_asin(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native")
        pool = [r[1] for r in read_csv(out / "expanded.csv")[1:]]
        self.assertNotIn("far widget", pool)          # native 0.05 but ranks 200 and 300
        self.assertEqual(receipt(out)["noise_filters"]["pool_rows_removed"], 1)

    def test_core_drops_one_word_unless_allowed(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native")
        core = [r[1] for r in read_csv(out / "core.csv")[1:]]
        self.assertEqual(core, ["widget cleaner", "widget cleaner's kit"])
        self.assertEqual(receipt(out)["noise_filters"]["core_one_word_removed"], [["widget", 5000]])
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native", "--allow-one-word", "widget")
        self.assertIn("widget", [r[1] for r in read_csv(out / "core.csv")[1:]])

    def test_rows_without_search_volume_stay_out(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native")
        self.assertNotIn("widget cleaner refill", [r[1] for r in read_csv(out / "expanded.csv")[1:]])
        self.assertEqual(receipt(out)["no_search_volume"], 1)

    def test_core_min_threshold(self):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native", "--core-min", "0.6")
        self.assertEqual([r[1] for r in read_csv(out / "core.csv")[1:]], ["widget cleaner"])


class CleaningTest(unittest.TestCase):
    def test_clean_keyword(self):
        self.assertEqual(kw.clean_keyword("Widget Cleaner&#39;s Kit")[0], "widget cleaner's kit")
        self.assertEqual(kw.clean_keyword("widget￼ cleaner ")[0], "widget cleaner")
        self.assertEqual(kw.clean_keyword("giant+widget+seeds")[0], "giant widget seeds")
        self.assertEqual(kw.clean_keyword("brand +widget +spray")[0], "brand widget spray")
        self.assertEqual(kw.clean_keyword("biotin + collagen")[0], "biotin + collagen")
        self.assertEqual(kw.clean_keyword("aloe cure+")[0], "aloe cure+")
        self.assertEqual(kw.clean_keyword("a+d ointment")[0], "a+d ointment")
        self.assertEqual(kw.clean_keyword("'widget oil'")[0], "widget oil")
        self.assertIsNone(kw.clean_keyword("brand widget | 20 pack")[0])
        self.assertIsNone(kw.clean_keyword(" ￼ ")[0])

    def test_dedupe_counts(self):
        proc, out = run_cli("--pages", *PAGES)
        r = receipt(out)
        self.assertEqual((r["raw_rows"], r["meta_total"], r["unique"], r["dropped"], r["merged"]), (8, 8, 6, 1, 1))
        self.assertEqual(r["merged_keywords"][0]["as"], "widget cleaner spray")
        self.assertEqual(len(r["inputs"]), 2)
        self.assertEqual(len(r["inputs"][0]["sha256"]), 64)


class ReconciliationTest(unittest.TestCase):
    def test_missing_page_fails_and_writes_only_receipt(self):
        proc, out = run_cli("--pages", PAGES[0])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("meta.total", proc.stderr)
        r = receipt(out)
        self.assertFalse(r["ok"])
        self.assertEqual((r["raw_rows"], r["meta_total"]), (4, 8))
        self.assertFalse((out / "core.csv").exists())
        self.assertFalse((out / "research.json").exists())

    def test_repeated_page_fails(self):
        proc, out = run_cli("--pages", PAGES[0], PAGES[0], PAGES[1])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("given twice", proc.stderr)

    def test_unaccounted_rows_fail(self):
        original = kw.dedupe

        def lossy(rows, fill):
            by_kw, dropped, merged = original(rows, fill)
            return by_kw, dropped, merged[:-1] if merged else merged

        kw.dedupe = lossy
        try:
            out = Path(tempfile.mkdtemp())
            with contextlib.redirect_stderr(io.StringIO()):
                rc = kw.main(["--pages", *PAGES, "--out-dir", str(out)])
        finally:
            kw.dedupe = original
        self.assertEqual(rc, 2)
        self.assertFalse(receipt(out)["accounted"])

    def test_overlapping_pages_fail(self):
        # Page 2 repeats a page-1 row in place of one of its own: counts still add up,
        # but a real keyword would be lost, so the adapter must refuse.
        p1 = json.loads(Path(PAGES[0]).read_text())
        p2 = json.loads(Path(PAGES[1]).read_text())
        p2["data"]["keywords"][-1] = p1["data"]["keywords"][0]
        tmp = Path(tempfile.mkdtemp())
        (tmp / "p2.json").write_text(json.dumps(p2))
        proc, out = run_cli("--pages", PAGES[0], str(tmp / "p2.json"), "--marketplace", "US")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("appears twice", proc.stderr)

    def test_anchor_outside_the_search_fails(self):
        proc, out = run_cli("--pages", *PAGES, "--anchor", "B0TEST9999")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("not in the pages", proc.stderr)

    def test_marketplace_mismatch_fails(self):
        proc, out = run_cli("--pages", *PAGES, "--marketplace", "DE")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("marketplace", proc.stderr)


class ResearchJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        proc, out = run_cli("--pages", *PAGES, "--relevancy", "native", "--marketplace", "US",
                            "--search-id", "123", "--live-info", str(FIX / "live-info.json"),
                            "--date-from", "2026-07-01", "--date-to", "2026-09-30")
        assert proc.returncode == 0, proc.stderr
        cls.out = out
        cls.r = json.loads((out / "research.json").read_text())

    def test_identity(self):
        r = self.r
        self.assertEqual(r["provider"], "soldscope")
        self.assertEqual(r["source"], "keyword_research_search_multi_asin")
        self.assertEqual((r["search_id"], r["marketplace"], r["anchor"]), (123, "US", None))
        self.assertEqual(r["asins"], A)
        self.assertEqual((r["date_from"], r["date_to"]), ("2026-07-01", "2026-09-30"))
        self.assertTrue(r["created_at"].endswith("Z"))
        self.assertEqual(r["statistics"], {"numKeywords": 4, "rawRows": 8, "uniqueRows": 6,
                                           "poolRows": 4, "coreRows": 2,
                                           "rankDates": {"organicMin": "2026-10-01",
                                                         "organicMax": "2026-10-01"}})
        self.assertEqual(r["thresholds"], {"topN": 50, "p1RankMax": 48, "rankCap": 101,
                                           "poolMin": 0.01, "coreMin": 0.30})
        self.assertEqual(r["relevancyChoice"], "native")

    def test_keyword_cpc(self):
        by = {k["keyword"]: k for k in self.r["keywords"]}
        self.assertEqual((by["widget cleaner"]["cpc"], by["widget cleaner"]["cpcMin"],
                          by["widget cleaner"]["cpcMax"]), (1.25, 0.9, 1.6))
        self.assertEqual(by["widget"]["cpc"], 0)
        for k in self.r["keywords"]:
            self.assertTrue({"cpc", "cpcMin", "cpcMax"} <= set(k), k["keyword"])

    def test_listing_age(self):
        comps = {c["asin"]: c for c in self.r["competitors"]}
        self.assertEqual((comps["B0TEST0001"]["listingAgeDays"], comps["B0TEST0001"]["listingAgeApprox"]),
                         (400, False))
        # days: false falls back to y/m/d: 1*365.25 + 2*30.44 + 3 = 429.13
        self.assertEqual((comps["B0TEST0002"]["listingAgeDays"], comps["B0TEST0002"]["listingAgeApprox"]),
                         (429, True))
        self.assertEqual((comps["B0TEST0003"]["listingAgeDays"], comps["B0TEST0003"]["listingAgeApprox"]),
                         (None, False))
        self.assertEqual(comps["B0TEST0004"]["listingAgeDays"], None)

    def test_rank_dates_span(self):
        tmp = Path(tempfile.mkdtemp())
        pages = []
        for i, p in enumerate(PAGES):
            page = json.loads(Path(p).read_text())
            page["data"]["keywords"][0]["asinsPositions"]["B0TEST0002"]["organicScrapeEventDate"] = \
                ["2026-09-12", "2026-10-20"][i]
            q = tmp / Path(p).name
            q.write_text(json.dumps(page))
            pages.append(str(q))
        proc, out = run_cli("--pages", *pages, "--relevancy", "computed")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        r = json.loads((out / "research.json").read_text())
        self.assertEqual(r["statistics"]["rankDates"], {"organicMin": "2026-09-12", "organicMax": "2026-10-20"})
        self.assertEqual(r["relevancyChoice"], "computed")

    def test_keywords_and_rank_caps(self):
        by = {k["keyword"]: k for k in self.r["keywords"]}
        wc = by["widget cleaner"]
        self.assertEqual(wc["asinRanks"], {"B0TEST0001": 3, "B0TEST0002": 10, "B0TEST0003": 40,
                                           "B0TEST0004": 101})
        self.assertEqual(wc["sponsoredAsinRanks"]["B0TEST0001"], 5)
        self.assertIsNone(wc["sponsoredAsinRanks"]["B0TEST0002"])
        self.assertEqual((wc["origin"], wc["relevancy"], wc["searchVolume"]), ("core", 0.75, 1000))
        self.assertEqual(by["widget"]["origin"], "pool")
        core = read_csv(self.out / "core.csv")
        self.assertEqual(core[1][5:], ["3", "10", "40", "101"])
        self.assertEqual(kw.cap_rank(0), None)
        self.assertEqual(kw.cap_rank(250), 101)
        self.assertEqual(kw.cap_rank(100), 100)

    def test_competitors(self):
        comps = {c["asin"]: c for c in self.r["competitors"]}
        self.assertEqual(list(comps), A)
        c1 = comps["B0TEST0001"]
        self.assertEqual(c1["category"], "Home & Kitchen")
        self.assertEqual(c1["sellerCountry"], "")
        self.assertEqual(c1["reviews"], c1["reviewCount"])
        # Both counts use the Core list (2 rows here), like DataDive's visible MKL.
        self.assertEqual(c1["advertisedKws"], 1)
        self.assertEqual(c1["kwRankedOnP1Percent"], 1.0)
        self.assertEqual(comps["B0TEST0002"]["fulfillment"], "AMZ")
        self.assertEqual(comps["B0TEST0003"]["kwRankedOnP1Percent"], 0.5)
        self.assertEqual(comps["B0TEST0002"]["kwRankedOnP1Percent"], 0.5)
        c4 = comps["B0TEST0004"]    # only in live info
        self.assertEqual((c4["price"], c4["reviewCount"], c4["sales"], c4["fulfillment"], c4["brand"]),
                         (24.99, 420, 300, "FBA/FBM", "Test Brand 4"))
        self.assertEqual(c4["kwRankedOnP1Percent"], 0.0)
        b = self.r["benchmark"]
        self.assertEqual((b["price"], b["reviewCount"], b["rating"]), (17.5, 250, 4.15))
        self.assertEqual(b["basis"], "median of 4 compared ASINs")
        rows = read_csv(self.out / "competitors.csv")
        self.assertEqual(rows[1], ["B0TEST0001", "Test Brand 1", "", "0", "4.0", "100", "10.00", "1000",
                                   "10000.00", "FBA", "Home & Kitchen"])

    def test_roots(self):
        roots = read_csv(self.out / "roots.csv")[1:]
        self.assertEqual([r[1:4] for r in roots[:2]], [["widget", "2", "1300"], ["cleaner", "1", "1000"]])
        self.assertEqual(float(roots[0][4]), 1.0)
        self.assertNotIn("widget cleaner", [r[1] for r in roots])   # 2 < --ngram-min-freq 3


class AsinPagesTest(unittest.TestCase):
    def test_merge_mode(self):
        proc, out = run_cli("--asin-pages", f"B0TEST0001={FIX / 'kr-B0TEST0001-page-001.json'}",
                            f"B0TEST0002={FIX / 'kr-B0TEST0002-page-001.json'}",
                            "--anchor", "B0TEST0002", "--marketplace", "DE", "--search-id", "11,12")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        r = receipt(out)
        self.assertEqual((r["raw_rows"], r["unique"], r["merged"], r["joined_across_asins"]), (6, 4, 2, 2))
        self.assertEqual(r["relevancy"]["choice"], "computed")
        research = json.loads((out / "research.json").read_text())
        self.assertEqual(research["source"], "kr_asin_search")
        self.assertEqual(research["search_id"], [11, 12])
        self.assertEqual(research["asins"], ["B0TEST0002", "B0TEST0001"])
        by = {k["keyword"]: k for k in research["keywords"]}
        self.assertEqual(by["widget reiniger"]["relevancy"], 0.5)       # 60 is outside the top 50
        self.assertEqual(by["widget reiniger"]["asinRanks"], {"B0TEST0002": 60, "B0TEST0001": 3})
        self.assertEqual(by["widget reiniger"]["sponsoredAsinRanks"]["B0TEST0001"], 7)
        self.assertEqual(by["widget"]["relevancy"], 1.0)
        self.assertEqual(read_csv(out / "core.csv")[0][5:], ["B0TEST0002", "B0TEST0001"])
        self.assertEqual(research["relevancyChoice"], "computed")
        self.assertIn("rankDates", research["statistics"])
        self.assertEqual(research["thresholds"]["topN"], 50)
        for k in research["keywords"]:
            self.assertTrue({"cpc", "cpcMin", "cpcMax"} <= set(k), k["keyword"])

    def test_merge_mode_short_read_fails(self):
        tmp = Path(tempfile.mkdtemp()) / "short.json"
        page = json.loads((FIX / "kr-B0TEST0001-page-001.json").read_text())
        page["meta"]["total"] = 5
        tmp.write_text(json.dumps(page))
        proc, out = run_cli("--asin-pages", f"B0TEST0001={tmp}")
        self.assertEqual(proc.returncode, 2)

    def test_pages_and_asin_pages_are_exclusive(self):
        proc, out = run_cli("--pages", *PAGES, "--asin-pages", f"B0TEST0001={FIX / 'kr-B0TEST0001-page-001.json'}")
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
