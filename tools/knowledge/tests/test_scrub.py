from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import scrub  # noqa: E402

# Planted tokens are assembled at runtime so this file holds no literal match.
PLANTED = {
    "slack_id": "U2" + "TESTTEST1",
    "slack_permalink": "https://team.slack" + ".com/archives/" + "C0" + "1/p1",
    "slack_link": "https://app.slack" + ".com/client/" + "T0" + "1/C0" + "1",
    "asin": "B0" + "ABCDEFGH",
    "fnsku": "X0" + "ABCDEFGH",
    "shipment_id": "FBA" + "15ABCDEFG",
    "order_id": "123-" + "4567890-" + "1234567",
    "case_id": "Case " + "ID: " + "1234567890",
    "ean_upc": "4000" + "000000000",
    "price": "$" + "19.99",
    "merchant_token": "A" + "3ABCDEFGHIJK1",
    "amzn1": "amzn1" + ".account.abc",
    "mons_sel": "mons_sel" + "_dir_mcid",
    "email": "someone" + "@" + "mail.test",
    "drive_link": "https://docs.google" + ".com/document/d/abc",
    "notion_link": "https://acme.notion" + ".site/page-abc",
    "zoom_link": "https://acme.zoom" + ".us/j/123",
    "cap_link": "https://cap" + ".so/s/abc",
    "personal_path": "/Users" + "/someone/Desktop/file.txt",
    "ip_or_home_path": "/home" + "/someone/project/file.txt",
}


class PatternTests(unittest.TestCase):
    def test_every_pattern_class_has_a_planted_token(self) -> None:
        self.assertEqual(set(PLANTED), set(scrub.PATTERNS))

    def test_each_pattern_hits_its_planted_token(self) -> None:
        for name, token in PLANTED.items():
            with self.subTest(pattern=name):
                text = f"intro line\nsee {token} here\n"
                hits = [h for h in scrub.find_hits(text) if h.pattern == name]
                self.assertEqual(len(hits), 1, scrub.find_hits(text))
                self.assertEqual(hits[0].line_no, 2)
                self.assertEqual(hits[0].context, f"see {token} here")
                self.assertIn(hits[0].match, token)

    def test_clean_text_has_no_hits(self) -> None:
        text = "The listing shows Suppressed in Manage All Inventory.\nCheck FBA_INB_0008 and retry.\n"
        self.assertEqual(scrub.find_hits(text), [])

    def test_case_id_needs_nine_digits(self) -> None:
        self.assertEqual(scrub.find_hits("case " + "12345678"), [])
        self.assertEqual(len(scrub.find_hits("case #" + "123456789")), 1)

    def test_case_id_label_variants(self) -> None:
        for text in ("case_id " + "123456789", "Case number: " + "123456789", "case-no. " + "123456789", "CASE#" + "123456789"):
            with self.subTest(text=text):
                self.assertEqual([h.pattern for h in scrub.find_hits(text)], ["case_id"])

    def test_slack_id_second_character_any_digit(self) -> None:
        for token in ("U0" + "ABCDE1234", "C9" + "ABCDE1234", "W1" + "TESTTEST"):
            with self.subTest(token=token):
                self.assertEqual([h.pattern for h in scrub.find_hits(f"by {token}")], ["slack_id"])
        self.assertEqual(scrub.find_hits("CONTRACTOR DOWNLOADS GUIDELINES"), [])
        # Amazon help page IDs are a letter plus digits only.
        self.assertEqual(scrub.find_hits("help page " + "G201074410"), [])

    def test_slack_archive_link_hits_both_slack_link_classes(self) -> None:
        names = {h.pattern for h in scrub.find_hits(PLANTED["slack_permalink"])}
        self.assertEqual(names, {"slack_permalink", "slack_link"})

    def test_notion_link_variants(self) -> None:
        for link in ("https://www.notion" + ".so/page", "https://app.notion" + ".com/p/abc", "https://x.notion" + ".site/p"):
            with self.subTest(link=link):
                self.assertIn("notion_link", {h.pattern for h in scrub.find_hits(link)})

    def test_asin_is_case_insensitive(self) -> None:
        self.assertEqual([h.pattern for h in scrub.find_hits("asin " + "b0abcdefgh")], ["asin"])

    def test_price_forms(self) -> None:
        for text in ("€" + "12,50", "£ " + "7", "12,50 " + "EUR", "1.99" + "USD", "300.00 " + "CHF"):
            with self.subTest(text=text):
                self.assertEqual([h.pattern for h in scrub.find_hits(f"costs {text} now")], ["price"])

    def test_merchant_token_needs_a_digit(self) -> None:
        token = "A273" + "MSLQCY3H0G"
        self.assertEqual([h.pattern for h in scrub.find_hits(f"seller {token}")], ["merchant_token"])
        self.assertEqual(scrub.find_hits("ADMINISTRATION"), [])

    def test_numbers_that_are_not_codes(self) -> None:
        for text in ("2026-10-06", "12345" + "678901", "1.5 units", "version 2.10"):
            with self.subTest(text=text):
                self.assertEqual(scrub.find_hits(f"on {text} only"), [])


class AllowlistTests(unittest.TestCase):
    def test_example_and_xxxx_placeholders_are_ignored(self) -> None:
        for token in ("B0" + "XXXXXXXX", "B0" + "EXAMPLE1", "U0" + "EXAMPLE12", "name" + "@example.com"):
            with self.subTest(token=token):
                self.assertEqual(scrub.find_hits(f"use {token}"), [])

    def test_public_marketplace_ids_are_ignored(self) -> None:
        for marketplace_id in ("A1PA6795UKMFR9", "A1F83G8C2ARO7P", "A2EUQ1WTGCTBG2", "ATVPDKIKX0DER"):
            with self.subTest(marketplace_id=marketplace_id):
                self.assertEqual(scrub.find_hits(f"marketplace {marketplace_id}"), [])


class TermTests(unittest.TestCase):
    def test_load_terms_skips_comments_blanks_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "terms.txt"
            path.write_text("# header\n\nNordwind Labs\nnordwind labs\n  Kestrel  \n# tail\n", encoding="utf-8")
            self.assertEqual(scrub.load_terms(path), ["Nordwind Labs", "Kestrel"])
            self.assertEqual(scrub.load_terms(Path(tmp) / "missing.txt"), [])

    def test_term_variants_match(self) -> None:
        terms = ["Nordwind Labs"]
        for text in ("Nordwind Labs", "nordwind-labs", "NORDWINDLABS", "nordwind_labs", "path/nordwind-labs.md"):
            with self.subTest(text=text):
                hits = scrub.find_hits(f"x {text} y", terms)
                self.assertEqual([h.pattern for h in hits], ["term:Nordwind Labs"])

    def test_hyphenated_term_matches_space_variant(self) -> None:
        hits = scrub.find_hits("see nordwind labs", ["nordwind-labs"])
        self.assertEqual(len(hits), 1)

    def test_term_respects_word_boundaries(self) -> None:
        self.assertEqual(scrub.find_hits("kestrels and akestrel", ["Kestrel"]), [])
        self.assertEqual(len(scrub.find_hits("a Kestrel.", ["kestrel"])), 1)


class RedactTests(unittest.TestCase):
    def test_redact_replaces_each_hit(self) -> None:
        asin = PLANTED["asin"]
        text = f"Ask Nordwind Labs about {asin}.\nNothing here.\n"
        out = scrub.redact(text, ["Nordwind Labs"])
        self.assertEqual(out, "Ask [REDACTED:term:Nordwind Labs] about [REDACTED:asin].\nNothing here.\n")

    def test_redact_cli_prints_redacted_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "unit.md"
            src.write_text(f"mail {PLANTED['email']} now\n", encoding="utf-8")
            terms = Path(tmp) / "terms.txt"
            terms.write_text("", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = scrub.main(["redact", str(src), "--terms", str(terms)])
            self.assertEqual(code, 0)
            self.assertEqual(buf.getvalue(), "mail [REDACTED:email] now\n")


class CheckCliTests(unittest.TestCase):
    def run_check(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = scrub.main(["check", *args])
        return code, out.getvalue(), err.getvalue()

    def test_check_reports_hits_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "unit.md"
            src.write_text(f"clean\nid {PLANTED['slack_id']}\nKestrel note\n", encoding="utf-8")
            terms = Path(tmp) / "terms.txt"
            terms.write_text("Kestrel\n", encoding="utf-8")
            code, out, _err = self.run_check(str(src), "--terms", str(terms))
            self.assertEqual(code, 1)
            self.assertEqual(
                out.splitlines(),
                [f"{src}:2: slack_id {PLANTED['slack_id']}", f"{src}:3: term:Kestrel Kestrel"],
            )

    def test_clean_file_exits_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "unit.md"
            src.write_text("clean text\n", encoding="utf-8")
            terms = Path(tmp) / "terms.txt"
            terms.write_text("Kestrel\n", encoding="utf-8")
            code, out, _err = self.run_check(str(src), "--terms", str(terms), "--strict")
            self.assertEqual((code, out), (0, ""))

    def test_missing_terms_file_fails_only_in_strict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "unit.md"
            src.write_text("clean text\n", encoding="utf-8")
            missing = str(Path(tmp) / "missing.txt")
            code, _out, err = self.run_check(str(src), "--terms", missing)
            self.assertEqual(code, 0)
            self.assertIn("terms file missing", err)
            code, _out, _err = self.run_check(str(src), "--terms", missing, "--strict")
            self.assertEqual(code, 1)

    def test_check_walks_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "a" / "b.md"
            nested.parent.mkdir()
            nested.write_text(f"{PLANTED['fnsku']}\n", encoding="utf-8")
            terms = Path(tmp) / "terms.txt"
            terms.write_text("", encoding="utf-8")
            code, out, _err = self.run_check(tmp, "--terms", str(terms))
            self.assertEqual(code, 1)
            self.assertIn("fnsku", out)


if __name__ == "__main__":
    unittest.main()
