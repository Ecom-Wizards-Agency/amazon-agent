from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import ledger  # noqa: E402

PREFIX = "---\ntype: reference\n---\n\n# Knowledge ledger\n\nOne row per source thread.\n\n"
SUFFIX = "\n## Notes\n\nKeep  this   spacing.\n| not a ledger row, after a blank line |\n"


def row(kb_id: str, parent_ts: str, **extra: str) -> dict:
    base = {col: "" for col in ledger.LEDGER_COLUMNS}
    base.update({"kb_id": kb_id, "parent_ts": parent_ts, "client_slug": "brandx", "notes": "n"})
    base.update(extra)
    return base


def ledger_text(*rows: dict) -> str:
    body = ledger.header_text() + "".join(ledger.render_row(r) + "\n" for r in rows)
    return PREFIX + body + SUFFIX


class LedgerFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.vault = base / "vault"
        (self.vault / "Clients").mkdir(parents=True)
        (self.vault / "Runs").mkdir()
        self.ledger_path = self.vault / "Runs" / "amazon-knowledge-ledger.md"
        self.root = base / "repo"
        (self.root / "knowledge" / "_index").mkdir(parents=True)
        self.staging = self.root / "_local" / "knowledge-sweep" / "ledger-staging.md"
        self.staging.parent.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_index(self, units: list[tuple[str, str]]) -> None:
        data = {"units": [{"id": uid, "status": status} for uid, status in units]}
        (self.root / "knowledge" / "_index" / "knowledge-index.json").write_text(json.dumps(data), encoding="utf-8")

    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ledger.main(["--vault", str(self.vault), "--root", str(self.root), *args])
        return code, out.getvalue()


class ParseTests(LedgerFixture):
    def test_parse_rows_and_tolerate_prose(self) -> None:
        raw = "| KC-0002 | brandx |  | 2.2 |  |  |  |  |  |  |  |  |  | a\\|b |\n"
        text = ledger_text(row("KC-0001", "1.1")).replace(SUFFIX, raw + SUFFIX)
        table = ledger.parse_table(text)
        self.assertTrue(table.found)
        self.assertEqual([r["kb_id"] for r in table.rows], ["KC-0001", "KC-0002"])
        self.assertEqual(table.rows[0]["client_slug"], "brandx")
        self.assertEqual(table.rows[1]["notes"], "a\\|b")
        self.assertEqual(list(table.rows[0]), ledger.LEDGER_COLUMNS)

    def test_no_table(self) -> None:
        self.assertFalse(ledger.parse_table(PREFIX + "no table\n").found)
        self.assertEqual(ledger.parse_table(PREFIX).rows, [])

    def test_short_row_is_padded(self) -> None:
        text = ledger.header_text() + "| KC-0003 | slug |\n"
        self.assertEqual(ledger.parse_table(text).rows[0]["notes"], "")

    def test_render_replaces_pipes_and_newlines(self) -> None:
        line = ledger.render_row(row("KC-0001", "1", notes="a|b\nc"))
        self.assertTrue(line.endswith("| a/b c |"))
        self.assertEqual(line.count("|"), len(ledger.LEDGER_COLUMNS) + 1)


class CheckTests(LedgerFixture):
    def test_mismatches_both_ways(self) -> None:
        self.write_index([("KC-0001", "draft"), ("KC-0002", "reviewed"), ("KC-0003", "retired")])
        self.ledger_path.write_text(ledger_text(row("KC-0001", "1"), row("KC-0003", "3"), row("KC-0099", "9")), encoding="utf-8")
        code, out = self.run_main("check")
        self.assertEqual(code, 1)
        self.assertIn("unit without ledger row: KC-0002", out)
        self.assertIn("ledger row without unit: KC-0099", out)
        self.assertNotIn("KC-0001", out)
        self.assertNotIn("KC-0003", out)

    def test_retired_unit_needs_no_row(self) -> None:
        self.write_index([("KC-0001", "draft"), ("KC-0002", "retired")])
        self.ledger_path.write_text(ledger_text(row("KC-0001", "1")), encoding="utf-8")
        code, out = self.run_main("check")
        self.assertEqual(code, 0, out)
        self.assertIn("ok", out)

    def test_check_function(self) -> None:
        missing, unknown = ledger.check(ledger_text(row("KC-0005", "5")), {"KC-0001"}, {"KC-0001"})
        self.assertEqual(missing, ["KC-0001"])
        self.assertEqual(unknown, ["KC-0005"])

    def test_no_vault_skips(self) -> None:
        out = io.StringIO()
        with mock.patch.object(ledger, "resolve_vault", return_value=None), contextlib.redirect_stdout(out):
            code = ledger.main(["--root", str(self.root), "check"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), "ledger: no team vault on this machine, skipped")

    def test_missing_ledger_file_fails_with_units(self) -> None:
        self.write_index([("KC-0001", "draft")])
        code, out = self.run_main("check")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", out)


class AppendTests(LedgerFixture):
    def test_append_dedupes_and_truncates_staging(self) -> None:
        original = ledger_text(row("KC-0001", "1.1"))
        self.ledger_path.write_text(original, encoding="utf-8")
        staged = ledger.header_text() + "".join(
            ledger.render_row(r) + "\n"
            for r in [row("KC-0001", "1.1"), row("KC-0001", "1.2"), row("KC-0002", "2.1"), row("KC-0002", "2.1")]
        )
        self.staging.write_text(staged, encoding="utf-8")
        code, out = self.run_main("append", "--from-staging")
        self.assertEqual(code, 0, out)
        self.assertIn("appended 2, skipped 2", out)
        self.assertEqual(self.staging.read_text(encoding="utf-8"), ledger.header_text())
        new_text = self.ledger_path.read_text(encoding="utf-8")
        keys = [ledger.row_key(r) for r in ledger.parse_table(new_text).rows]
        self.assertEqual(keys, [("KC-0001", "1.1"), ("KC-0001", "1.2"), ("KC-0002", "2.1")])

        code, out = self.run_main("append", "--from-staging")
        self.assertEqual(code, 0)
        self.assertIn("appended 0, skipped 0", out)

    def test_text_outside_table_preserved(self) -> None:
        original = ledger_text(row("KC-0001", "1.1"))
        self.ledger_path.write_text(original, encoding="utf-8")
        self.staging.write_text(ledger.header_text() + ledger.render_row(row("KC-0002", "2")) + "\n", encoding="utf-8")
        code, _out = self.run_main("append", "--from-staging")
        self.assertEqual(code, 0)
        new_text = self.ledger_path.read_text(encoding="utf-8")
        added = ledger.render_row(row("KC-0002", "2")) + "\n"
        self.assertEqual(new_text, original.replace(SUFFIX, added + SUFFIX))
        self.assertTrue(new_text.startswith(PREFIX))
        self.assertTrue(new_text.endswith(SUFFIX))

    def test_crlf_and_no_trailing_newline_preserved(self) -> None:
        head = "---\r\ntype: reference\r\n---\r\n\r\n"
        table = ledger.header_text("\r\n") + ledger.render_row(row("KC-0001", "1"))
        self.ledger_path.write_bytes((head + table).encode("utf-8"))
        self.staging.write_text(ledger.header_text() + ledger.render_row(row("KC-0002", "2")) + "\n", encoding="utf-8")
        code, _out = self.run_main("append", "--from-staging")
        self.assertEqual(code, 0)
        data = self.ledger_path.read_bytes().decode("utf-8")
        self.assertTrue(data.startswith(head + table + "\r\n"))
        self.assertTrue(data.endswith(ledger.render_row(row("KC-0002", "2")) + "\r\n"))

    def test_refuses_when_ledger_missing(self) -> None:
        self.staging.write_text(ledger.header_text() + ledger.render_row(row("KC-0002", "2")) + "\n", encoding="utf-8")
        code, out = self.run_main("append", "--from-staging")
        self.assertEqual(code, 1)
        self.assertIn("Create it first", out)
        self.assertIn("| kb_id | client_slug |", out)
        self.assertFalse(self.ledger_path.exists())
        self.assertIn("KC-0002", self.staging.read_text(encoding="utf-8"))

    def test_append_refused_in_unattended_mode(self) -> None:
        original = ledger_text(row("KC-0001", "1"))
        self.ledger_path.write_text(original, encoding="utf-8")
        staged = ledger.header_text() + ledger.render_row(row("KC-0002", "2")) + "\n"
        self.staging.write_text(staged, encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict("os.environ", {"WIZARDS_AI_MODE": "1"}):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = ledger.main(["--vault", str(self.vault), "--root", str(self.root), "append", "--from-staging"])
            self.assertEqual(code, 2)
            self.assertIn("attended only", err.getvalue())
            self.assertIn("WIZARDS_AI_MODE=1", err.getvalue())
            self.assertEqual(self.ledger_path.read_text(encoding="utf-8"), original)
            self.assertEqual(self.staging.read_text(encoding="utf-8"), staged)
            # Read-only commands still run unattended.
            self.write_index([("KC-0001", "draft")])
            code, _out = self.run_main("check")
            self.assertEqual(code, 0)
        with mock.patch.dict("os.environ", {"WIZARDS_AI_MODE": "0"}):
            code, out_text = self.run_main("append", "--from-staging")
        self.assertEqual(code, 0, out_text)
        self.assertIn("appended 1, skipped 0", out_text)

    def test_explicit_staging_path(self) -> None:
        self.ledger_path.write_text(ledger_text(), encoding="utf-8")
        other = self.root / "other-staging.md"
        other.write_text(ledger.header_text() + ledger.render_row(row("KC-0004", "4")) + "\n", encoding="utf-8")
        code, out = self.run_main("append", "--from-staging", "--staging", str(other))
        self.assertEqual(code, 0)
        self.assertIn("appended 1, skipped 0", out)


class ShowTests(LedgerFixture):
    def test_show(self) -> None:
        self.ledger_path.write_text(ledger_text(row("KC-0001", "1"), row("KC-0002", "2"), row("KC-0001", "3")), encoding="utf-8")
        code, out = self.run_main("show", "KC-0001")
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 4)
        self.assertNotIn("KC-0002", out)
        code, out = self.run_main("show", "KC-0050")
        self.assertEqual(code, 1)
        self.assertIn("no rows", out)


if __name__ == "__main__":
    unittest.main()
