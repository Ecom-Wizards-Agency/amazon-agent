#!/usr/bin/env python3
"""Cross-check and extend the private knowledge ledger in the team vault.

The ledger is `<vault>/Runs/amazon-knowledge-ledger.md`: frontmatter
(`type: reference`), optional prose, and one markdown table with the columns in
LEDGER_COLUMNS. One row per source thread, joined to a unit by `kb_id`.

Commands:
  check                      every active unit in the index has a row and every
                             row names a unit in the index; exit 1 on mismatch.
                             Without a team vault on this machine it skips, exit 0.
  append --from-staging      move rows from the gitignored staging file
                             (_local/knowledge-sweep/ledger-staging.md) into the
                             ledger, skipping (kb_id, parent_ts) pairs already
                             present, then truncate the staging file to its header.
                             Attended only: refused with exit 2 when
                             WIZARDS_AI_MODE=1 (the unattended bot flag).
  show KC-NNNN               print the ledger rows for one unit.

Text outside the table is preserved byte for byte. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from ads_recall import resolve_vault  # noqa: E402

WORKSPACE_ROOT = HERE.parents[1]
LEDGER_REL = Path("Runs") / "amazon-knowledge-ledger.md"
INDEX_REL = Path("knowledge") / "_index" / "knowledge-index.json"
STAGING_REL = Path("_local") / "knowledge-sweep" / "ledger-staging.md"

LEDGER_COLUMNS = [
    "kb_id",
    "client_slug",
    "channel",
    "parent_ts",
    "permalink",
    "first_seen",
    "resolved_on",
    "resolution_status",
    "who_diagnosed",
    "who_executed",
    "fix_source",
    "evidence_location",
    "identifiers",
    "notes",
]

_CELL_SPLIT = re.compile(r"(?<!\\)\|")
_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


def header_text(newline: str = "\n") -> str:
    """Return the table header and separator lines, newline-terminated."""
    head = "| " + " | ".join(LEDGER_COLUMNS) + " |"
    sep = "|" + "|".join("---" for _ in LEDGER_COLUMNS) + "|"
    return head + newline + sep + newline


def clean_cell(value: object) -> str:
    """Make a value safe for one table cell: no pipes, no line breaks."""
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(item) for item in value)
    text = str(value).replace("|", "/")
    text = re.sub(r"[\r\n]+", " ", text)
    return text.strip()


def render_row(row: dict) -> str:
    """Render a row dict as one table line without a trailing newline."""
    return "| " + " | ".join(clean_cell(row.get(col, "")) for col in LEDGER_COLUMNS) + " |"


def split_cells(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.strip() for cell in _CELL_SPLIT.split(text)]


def _is_table_line(line: str) -> bool:
    return line.lstrip().startswith("|")


def _is_header(line: str) -> bool:
    return _is_table_line(line) and split_cells(line) == LEDGER_COLUMNS


def _is_separator(line: str) -> bool:
    if not _is_table_line(line):
        return False
    cells = split_cells(line)
    return bool(cells) and all(_SEPARATOR_CELL.match(cell) for cell in cells)


@dataclass
class Table:
    """A parsed ledger file. `lines` keep their own line endings."""

    lines: list[str]
    header_at: int | None = None
    end: int = 0  # index just past the last table line
    rows: list[dict] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.header_at is not None

    def newline(self) -> str:
        if self.header_at is not None:
            line = self.lines[self.header_at]
            if line.endswith("\r\n"):
                return "\r\n"
        return "\n"


def parse_table(text: str) -> Table:
    """Find the ledger table (header with LEDGER_COLUMNS, then a separator)."""
    lines = text.splitlines(keepends=True)
    table = Table(lines=lines)
    for idx, line in enumerate(lines):
        if _is_header(line) and idx + 1 < len(lines) and _is_separator(lines[idx + 1]):
            table.header_at = idx
            pos = idx + 2
            while pos < len(lines) and _is_table_line(lines[pos]):
                cells = split_cells(lines[pos])
                cells = (cells + [""] * len(LEDGER_COLUMNS))[: len(LEDGER_COLUMNS)]
                table.rows.append(dict(zip(LEDGER_COLUMNS, cells)))
                pos += 1
            table.end = pos
            break
    return table


def append_rows(text: str, rows: list[dict]) -> str:
    """Return text with rows inserted after the table's last line."""
    table = parse_table(text)
    if not table.found:
        raise ValueError("no ledger table header found")
    nl = table.newline()
    before = table.lines[: table.end]
    after = table.lines[table.end :]
    if before and not before[-1].endswith(("\n", "\r")):
        before[-1] = before[-1] + nl
    added = [render_row(row) + nl for row in rows]
    return "".join(before + added + after)


def read_raw(path: Path) -> str:
    """Read a file without newline translation, so CRLF survives a rewrite."""
    return path.read_bytes().decode("utf-8")


def row_key(row: dict) -> tuple[str, str]:
    return (row.get("kb_id", "").strip(), row.get("parent_ts", "").strip())


def load_index_ids(root: Path) -> tuple[set[str], set[str]] | None:
    """Return (active ids, all ids) from the index, or None when it is missing."""
    path = root / INDEX_REL
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    units = data.get("units", [])
    all_ids = {str(u.get("id", "")) for u in units if u.get("id")}
    active = {str(u.get("id", "")) for u in units if u.get("id") and u.get("status") != "retired"}
    return active, all_ids


def check(ledger_text: str, active: set[str], all_ids: set[str]) -> tuple[list[str], list[str]]:
    """Return (active units without a row, row kb_ids not in the index)."""
    rows = parse_table(ledger_text).rows
    row_ids = {row.get("kb_id", "").strip() for row in rows}
    row_ids.discard("")
    missing_rows = sorted(active - row_ids)
    unknown_ids = sorted(row_ids - all_ids)
    return missing_rows, unknown_ids


def append_from_staging(ledger_path: Path, staging_path: Path) -> tuple[int, int]:
    """Move staged rows into the ledger. Return (appended, skipped)."""
    ledger_text = read_raw(ledger_path)
    table = parse_table(ledger_text)
    if not table.found:
        raise ValueError(f"{ledger_path}: no ledger table header found")
    staged = parse_table(staging_path.read_text(encoding="utf-8")).rows
    seen = {row_key(row) for row in table.rows}
    new_rows: list[dict] = []
    skipped = 0
    for row in staged:
        key = row_key(row)
        if not key[0] or key in seen:
            skipped += 1
            continue
        seen.add(key)
        new_rows.append(row)
    if new_rows:
        ledger_path.write_text(append_rows(ledger_text, new_rows), encoding="utf-8", newline="")
    staging_path.write_text(header_text(), encoding="utf-8")
    return len(new_rows), skipped


def _missing_ledger_message(path: Path) -> str:
    return (
        f"ledger: {path} does not exist. Create it first with frontmatter `type: reference`"
        f" and this table header:\n{header_text()}"
    )


def unattended() -> bool:
    """True in a Grimoire or scheduled run, which may not write the team vault ledger."""
    return os.environ.get("WIZARDS_AI_MODE", "").strip() == "1"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", help="explicit team-vault path")
    parser.add_argument("--root", default=str(WORKSPACE_ROOT), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="cross-check the ledger and the index")
    p_append = sub.add_parser("append", help="append staged rows to the ledger")
    p_append.add_argument("--from-staging", action="store_true", required=True)
    p_append.add_argument("--staging", help="staging file (default _local/knowledge-sweep/ledger-staging.md)")
    p_show = sub.add_parser("show", help="print the rows for one unit id")
    p_show.add_argument("kb_id")
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "append" and unattended():
        print(
            "ledger: append writes the team-vault ledger and is attended only;"
            " refused because WIZARDS_AI_MODE=1. Run it from an attended session.",
            file=sys.stderr,
        )
        return 2

    vault = resolve_vault(args.vault)
    if vault is None:
        print("ledger: no team vault on this machine, skipped")
        return 0
    ledger_path = vault / LEDGER_REL

    if args.command == "check":
        ids = load_index_ids(root)
        if ids is None:
            print(f"ledger: index missing at {root / INDEX_REL}; run build_knowledge_index.py first")
            return 1
        active, all_ids = ids
        if not ledger_path.is_file():
            print(f"ledger: {ledger_path} does not exist")
            for unit_id in sorted(active):
                print(f"  unit without ledger row: {unit_id}")
            return 1 if active else 0
        missing_rows, unknown_ids = check(read_raw(ledger_path), active, all_ids)
        for unit_id in missing_rows:
            print(f"  unit without ledger row: {unit_id}")
        for unit_id in unknown_ids:
            print(f"  ledger row without unit: {unit_id}")
        if missing_rows or unknown_ids:
            print(f"ledger: {len(missing_rows)} units without a row, {len(unknown_ids)} row ids without a unit")
            return 1
        print(f"ledger: ok, {len(active)} active units all have rows")
        return 0

    if args.command == "append":
        staging_path = Path(args.staging) if args.staging else root / STAGING_REL
        if not ledger_path.is_file():
            print(_missing_ledger_message(ledger_path))
            return 1
        if not staging_path.is_file():
            print(f"ledger: nothing staged, {staging_path} does not exist")
            print("appended 0, skipped 0")
            return 0
        try:
            appended, skipped = append_from_staging(ledger_path, staging_path)
        except ValueError as exc:
            print(f"ledger: {exc}")
            return 1
        print(f"appended {appended}, skipped {skipped}")
        return 0

    # show
    if not ledger_path.is_file():
        print(_missing_ledger_message(ledger_path))
        return 1
    rows = [r for r in parse_table(read_raw(ledger_path)).rows if r.get("kb_id") == args.kb_id]
    if not rows:
        print(f"ledger: no rows for {args.kb_id}")
        return 1
    print(header_text(), end="")
    for row in rows:
        print(render_row(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
