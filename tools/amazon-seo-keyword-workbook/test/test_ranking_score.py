import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

import ranking_score as rs  # noqa: E402
from build_keyword_workbook import (  # noqa: E402
    RANKING_SCORE_LABEL,
    append_ranking_score_row,
    compute_ranking_scores,
    ranking_score_checks,
    ranking_score_row,
)


class MatchTierTest(unittest.TestCase):
    def test_exact_phrase(self):
        self.assertEqual(rs.match_tier("blue widget", "Compact Blue Widget for travel"), 1.0)

    def test_exact_after_singularization(self):
        self.assertEqual(rs.match_tier("blue widgets", "Compact blue widget"), 0.75)
        self.assertEqual(rs.match_tier("blue widget", "Compact blue widgets"), 0.75)

    def test_any_order(self):
        self.assertEqual(rs.match_tier("blue widget", "Widget in deep blue"), 0.5)

    def test_any_order_after_singularization(self):
        self.assertEqual(rs.match_tier("blue widgets", "Widget in deep blue"), 0.25)

    def test_no_match(self):
        self.assertEqual(rs.match_tier("red gadget", "Compact blue widget"), 0.0)
        self.assertEqual(rs.match_tier("", "Compact blue widget"), 0.0)

    def test_short_words_and_double_s_are_not_singularized(self):
        self.assertEqual(rs.singularize("gas"), "gas")
        self.assertEqual(rs.singularize("glass"), "glass")
        self.assertEqual(rs.singularize("cups"), "cup")

    def test_accent_folding(self):
        self.assertEqual(rs.match_tier("creme brulee", "Crème Brûlée Widget"), 1.0)

    def test_object_replacement_char_and_html_entities(self):
        self.assertEqual(rs.match_tier("￼blue widget", "blue widget"), 1.0)
        self.assertEqual(rs.match_tier("salt pepper widget", "Salt &amp; Pepper Widget"), 1.0)
        self.assertEqual(rs.tokenize("A\ufffcB"), ["ab"])

    def test_object_replacement_char_inside_a_word_is_removed(self):
        self.assertEqual(rs.match_tier("widget", "wid\ufffcget case"), 1.0)


class ScoreListingTest(unittest.TestCase):
    def test_bullets_add_nothing_when_title_is_exact(self):
        s = rs.score_listing([("blue widget", 1000)], "Blue Widget", ["blue widget again"])
        self.assertEqual(s["title"], 1000)
        self.assertEqual(s["bullets"], 0)

    def test_bullets_add_the_tier_improvement_over_a_broad_title(self):
        s = rs.score_listing([("blue widget", 1000)], "Widget, blue", ["A blue widget"])
        self.assertEqual(s["title"], 500)
        self.assertEqual(s["bullets"], 500)

    def test_description_credits_only_over_the_best_higher_field(self):
        s = rs.score_listing([("blue widget", 1000)], "Widget", ["Widget in blue"], "blue widget")
        self.assertEqual((s["title"], s["bullets"], s["description"]), (0, 500, 500))

    def test_total_uses_weights(self):
        kws = [("alpha", 100), ("beta", 10), ("gamma", 1)]
        s = rs.score_listing(kws, "alpha", ["beta"], "gamma")
        self.assertEqual(s["total"], 3 * 100 + 2 * 10 + 1)
        self.assertEqual(s["max_possible"], 3 * 111)
        self.assertEqual(s["keywords_credited"], 3)
        custom = rs.score_listing(kws, "alpha", ["beta"], "gamma", weights={"title": 1, "bullets": 1})
        self.assertEqual(custom["total"], 100 + 10 + 1)

    def test_item_highlights_count_with_the_title(self):
        kws = [("travel case", 400)]
        s = rs.score_listing(kws, "Blue Widget", ["travel case included"], item_highlights="Travel Case")
        self.assertEqual((s["title"], s["bullets"]), (400, 0))
        b = rs.score_listing(kws, "Blue Widget", [], item_highlights="Travel Case", highlights_field="bullets")
        self.assertEqual((b["title"], b["bullets"]), (0, 400))
        n = rs.score_listing(kws, "Blue Widget", [], item_highlights="Travel Case", highlights_field="none")
        self.assertEqual(n["total"], 0)

    def test_empty_fields(self):
        s = rs.score_listing([("blue widget", 1000)], "", [], "")
        self.assertEqual((s["total"], s["pct_of_max"], s["keywords_credited"]), (0, 0.0, 0))
        none = rs.score_listing([], "Blue Widget", None)
        self.assertEqual((none["total"], none["max_possible"], none["pct_of_max"]), (0, 0, 0.0))

    def test_bullets_accept_a_string(self):
        s = rs.score_listing([("blue widget", 1000)], "", "A blue widget")
        self.assertEqual(s["bullets"], 1000)


class InputParsingTest(unittest.TestCase):
    def test_keywords_from_rows_detects_headers_and_keeps_every_row(self):
        rows = [["", "SV", "Search Terms"], ["", "1,000", "blue widget"],
                ["", "20", "\ufffcblue widget"], ["", "300", "red widget"], ["", "5", ""]]
        self.assertEqual(
            rs.keywords_from_rows(rows),
            [("blue widget", 1000.0), ("\ufffcblue widget", 20.0), ("red widget", 300.0)],
        )

    def test_low_sv_variant_first_does_not_drop_the_high_sv_keyword(self):
        rows = [["", "Search Terms", "SV"], ["", "\ufffcblue widget", "20"], ["", "blue widget", "1000"]]
        kws = rs.keywords_from_rows(rows)
        self.assertEqual(sum(sv for _, sv in kws), 1020.0)
        s = rs.score_listing(kws, "Blue Widget", [])
        self.assertEqual(s["title"], 1020)

    def test_keywords_from_rows_falls_back_to_builder_columns(self):
        rows = [["", "Keyword Phrase", "Volume"], ["", "blue widget", "40"]]
        self.assertEqual(rs.keywords_from_rows(rows), [("blue widget", 40.0)])

    def test_draft_uses_first_line_of_each_cell(self):
        rows = [
            {"section": "Title (≤75 characters)", "new": "Blue Widget\nwhy: rationale"},
            {"section": "Item Highlights", "new": "Travel Case · Soft Grip"},
            {"section": "Bullet 1", "new": "Grip: Soft grip."},
            {"section": "Bullet 2", "new": "(to be written)"},
            {"section": "Description", "new": "A blue widget."},
            {"section": "Backend Search Terms", "new": "widgit"},
        ]
        d = rs.draft_from_seo_rows(rows)
        self.assertEqual(d["title"], "Blue Widget")
        self.assertEqual(d["bullets"], ["Grip: Soft grip."])
        self.assertEqual(d["item_highlights"], "Travel Case · Soft Grip")
        self.assertNotIn("widgit", json.dumps(d))


class CliTest(unittest.TestCase):
    def test_cli_scores_listings_draft_and_compares(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "core.csv").write_text('"","Search Terms","SV"\n"","blue widget","1000"\n"","travel case","200"\n')
            (root / "listings.json").write_text(json.dumps({"listings": [
                {"asin": "TESTASIN01", "title": "Blue Widget", "bullets": ["With travel case"], "description": ""},
                {"asin": "TESTASIN02", "title": "Widget", "bullets": [], "description": "blue widget"},
            ]}))
            (root / "seo.json").write_text(json.dumps({"rows": [
                {"section": "Title", "new": "Blue Widget"},
                {"section": "Item Highlights", "new": "Travel Case"},
            ]}))
            (root / "dd.json").write_text(json.dumps({"competitors": [
                {"asin": "TESTASIN01", "listing": {"rankingJuice": 3400, "title": {"rankingJuice": 1000},
                                                   "bullets": {"rankingJuice": 200}, "description": {"rankingJuice": 0}}},
            ]}))
            base = [sys.executable, str(TOOL_DIR / "ranking_score.py"), "--keywords", str(root / "core.csv"),
                    "--listing", str(root / "listings.json"), "--seo-content", str(root / "seo.json"),
                    "--compare-datadive", str(root / "dd.json")]
            table = subprocess.run(base, capture_output=True, text=True)
            self.assertEqual(table.returncode, 0, table.stderr)
            self.assertIn("Draft", table.stdout)
            self.assertIn("Ours vs DataDive", table.stdout)
            out = subprocess.run(base + ["--json"], capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            data = json.loads(out.stdout)
            by_name = {r["name"]: r for r in data["rows"]}
            self.assertEqual(by_name["TESTASIN01"]["total"], 3 * 1000 + 2 * 200)
            self.assertEqual(by_name["Draft"]["total"], 3 * 1200)
            self.assertEqual(by_name["TESTASIN02"]["total"], 1000)
            self.assertEqual(data["datadive_comparison"]["rows"][0]["ratio_total"], 1.0)


class BuilderRowTest(unittest.TestCase):
    CFG = {"product_anchor": {"asin": "TESTANCHOR"}}

    def _inputs(self, root: Path) -> tuple[list, str, str]:
        master = [["Search Terms", "SV"], ["blue widget", "1000"], ["travel case", "200"]]
        seo = root / "seo.json"
        seo.write_text(json.dumps({"rows": [
            {"section": "Title (≤75 characters)", "new": "Example Brand Blue Widget"},
            {"section": "Item Highlights", "new": "Travel Case · Soft Grip"},
            {"section": "Bullet 1", "new": "Grip: Soft grip."},
        ]}))
        listing = root / "listing.json"
        listing.write_text(json.dumps({"listings": [
            {"asin": "TESTANCHOR", "title": "Blue Widget Travel Case", "bullets": []},
            {"asin": "TESTCOMP01", "title": "Widget", "bullets": ["blue"]},
            {"asin": "TESTCOMP02", "title": "Blue Widget", "bullets": []},
        ]}))
        return master, str(seo), str(listing)

    def test_row_is_appended_with_label_and_no_proprietary_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            warnings: list[str] = []
            result = compute_ranking_scores(self.CFG, master, seo, listing, warnings)
            self.assertEqual(result["draft"]["total"], 3 * 1200)
            self.assertEqual([c["asin"] for c in result["competitors"]], ["TESTCOMP02", "TESTCOMP01"])

            wb = Workbook()
            ws = wb.active
            ws.title = "4.1 SEO Text"
            ws.append(["Section", "Old Listing", "New Listing", "Notes / Compliance"])
            ws.append(["Title (≤75 characters)", "", "Example Brand Blue Widget", ""])
            r = append_ranking_score_row(ws, result)
            self.assertEqual(r, 3)
            cells = [ws.cell(r, c).value or "" for c in range(1, 5)]
            self.assertEqual(cells[0], RANKING_SCORE_LABEL)
            self.assertIn("3,600", cells[2])
            self.assertLess(cells[2].index("TESTCOMP02"), cells[2].index("TESTCOMP01"))
            self.assertNotIn("TESTANCHOR", cells[2])
            for text in cells:
                self.assertNotIn("ranking juice", text.lower())
                self.assertNotIn(" — ", text)
            self.assertIn("Backend search terms not scored", cells[3])
            self.assertIn("Item Highlights counted with the title", cells[3])

            checks = ranking_score_checks(result, warnings)
            self.assertEqual([c["check"] for c in checks], ["Keyword ranking score computed"])
            self.assertTrue(checks[0]["pass"])
            self.assertFalse(any("below the competitor median" in w for w in warnings))

    def test_warning_when_draft_trails_competitor_median(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            Path(seo).write_text(json.dumps({"rows": [{"section": "Title", "new": "Example Brand"}]}))
            warnings: list[str] = []
            result = compute_ranking_scores(self.CFG, master, seo, listing, warnings)
            checks = ranking_score_checks(result, warnings)
            self.assertTrue(checks[0]["pass"])
            self.assertTrue(any("below the competitor median" in w for w in warnings))

    def test_missing_draft_copy_is_informational_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            Path(seo).write_text(json.dumps({"rows": [{"section": "Title", "new": "(to be written)"}]}))
            warnings: list[str] = []
            result = compute_ranking_scores(self.CFG, master, seo, listing, warnings)
            self.assertFalse(result["computed"])
            checks = ranking_score_checks(result, warnings)
            self.assertTrue(checks[0]["pass"])
            self.assertIn("not computed: no draft copy", checks[0]["detail"])
            self.assertIn("Draft: not scored", ranking_score_row(result)[2])

    def test_mkl_without_sv_is_informational_not_a_failure(self):
        warnings: list[str] = []
        result = compute_ranking_scores(
            self.CFG, [["Keyword Phrase"], ["blue widget"]], "/nonexistent", "", warnings)
        checks = ranking_score_checks(result, warnings)
        self.assertTrue(checks[0]["pass"])
        self.assertIn("no keywords with SV", checks[0]["detail"])
        self.assertTrue(any("no keywords with SV" in w for w in warnings))

    def test_invalid_weights_fall_back_with_a_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            cfg = {**self.CFG, "ranking_score": {"weights": {"title": "x"}}}
            warnings: list[str] = []
            result = compute_ranking_scores(cfg, master, seo, listing, warnings)
            self.assertEqual(result["weights"], rs.DEFAULT_WEIGHTS)
            self.assertEqual(result["draft"]["total"], 3 * 1200)
            self.assertTrue(any("ranking_score.weights" in w for w in warnings))

    def test_disabled_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            cfg = {**self.CFG, "ranking_score": {"enabled": False}}
            warnings: list[str] = []
            result = compute_ranking_scores(cfg, master, seo, listing, warnings)
            self.assertFalse(result["enabled"])
            self.assertNotIn("draft", result)
            self.assertEqual(ranking_score_checks(result, warnings), [])
            self.assertEqual(warnings, [])

    def test_row_formatting_uses_configured_weights(self):
        with tempfile.TemporaryDirectory() as tmp:
            master, seo, listing = self._inputs(Path(tmp))
            cfg = {**self.CFG, "ranking_score": {"weights": {"title": 2}, "item_highlights_field": "bullets"}}
            result = compute_ranking_scores(cfg, master, seo, listing, [])
            row = ranking_score_row(result)
            self.assertIn("title x2 + bullets x2 + description x1", row[3])
            self.assertIn("Item Highlights counted with the bullets", row[3])
            self.assertEqual(result["draft"]["total"], 2 * 1000 + 2 * 200)


if __name__ == "__main__":
    unittest.main()
