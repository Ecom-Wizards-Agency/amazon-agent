#!/usr/bin/env python3
"""Find and redact client-identifying tokens in knowledge text.

Two layers:

- PATTERNS: regex classes for IDs, EAN/UPC codes, prices, links and machine
  paths. Always on.
- A denylist of terms (client, brand, person and partner names), one per
  line in the gitignored `_local/knowledge-redaction-terms.txt`. Seeded by
  `tools/knowledge/seed_redaction_terms.py`, extended by hand.

Stdlib only, because Grimoire runs on the PATH python3 without PyYAML.

Usage:
  python3 tools/knowledge/scrub.py check <paths...> [--terms FILE] [--strict]
  python3 tools/knowledge/scrub.py redact <path> [--terms FILE]

`check` prints `<path>:<line>: <pattern> <match>` per hit and exits 1 on any
hit. `--strict` also exits 1 when the terms file is missing. Directories are
walked for text files. `redact` prints the text with each hit replaced by
`[REDACTED:<pattern>]`.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import NamedTuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TERMS_PATH = WORKSPACE_ROOT / "_local" / "knowledge-redaction-terms.txt"

# Ordered: when two classes match the same span, the earlier one names the hit
# in redact output. Add a class by adding a line.
PATTERNS: "OrderedDict[str, re.Pattern[str]]" = OrderedDict(
    [
        # The second character is a digit, so all-caps words never match, and at
        # least one letter follows, so Amazon help page IDs (G201074410) pass.
        ("slack_id", re.compile(r"\b[UCDGW](?=[0-9]*[A-Z])[0-9][A-Z0-9]{7,10}\b")),
        ("slack_permalink", re.compile(r"slack\.com/archives/")),
        ("slack_link", re.compile(r"slack\.com/(?:archives|client)/")),
        ("asin", re.compile(r"\bB0[A-Z0-9]{8}\b", re.IGNORECASE)),
        ("fnsku", re.compile(r"\bX0[A-Z0-9]{8}\b")),
        ("shipment_id", re.compile(r"\bFBA[0-9A-Z]{9}\b")),
        ("order_id", re.compile(r"\b\d{3}-\d{7}-\d{7}\b")),
        ("case_id", re.compile(r"\bcase[\s_-]*(?:id|number|no\.?)?[:#]?\s*\d{9,12}\b", re.IGNORECASE)),
        ("ean_upc", re.compile(r"\b\d{12,14}\b")),
        ("price", re.compile(r"[$€£]\s?\d[\d.,]*|\b\d+[.,]\d{2}\s?(?:EUR|USD|GBP|CHF|PLN|SEK)\b")),
        # At least one digit after the leading A, so words like ADMINISTRATION pass.
        ("merchant_token", re.compile(r"\bA(?=[A-Z]*[0-9])[0-9A-Z]{12,13}\b")),
        ("amzn1", re.compile(r"amzn1\.[a-z.]+")),
        ("mons_sel", re.compile(r"mons_sel_[a-z_]+")),
        ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")),
        ("drive_link", re.compile(r"docs\.google\.com|drive\.google\.com")),
        ("notion_link", re.compile(r"notion\.(?:so|site)|app\.notion\.com")),
        ("zoom_link", re.compile(r"zoom\.us/")),
        ("cap_link", re.compile(r"cap\.so/")),
        ("personal_path", re.compile(r"/Users/[A-Za-z0-9._-]+/")),
        # A path under /home leaks the operator's machine and user name.
        ("ip_or_home_path", re.compile(r"/home/[a-z0-9._-]+/")),
    ]
)

# A regex match containing one of these markers is a placeholder, not a leak.
ALLOW_MARKERS = ("EXAMPLE", "XXXX")

# Public Amazon marketplace IDs. They identify a country, not a seller.
PUBLIC_MARKETPLACE_IDS = frozenset(
    {
        "A1PA6795UKMFR9",
        "ATVPDKIKX0DER",
        "A1F83G8C2ARO7P",
        "A13V1IB3VIYZZH",
        "APJ6JRA9NG5V4",
        "A1RKKUPIHCS9HS",
        "A1805IZSGTT6HH",
        "A2NODRKZP88ZB9",
        "A1C3SOZRARQ6R3",
        "A39IBJ37TRP1C6",
        "A1VC38T7YXB528",
        "A2EUQ1WTGCTBG2",
        "A1AM78C64UM0Y8",
        # Not in the original brief. A1805IZSGTT6HS is the documented NL ID
        # (the brief listed A1805IZSGTT6HH); the rest are the other public
        # marketplaces: BR, BE, TR, AE, SA, EG, IN, SG, IE, ZA.
        "A1805IZSGTT6HS",
        "A2Q3Y263D00KWC",
        "AMEN7PMS3EDWL",
        "A33AVAJ2PDY3EV",
        "A2VIGQ35RCS4UG",
        "A17E79C6D8DWNP",
        "ARBP9OOSHTCHU",
        "A21TJRUUN4KGV",
        "A19VAU5U5O7RUS",
        "A28R8C7NBKEWEA",
        "AE08WJ6YKNBMC",
    }
)
ALLOWLIST = PUBLIC_MARKETPLACE_IDS

# Characters that separate the words of a multi-word term in its variants.
_TERM_SPLIT = re.compile(r"[\s\-_]+")
# Between the words of a term: nothing, one space, hyphen or underscore.
_TERM_JOIN = r"[ \t\-_]?"
# A term must not touch a letter or digit on either side. Underscores and
# punctuation count as boundaries, so `client_term` and `term.md` still hit.
_TERM_BEFORE = r"(?<![^\W_])"
_TERM_AFTER = r"(?![^\W_])"


class Hit(NamedTuple):
    pattern: str
    match: str
    line_no: int
    context: str
    start: int = -1
    end: int = -1


def is_allowed(match: str) -> bool:
    """True when a regex match is a placeholder or a public marketplace ID."""
    upper = match.upper()
    if any(marker in upper for marker in ALLOW_MARKERS):
        return True
    return match in ALLOWLIST


def load_terms(path: str | Path) -> list[str]:
    """Read a denylist: one term per line, `#` comments and blanks ignored.

    Deduplicated case-insensitively, first spelling kept, file order kept.
    A missing file returns an empty list.
    """
    path = Path(path)
    if not path.is_file():
        return []
    seen: set[str] = set()
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        term = line.strip()
        if not term or term.startswith("#"):
            continue
        key = term.casefold()
        if key in seen:
            continue
        seen.add(key)
        terms.append(term)
    return terms


def term_regex(term: str) -> re.Pattern[str] | None:
    """Compile a case-insensitive, boundary-anchored regex for one term.

    `Nordwind Labs` also matches `nordwind-labs`, `nordwind_labs` and
    `nordwindlabs`.
    """
    parts = [p for p in _TERM_SPLIT.split(term.strip()) if p]
    if not parts:
        return None
    body = _TERM_JOIN.join(re.escape(part) for part in parts)
    return re.compile(_TERM_BEFORE + body + _TERM_AFTER, re.IGNORECASE)


def _compiled_terms(terms: list[str] | None) -> list[tuple[str, re.Pattern[str]]]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for term in terms or []:
        regex = term_regex(term)
        if regex is not None:
            compiled.append((term, regex))
    return compiled


def find_hits(text: str, terms: list[str] | None = None) -> list[Hit]:
    """Return every regex-class and denylist hit, ordered by position.

    Denylist hits use the pattern name `term:<term>`. `start` and `end` are
    offsets into `text`.
    """
    hits: list[Hit] = []
    compiled_terms = _compiled_terms(terms)
    offset = 0
    for line_no, raw in enumerate(text.splitlines(keepends=True), start=1):
        line = raw.rstrip("\r\n")
        for name, regex in PATTERNS.items():
            for m in regex.finditer(line):
                if is_allowed(m.group(0)):
                    continue
                hits.append(Hit(name, m.group(0), line_no, line, offset + m.start(), offset + m.end()))
        for term, regex in compiled_terms:
            for m in regex.finditer(line):
                hits.append(Hit(f"term:{term}", m.group(0), line_no, line, offset + m.start(), offset + m.end()))
        offset += len(raw)
    hits.sort(key=lambda h: (h.start, -(h.end - h.start)))
    return hits


def redact(text: str, terms: list[str] | None = None) -> str:
    """Replace each hit with `[REDACTED:<pattern>]`.

    Where hits overlap, the one that starts first wins, then the longer one.
    """
    out: list[str] = []
    cursor = 0
    for hit in find_hits(text, terms):
        if hit.start < cursor:
            continue
        out.append(text[cursor : hit.start])
        out.append(f"[REDACTED:{hit.pattern}]")
        cursor = hit.end
    out.append(text[cursor:])
    return "".join(out)


def _iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(p for p in sorted(path.rglob("*")) if p.is_file())
        else:
            files.append(path)
    return files


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _terms_for(args: argparse.Namespace) -> tuple[list[str], Path, bool]:
    terms_path = Path(args.terms) if args.terms else DEFAULT_TERMS_PATH
    exists = terms_path.is_file()
    return (load_terms(terms_path) if exists else []), terms_path, exists


def cmd_check(args: argparse.Namespace) -> int:
    terms, terms_path, exists = _terms_for(args)
    status = 0
    if not exists:
        print(f"scrub: terms file missing, denylist skipped: {terms_path}", file=sys.stderr)
        if args.strict:
            status = 1
    for path in _iter_files(args.paths):
        if not path.exists():
            print(f"scrub: no such file: {path}", file=sys.stderr)
            status = 1
            continue
        text = _read_text(path)
        if text is None:
            continue
        for hit in find_hits(text, terms):
            print(f"{path}:{hit.line_no}: {hit.pattern} {hit.match}")
            status = 1
    return status


def cmd_redact(args: argparse.Namespace) -> int:
    terms, _terms_path, _exists = _terms_for(args)
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"scrub: cannot read {path}: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(redact(text, terms))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find or redact client-identifying tokens.")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="report hits, exit 1 on any")
    check.add_argument("paths", nargs="+")
    check.add_argument("--terms", help=f"denylist file (default {DEFAULT_TERMS_PATH})")
    check.add_argument("--strict", action="store_true", help="also fail when the terms file is missing")
    check.set_defaults(func=cmd_check)

    red = sub.add_parser("redact", help="print the text with hits replaced")
    red.add_argument("path")
    red.add_argument("--terms", help=f"denylist file (default {DEFAULT_TERMS_PATH})")
    red.set_defaults(func=cmd_redact)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
