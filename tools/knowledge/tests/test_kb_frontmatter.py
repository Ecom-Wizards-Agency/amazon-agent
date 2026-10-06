from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import kb_frontmatter as kb  # noqa: E402

TEMPLATE = REPO / "knowledge" / "TEMPLATE.md"
SCRIPT = REPO / "tools" / "knowledge" / "kb_frontmatter.py"


def fm(*lines: str) -> str:
    return "---\n" + "\n".join(lines) + "\n---\nbody\n"


class TemplateRoundTrip(unittest.TestCase):
    def test_template_parses_with_contract_keys(self) -> None:
        mapping, body, error = kb.read_unit(TEMPLATE)
        self.assertIsNone(error)
        self.assertEqual(list(mapping), kb.KEY_ORDER)
        self.assertTrue(kb.ID_RE.match(mapping["id"]))
        self.assertEqual([h for h, _ in kb.split_sections(body)], kb.SECTION_ORDER)

    def test_template_round_trip(self) -> None:
        mapping, body, error = kb.read_unit(TEMPLATE)
        self.assertIsNone(error)
        dumped = kb.dump_frontmatter(mapping)
        again, body2, error2 = kb.parse_frontmatter(dumped + body)
        self.assertIsNone(error2)
        self.assertEqual(again, mapping)
        self.assertEqual(list(again), list(mapping))
        self.assertEqual(body2, body)
        # Dumping twice is stable.
        self.assertEqual(kb.dump_frontmatter(again), dumped)

    def test_template_within_line_cap(self) -> None:
        self.assertLessEqual(len(TEMPLATE.read_text(encoding="utf-8").splitlines()), kb.LINE_CAP)


class Typing(unittest.TestCase):
    def test_lists_booleans_and_strings(self) -> None:
        text = fm(
            "a: [x, \"y z\", \"q,r\"]",
            "b: []",
            "c: true",
            "d: false",
            "e: \"true\"",
            "f: plain value # trailing comment",
            "g: \"quoted # not a comment\"  # real comment",
            "h: \"\"",
            "i: ledger:KC-0001",
            "j: [true, false]",
            "k: \"esc \\\"q\\\" back\\\\slash \\u00e9\"",
        )
        mapping, body, error = kb.parse_frontmatter(text)
        self.assertIsNone(error)
        self.assertEqual(mapping["a"], ["x", "y z", "q,r"])
        self.assertEqual(mapping["b"], [])
        self.assertIs(mapping["c"], True)
        self.assertIs(mapping["d"], False)
        self.assertEqual(mapping["e"], "true")
        self.assertEqual(mapping["f"], "plain value")
        self.assertEqual(mapping["g"], "quoted # not a comment")
        self.assertEqual(mapping["h"], "")
        self.assertEqual(mapping["i"], "ledger:KC-0001")
        self.assertEqual(mapping["j"], ["true", "false"])
        self.assertEqual(mapping["k"], 'esc "q" back\\slash \u00e9')
        self.assertEqual(list(mapping), list("abcdefghijk"))
        self.assertEqual(body, "body\n")

    def test_dump_quoting_round_trips(self) -> None:
        mapping = {
            "id": "KC-0007",
            "title": "plain",
            "surface": "x",
            "colon": "a: b",
            "hash": "a # b",
            "brackets": "[x]",
            "comma": "a, b",
            "quote": 'say "hi"',
            "spaces": "  padded ",
            "empty": "",
            "word_true": "true",
            "flag": True,
            "items": ["a", "b c", "d:e", "", "true", 'q"x'],
            "backslash": "a\\b",
            "dash": "-leading",
        }
        dumped = kb.dump_frontmatter(mapping)
        self.assertIn('title: "plain"', dumped)
        self.assertIn('surface: "x"', dumped)
        self.assertIn('colon: "a: b"', dumped)
        self.assertIn('empty: ""', dumped)
        self.assertIn("flag: true", dumped)
        self.assertIn('word_true: "true"', dumped)
        again, _body, error = kb.parse_frontmatter(dumped)
        self.assertIsNone(error)
        self.assertEqual(again, mapping)

    def test_comment_and_blank_lines_allowed(self) -> None:
        mapping, _body, error = kb.parse_frontmatter(fm("# note", "", "a: b"))
        self.assertIsNone(error)
        self.assertEqual(mapping, {"a": "b"})


class Errors(unittest.TestCase):
    def assertError(self, text: str, fragment: str, line: int | None = None) -> None:
        mapping, _body, error = kb.parse_frontmatter(text)
        self.assertIsNone(mapping)
        self.assertIsNotNone(error)
        self.assertIn(fragment, error)
        if line is not None:
            self.assertTrue(error.startswith(f"line {line}:"), error)

    def test_nested_map_indented(self) -> None:
        self.assertError(fm("a: b", "parent:", "  child: x"), "nested", 3)

    def test_nested_map_inline(self) -> None:
        self.assertError(fm("a: b: c"), "nested map", 2)

    def test_flow_map(self) -> None:
        self.assertError(fm("a: {b: c}"), "nested map", 2)

    def test_single_quotes(self) -> None:
        self.assertError(fm("a: 'x'"), "single quotes", 2)

    def test_single_quotes_in_list(self) -> None:
        self.assertError(fm("a: ['x']"), "single quotes", 2)

    def test_duplicate_key(self) -> None:
        self.assertError(fm("a: 1", "b: 2", "a: 3"), "duplicate key", 4)

    def test_unterminated_list(self) -> None:
        self.assertError(fm("a: [x, y"), "unterminated inline list", 2)

    def test_unterminated_list_quoted_item(self) -> None:
        self.assertError(fm('a: ["x", "y'), "unterminated", 2)

    def test_unterminated_string(self) -> None:
        self.assertError(fm('a: "open'), "unterminated double-quoted string", 2)

    def test_multi_line_value(self) -> None:
        self.assertError(fm("a: |", "  text"), "multi-line", 2)

    def test_block_list(self) -> None:
        self.assertError(fm("a: b", "- item"), "block list", 3)

    def test_empty_value(self) -> None:
        self.assertError(fm("a:"), "empty value", 2)

    def test_unknown_syntax(self) -> None:
        self.assertError(fm("not a key line"), "expected 'key: value'", 2)

    def test_anchor(self) -> None:
        self.assertError(fm("a: &anchor x"), "unsupported", 2)

    def test_text_after_quote(self) -> None:
        self.assertError(fm('a: "x" y'), "unexpected text", 2)

    def test_trailing_comma(self) -> None:
        self.assertError(fm("a: [x, ]"), "trailing comma", 2)

    def test_list_item_with_colon_space(self) -> None:
        self.assertError(fm("a: b", "items: [x: y, z]"), "nested map inside a list", line=3)

    def test_list_item_ending_with_colon(self) -> None:
        self.assertError(fm("items: [ok, x:]"), "nested map inside a list", line=2)

    def test_list_item_with_space_hash(self) -> None:
        self.assertError(fm("items: [x #c, y]"), "starts a comment", line=2)

    def test_bare_scalar_block_indicators(self) -> None:
        for value in ("- b", "? b", "-", "?"):
            with self.subTest(value=value):
                self.assertError(fm("a: ok", f"b: {value}"), "YAML block syntax", line=3)

    def test_bare_null_words(self) -> None:
        for value in ("~", "null", "Null", "NULL", "~ # comment"):
            with self.subTest(value=value):
                self.assertError(fm(f"a: {value}"), "YAML null", line=2)
        for item in ("~", "null"):
            with self.subTest(item=item):
                self.assertError(fm(f"items: [a, {item}]"), "YAML null", line=2)

    def test_similar_bare_values_still_parse(self) -> None:
        text = fm("a: -leading", "b: nullable", "c: [x:y, a-b, tilde~]", "d: plain # comment")
        mapping, _body, error = kb.parse_frontmatter(text)
        self.assertIsNone(error)
        self.assertEqual(mapping, {"a": "-leading", "b": "nullable", "c": ["x:y", "a-b", "tilde~"], "d": "plain"})

    def test_rejected_values_round_trip_through_dump(self) -> None:
        mapping = {
            "tilde": "~",
            "null_word": "null",
            "dash": "- b",
            "question": "? b",
            "items": ["x: y", "x:", "x #c", "~", "null", "- b"],
        }
        dumped = kb.dump_frontmatter(mapping)
        self.assertIn('tilde: "~"', dumped)
        self.assertIn('null_word: "null"', dumped)
        again, _body, error = kb.parse_frontmatter(dumped)
        self.assertIsNone(error)
        self.assertEqual(again, mapping)

    def test_missing_opening(self) -> None:
        self.assertError("a: b\n", "missing opening")

    def test_missing_closing(self) -> None:
        self.assertError("---\na: b\n", "no closing")


class Sections(unittest.TestCase):
    def test_split_sections(self) -> None:
        body = (
            "\npreamble ignored\n\n## Question\n\nWhat?\n\n## Answer\n\nLine one.\n### Sub\nLine two.\n"
            "\n```\n## not a heading\n```\n\n## Gaps\n\nNone known.\n"
        )
        sections = kb.split_sections(body)
        self.assertEqual([h for h, _ in sections], ["Question", "Answer", "Gaps"])
        self.assertEqual(sections[0][1], "What?")
        self.assertIn("### Sub", sections[1][1])
        self.assertIn("## not a heading", sections[1][1])
        self.assertEqual(sections[2][1], "None known.")

    def test_no_sections(self) -> None:
        self.assertEqual(kb.split_sections("just text\n"), [])


class Cli(unittest.TestCase):
    def test_cli_prints_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(TEMPLATE)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["id"], "KC-0000")

    def test_cli_error_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_text(fm("a: 'x'"), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(bad)], capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("line 2", result.stderr)


if __name__ == "__main__":
    unittest.main()
