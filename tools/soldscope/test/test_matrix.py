"""Tests for tools/soldscope/matrix.py on synthetic data (no client data)."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"
KW_TOOL = HERE.parent / "keywords.py"
TOOL = HERE.parent / "matrix.py"
PAGES = [str(FIX / "multi-page-001.json"), str(FIX / "multi-page-002.json")]
XSS = "</script><img src=x onerror=alert(1)>"


def asins(n):
    return [f"B0TEST{i:04d}" for i in range(1, n + 1)]


def make_research(rows, n=4, sales=None, drop=(), **extra):
    """research.json in keywords.py's shape. rows: (keyword, sv, ranks[, sponsored[, stored relevancy]])."""
    a = asins(n)
    kws = []
    for row in rows:
        kw, sv, ranks = row[:3]
        spon = row[3] if len(row) > 3 and row[3] is not None else [None] * n
        rel = row[4] if len(row) > 4 else round(sum(1 for r in ranks if isinstance(r, int) and r <= 50) / n, 4)
        kws.append({"keyword": kw, "searchVolume": sv, "relevancy": rel, "cpc": 1.5, "cpcMin": 1.0, "cpcMax": 2.0,
                    "asinRanks": dict(zip(a, ranks)), "sponsoredAsinRanks": dict(zip(a, spon)), "origin": "pool"})
    sales = sales or [None] * n
    research = {
        "provider": "soldscope", "source": "keyword_research_search_multi_asin", "search_id": 7,
        "marketplace": "US", "asins": a, "anchor": None, "date_from": None, "date_to": None,
        "created_at": "2026-10-02T00:00:00Z",
        "statistics": {"rankDates": {"organicMin": "2026-09-01", "organicMax": "2026-10-01"}},
        "thresholds": {"topN": 50, "p1RankMax": 48, "rankCap": 101, "poolMin": 0.01, "coreMin": 0.3},
        "relevancyChoice": "computed", "keywords": kws,
        "competitors": [{"asin": x, "brand": f"Test Brand {i + 1}", "title": f"Test Widget {i + 1}",
                         "sales": s, "revenue": None if s is None else s * 10, "price": 10.0,
                         "listingAgeDays": 400, "listingAgeApprox": False}
                        for i, (x, s) in enumerate(zip(a, sales))],
    }
    for k in drop:
        research.pop(k)
    research.update(extra)
    d = Path(tempfile.mkdtemp(prefix="soldscope-mx-"))
    (d / "research.json").write_text(json.dumps(research), encoding="utf-8")
    return d


def run_matrix(d, *args):
    proc = subprocess.run([sys.executable, str(TOOL), "--research", str(d / "research.json"),
                           "--out-dir", str(d), *args], capture_output=True, text=True)
    return proc


def payload(d):
    html = (d / "matrix.html").read_text(encoding="utf-8")
    b64 = re.search(r'const DATA_B64 = "([A-Za-z0-9+/=]*)"', html).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def receipt(d):
    return json.loads((d / "matrix-receipt.json").read_text())


def header(p, label):
    return next(h for h in p["header"] if h["label"] == label)


class FixtureRunTest(unittest.TestCase):
    """keywords.py on the shared fixtures, then matrix.py."""

    @classmethod
    def setUpClass(cls):
        cls.d = Path(tempfile.mkdtemp(prefix="soldscope-mx-"))
        proc = subprocess.run([sys.executable, str(KW_TOOL), "--pages", *PAGES, "--marketplace", "US",
                               "--search-id", "5", "--relevancy", "computed", "--out-dir", str(cls.d)],
                              capture_output=True, text=True)
        assert proc.returncode == 0, proc.stderr
        cls.proc = run_matrix(cls.d, "--views", "roots,outliers", "--outlier-min-sv", "100")
        assert cls.proc.returncode == 0, cls.proc.stderr
        cls.p, cls.r = payload(cls.d), receipt(cls.d)

    def test_rows_and_views(self):
        self.assertEqual([r[0] for r in self.p["views"]["matrix"]["rows"]], ["widget", "widget cleaner"])
        self.assertEqual([r[0] for r in self.p["views"]["outliers"]["rows"]],
                         ["widget cleaner's kit", "widget cleaner spray"])
        # computed relevancy: Core is "widget cleaner" alone; ties on broad SV sort by name
        self.assertEqual([r[:3] for r in self.p["views"]["roots"]["rows"]],
                         [["cleaner", 1, 1000], ["widget", 1, 1000]])
        self.assertEqual(self.r["stored_relevancy_differs"], 0)      # computed choice: same share
        self.assertTrue(self.r["ok"])
        self.assertIn("matrix 2/2", self.proc.stdout)

    def test_header_from_research(self):
        self.assertEqual([c["t"] for c in header(self.p, "Listing Age")["cells"]][:2], ["1y 1m", "1y 2m approx."])
        self.assertEqual(self.p["note"], "2 terms, relevancy >= 30%, ranks scraped 2026-10-01 to 2026-10-01")
        self.assertIn("search 5", self.p["meta"])
        bid = self.p["views"]["matrix"]["rows"][1]
        self.assertEqual(bid[3:6], [1.25, 0.9, 1.6])
        self.assertIsNone(self.p["views"]["matrix"]["rows"][0][3])   # cpc 0 shows blank


class MetricsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = make_research([
            ("alpha one", 1000, [1, 10, 60, None], [2, None, None, None]),
            ("beta two", 3000, [5, 49, 30, 20]),
            ("gamma", 600, [101, 48, 50, 3]),
            ("no volume", None, [1, 1, 1, 1]),
            ("lonely", 5000, [1, None, None, None]),       # 25% < 30%
        ], sales=[100, 300, None, 200])
        proc = run_matrix(cls.d)
        assert proc.returncode == 0, proc.stderr
        cls.p, cls.r = payload(cls.d), receipt(cls.d)
        cls.c = {c["asin"]: c for c in cls.p["comps"]}

    def test_competitor_order_and_rank_columns(self):
        self.assertEqual([c["asin"] for c in self.p["comps"]],
                         ["B0TEST0002", "B0TEST0004", "B0TEST0001", "B0TEST0003"])
        rows = {r[0]: r for r in self.p["views"]["matrix"]["rows"]}
        self.assertEqual(list(rows), ["beta two", "alpha one", "gamma"])          # SV desc
        self.assertEqual(rows["alpha one"][7], [10, None, 1, 60])                 # follows comps order
        self.assertEqual(rows["alpha one"][8], [None, None, 2, None])

    def test_p1_share_strength_advertised(self):
        a1, a2, a3 = self.c["B0TEST0001"], self.c["B0TEST0002"], self.c["B0TEST0003"]
        self.assertEqual((a1["p1Kws"], a1["p1Sv"], a1["strength"], a1["advKws"]), (2, 4000, "Very Strong", 1))
        self.assertAlmostEqual(a1["sov"], 4000 / 4600)
        self.assertAlmostEqual(a1["p1Pct"], 2 / 3)
        self.assertAlmostEqual(a1["advPct"], 1 / 3)
        self.assertEqual((a2["p1Kws"], a2["p1Sv"], a2["strength"]), (2, 1600, "Very Weak"))   # 49 is off P1
        self.assertEqual((a3["p1Kws"], a3["p1Sv"], a3["strength"]), (1, 3000, "Strong"))
        strength = header(self.p, "Strength")
        self.assertEqual(strength["median"]["chips"][0][0], "1 Very Weak")
        self.assertEqual([c.get("badge") for c in strength["cells"]][2], "vs")
        self.assertEqual(header(self.p, "KWs on P1")["cells"][2]["s"], "67%")

    def test_niche_median_range_with_three_values(self):
        sales = header(self.p, "30d Sales")["median"]
        self.assertEqual(sales["t"], "150 - 200")       # median 200; avg of 2nd..last (200, 100); lower first
        self.assertIn("Median 200; average of the 2nd to 4th highest 150", sales["tip"])
        self.assertEqual(header(self.p, "Brand")["median"]["t"], "4 brands")
        self.assertEqual(header(self.p, "ASIN")["cells"][0]["href"], "https://www.amazon.com/dp/B0TEST0002")


class LaunchScoreTest(unittest.TestCase):
    def test_half_up_and_floor(self):
        r9 = [1] * 9 + [None]
        d = make_research([
            ("half", 1500, [1] * 10),                  # 1500 / 1.0 * 0.003 = 4.5 -> 5
            ("just under", 1499, [1] * 10),            # 4.497 -> 4
            ("example", 256445, r9),                   # 256445 / 0.9 * 0.003 = 854.8 -> 855
            ("below forty", 9000, [1, 1, 1] + [None] * 7),
        ], n=10, sales=[500] + [None] * 9)
        proc = run_matrix(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        p = payload(d)
        ls = {r[0]: r[6] for r in p["views"]["matrix"]["rows"]}
        self.assertEqual(ls, {"half": 5, "just under": 4, "example": 855, "below forty": None})
        self.assertEqual(header(p, "30d Sales")["median"]["t"], "500")    # one value: median only


class OutlierTest(unittest.TestCase):
    def test_selection_and_overlap_badge(self):
        n = 10
        d = make_research([
            ("edge", 5000, [1, 2, 3] + [None] * 7),        # exactly 30%: matrix and outlier
            ("out", 3000, [None, 4] + [None] * 8),         # 10%
            ("small", 1000, [5] + [None] * 9),             # below the SV floor
            ("high", 9000, [1, 2, 3, 4] + [None] * 6),     # 40%: matrix only
            ("far", 4000, [70, None] + [None] * 8),        # no top-N ASIN: h = 0, still an outlier
        ], n=n)
        proc = run_matrix(d, "--views", "outliers")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        p, r = payload(d), receipt(d)
        self.assertEqual([(x[0], x[9]) for x in p["views"]["outliers"]["rows"]],
                         [("edge", 1), ("far", 0), ("out", 0)])
        self.assertEqual([x[0] for x in p["views"]["matrix"]["rows"]], ["high", "edge"])
        self.assertEqual(r["outliers_in_matrix"], 1)
        c = {x["asin"]: x for x in p["comps"]}
        self.assertEqual((c["B0TEST0002"]["outlierSv"], c["B0TEST0002"]["outlierKws"]), (8000, 2))
        self.assertEqual((c["B0TEST0001"]["outlierSv"], c["B0TEST0001"]["outlierKws"]), (5000, 1))
        self.assertIn("top 50", p["outlierNote"])
        self.assertNotIn("roots", p["views"])

    def test_outlier_header_without_outlier_view(self):
        d = make_research([("edge", 5000, [1, 2, 3] + [None] * 7)], n=10)
        proc = run_matrix(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        p = payload(d)
        self.assertNotIn("outliers", p["views"])
        self.assertEqual(header(p, "30d Outlier SV")["cells"][0]["t"], "5,000")


class InputTest(unittest.TestCase):
    def test_relevancy_is_recomputed(self):
        # Stored (native, rank-weighted) 0.9, but only 1 of 4 ASINs ranks in the top 50.
        d = make_research([("native high", 800, [3, None, None, None], None, 0.9),
                           ("kept", 500, [1, 2, None, None], None, 0.5)])
        proc = run_matrix(d)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        p = payload(d)
        self.assertEqual([(r[0], r[2]) for r in p["views"]["matrix"]["rows"]], [("kept", 2)])
        self.assertEqual(receipt(d)["stored_relevancy_differs"], 1)

    def test_missing_thresholds_exits_2(self):
        d = make_research([("a b", 100, [1, 1, 1, 1])], drop=("thresholds",))
        proc = run_matrix(d)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("re-run tools/soldscope/keywords.py", proc.stderr)
        self.assertFalse((d / "matrix.html").exists())
        self.assertFalse(receipt(d)["ok"])

    def test_roots_view_needs_roots_csv(self):
        d = make_research([("a b", 100, [1, 1, 1, 1])])
        proc = run_matrix(d, "--views", "roots")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("roots.csv", proc.stderr)

    def test_malformed_rank_exits_2(self):
        d = make_research([("a b", 100, [1, "x", 1, 1])])
        self.assertEqual(run_matrix(d).returncode, 2)

    def test_script_text_never_reaches_the_html(self):
        d = make_research([(XSS, 900, [1, 1, 1, 1]), ("plain", 100, [1, 1, 1, 1])])
        (d / "research.json").write_text((d / "research.json").read_text().replace(
            '"Test Brand 1"', json.dumps(XSS)), encoding="utf-8")
        proc = run_matrix(d, "--title", XSS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        html = (d / "matrix.html").read_text(encoding="utf-8")
        self.assertNotIn(XSS, html)
        self.assertNotIn("<img", html)
        # The title tag carries the title HTML-escaped; no live markup reaches the page.
        self.assertIn("<title>&lt;/script&gt;&lt;img src=x onerror=alert(1)&gt;</title>", html)
        self.assertNotIn("onerror", html.replace("&lt;img src=x onerror=alert(1)&gt;", ""))
        self.assertEqual(html.count("</script>"), 1)
        p = payload(d)
        self.assertEqual(p["views"]["matrix"]["rows"][0][0], XSS)
        self.assertEqual(p["title"], XSS)


def bulk_rows(count, n=4):
    rows = []
    for i in range(count):
        h = hashlib.sha256(str(i).encode()).hexdigest()
        words = " ".join(h[j:j + 5] for j in range(0, 20, 5))
        rows.append((f"kw {words}", 1000 + (i // 2) * 3, [int(h[k], 16) * 3 + 1 for k in range(n)]))
    return rows                                      # pairs share an SV, so ties are exercised


class ReviewFixesTest(unittest.TestCase):
    def test_title_holding_the_data_token_stays_text(self):
        d = make_research([("a b", 900, [1, 1, 1, 1])])
        proc = run_matrix(d, "--title", "Widget __DATA__ Matrix")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        html = (d / "matrix.html").read_text(encoding="utf-8")
        self.assertIn("<title>Widget __DATA__ Matrix</title>", html)
        self.assertEqual(payload(d)["title"], "Widget __DATA__ Matrix")

    def test_header_integers_round_half_up(self):
        sys.path.insert(0, str(TOOL.parent))
        import matrix
        self.assertEqual([matrix.fmt_int(v) for v in (4.5, 554.5, 1971.5, 2.4)], ["5", "555", "1,972", "2"])


class SizeTest(unittest.TestCase):
    def test_trimming_reconciles_and_shows_a_banner(self):
        d = make_research(bulk_rows(600))
        proc = run_matrix(d, "--max-bytes", "0")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        full = receipt(d)["html_bytes"]
        cap = full - 4000
        proc = run_matrix(d, "--max-bytes", str(cap))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        r, p = receipt(d), payload(d)
        v = r["views"]["matrix"]
        self.assertTrue(r["ok"])
        self.assertLessEqual(r["html_bytes"], cap)
        self.assertGreater(v["dropped"], 0)
        self.assertEqual(v["rendered"] + v["dropped"], v["eligible"])
        self.assertEqual(v["eligible"], 600)
        self.assertEqual(len(v["dropped_keywords"]), v["dropped"])
        ordered = sorted(bulk_rows(600), key=lambda t: (-t[1], t[0]))
        self.assertEqual(v["dropped_keywords"], [t[0] for t in ordered[v["rendered"]:]])
        self.assertEqual([x[0] for x in p["views"]["matrix"]["rows"]], [t[0] for t in ordered[:v["rendered"]]])
        self.assertEqual(p["views"]["matrix"]["banner"],
                         f"Showing top {v['rendered']:,} of 600 terms by search volume to fit the "
                         f"{cap:,}-byte page limit")
        # Header metrics still count the full row set.
        self.assertEqual(sum(1 for t in bulk_rows(600) if t[2][0] <= 48),
                         next(c for c in p["comps"] if c["asin"] == "B0TEST0001")["p1Kws"])
        self.assertTrue(p["note"].startswith("600 terms"))

    def test_payload_hash_is_stable(self):
        d = make_research(bulk_rows(50))
        hashes = []
        for _ in range(2):
            self.assertEqual(run_matrix(d, "--views", "outliers").returncode, 0)
            hashes.append(receipt(d)["payload_sha256"])
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(len(hashes[0]), 64)

    def test_template_budget(self):
        self.assertLessEqual((HERE.parent / "matrix_template.html").stat().st_size, 24 * 1024)


NODE_HARNESS = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const code = html.slice(html.lastIndexOf('<script>') + 8, html.lastIndexOf('</script>'));
const mod = { exports: {} };
new Function('module', code)(mod);
const KM = mod.exports;
(async () => {
  const d = await KM.decode(KM.B64);
  const t = (s, k, vals) => { const f = KM.parseFilter(s, k); return f === null ? 'none' : f === undefined ? 'bad' : vals.map(f); };
  console.log(JSON.stringify({
    title: d.title, rows: d.views.matrix.rows.map(r => r[0]),
    text: [t('clean', 'text', ['widget cleaner', 'widget']), t('widget, !clean', 'text', ['widget', 'widget cleaner']),
           t('!clean', 'text', ['widget', 'widget cleaner']), t('spray, kit', 'text', ['a kit', 'a spray', 'a mop'])],
    num: [t('>10', 'num', [11, 10, null]), t('>=10', 'num', [10, 9]), t('<10', 'num', [9, 10]), t('<=5', 'num', [5, 6]),
          t('=10', 'num', [10, 11]), t('10', 'num', [10, 11]), t('10-50', 'num', [10, 50, 51, null]),
          t('2,000', 'num', [2000]), t('abc', 'num', [1]), t('  ', 'num', [1])],
    asc: KM.order([5, null, 101, 1, 100], 'asc'), desc: KM.order([5, null, 101, 1, 100], 'desc'),
    none: KM.order([5, null, 1], null), text_asc: KM.order(['b', 'a', null], 'asc'),
    next: [KM.nextDir(null, true), KM.nextDir('asc', true), KM.nextDir('desc', true), KM.nextDir(null, false)],
    band: [1, 5, 6, 21, 22, 40, 41, 101, null].map(KM.band),
  }));
})().catch(e => { console.error(e); process.exit(1); });
"""


@unittest.skipIf(shutil.which("node") is None, "node not installed")
class NodeHelpersTest(unittest.TestCase):
    def test_decode_filter_sort(self):
        d = Path(tempfile.mkdtemp(prefix="soldscope-mx-"))
        proc = subprocess.run([sys.executable, str(KW_TOOL), "--pages", *PAGES, "--relevancy", "computed",
                               "--out-dir", str(d)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_matrix(d, "--title", "Widget Keyword Matrix").returncode, 0)
        harness = d / "harness.js"
        harness.write_text(NODE_HARNESS, encoding="utf-8")
        proc = subprocess.run(["node", str(harness), str(d / "matrix.html")], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["title"], "Widget Keyword Matrix")
        self.assertEqual(out["rows"], ["widget", "widget cleaner"])
        self.assertEqual(out["text"], [[True, False], [True, False], [True, False], [True, True, False]])
        self.assertEqual(out["num"], [[True, False, False], [True, False], [True, False], [True, False],
                                      [True, False], [True, False], [True, True, False, False], [True],
                                      "bad", "none"])
        self.assertEqual(out["asc"], [3, 0, 4, 2, 1])     # 1, 5, 100, 101 (>100), blank
        self.assertEqual(out["desc"], [2, 4, 0, 3, 1])    # 101, 100, 5, 1, blank still last
        self.assertEqual(out["none"], [0, 1, 2])
        self.assertEqual(out["text_asc"], [1, 0, 2])
        self.assertEqual(out["next"], ["asc", "desc", None, "desc"])
        self.assertEqual(out["band"], [0, 0, 1, 1, 2, 2, 3, 3, 3])


if __name__ == "__main__":
    unittest.main()
