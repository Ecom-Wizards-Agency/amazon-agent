#!/usr/bin/env python3
"""Read and write the flat frontmatter subset used by knowledge units.

Stdlib only, because Grimoire runs on the PATH python3 without PyYAML.

The subset: `key: value` lines between the first two `---` lines. A value is
a bare scalar, a double-quoted string with backslash escapes, `true`/`false`,
or an inline list `[a, "b c"]` whose items are bare or double-quoted. A
trailing ` # comment` is stripped only after an unquoted value or a closed
quote or list. Blank lines and whole-line `#` comments are allowed. Nested
maps, multi-line values, single quotes, duplicate keys and any other syntax
are errors that name the line. So are bare values a YAML reader would not
read as the same string: a null (`~`, `null`), a scalar starting with `- ` or
`? `, and a list item containing `: `, ` #` or ending with `:`.

Usage: python3 tools/knowledge/kb_frontmatter.py <unit.md>
Prints the frontmatter as JSON. Exit 1 on a parse error.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

KEY_ORDER = [
    "id",
    "title",
    "kind",
    "topic",
    "status",
    "skills",
    "marketplaces",
    "marketplace_inferred",
    "surface",
    "surface_verified",
    "symptom_keywords",
    "error_text",
    "asked_as",
    "synonyms",
    "resolution_status",
    "fix_source",
    "evidence_location",
    "confidence",
    "verification",
    "verified_on",
    "verified_how",
    "amazon_sources",
    "related_sops",
    "supersedes",
    "contradicts",
    "observed",
    "review_by",
    "provenance",
]

TOPICS = [
    "compliance",
    "logistics",
    "catalog",
    "support-cases",
    "ads",
    "account-health",
    "seo",
    "brand-registry",
    "reporting",
]
KINDS = ["diagnosis", "procedure", "rule", "reference", "decision-aid"]
STATUSES = ["draft", "reviewed", "retired"]
RESOLUTION_STATUSES = ["resolved", "partial", "diagnosis-only", "unknown"]
FIX_SOURCES = ["agency", "client", "amazon-support", "first-party-doc", "unknown"]
EVIDENCE_LOCATIONS = ["slack", "screenshot", "call", "email", "case", "video", "run-note", "none"]
CONFIDENCES = ["high", "medium", "low"]
VERIFICATIONS = ["unverified", "verified"]
VERIFIED_HOWS = ["live-ui", "first-party-capture", "operator", ""]
MARKETPLACES = ["US", "CA", "MX", "DE", "UK", "FR", "IT", "ES", "NL", "SE", "PL", "AU", "JP", "all"]
SECTION_ORDER = ["Question", "Answer", "Cause", "Fix", "Verify", "Stop before", "Sources", "Gaps"]

ID_RE = re.compile(r"^KC-[0-9]{4}$")
LINE_CAP = 90

# Keys whose values the dumper always quotes.
ALWAYS_QUOTED = {"title", "surface"}

_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "n": "\n", "t": "\t", "r": "\r", "0": "\0"}
_QUOTE_CHARS = set(':#[]{},"\'\\')
_LEADING_SPECIAL = set("|>&*!%@`-?")
# Bare words YAML reads as null. The parser rejects them; the dumper quotes them.
_NULL_WORDS = {"~", "null", "Null", "NULL"}


class FrontmatterError(ValueError):
    """Raised inside the parser; parse_frontmatter turns it into a string."""


def _strip_comment_tail(rest: str, lineno: int, what: str) -> None:
    """After a closed quote or list only whitespace or ` # comment` may follow."""
    if not rest.strip():
        return
    if re.match(r"^\s+#", rest):
        return
    raise FrontmatterError(f"line {lineno}: unexpected text after {what}: {rest.strip()!r}")


def _parse_quoted(text: str, start: int, lineno: int) -> tuple[str, int]:
    """Parse a double-quoted string beginning at text[start] == '"'.

    Returns (value, index just past the closing quote).
    """
    out: list[str] = []
    i = start + 1
    while i < len(text):
        ch = text[i]
        if ch == "\\":
            if i + 1 >= len(text):
                break
            nxt = text[i + 1]
            if nxt in _ESCAPES:
                out.append(_ESCAPES[nxt])
                i += 2
                continue
            if nxt == "u":
                digits = text[i + 2 : i + 6]
                if len(digits) == 4 and all(c in "0123456789abcdefABCDEF" for c in digits):
                    out.append(chr(int(digits, 16)))
                    i += 6
                    continue
            raise FrontmatterError(f"line {lineno}: unknown escape \\{nxt} in quoted string")
        if ch == '"':
            return "".join(out), i + 1
        out.append(ch)
        i += 1
    raise FrontmatterError(f"line {lineno}: unterminated double-quoted string")


def _parse_list(text: str, lineno: int) -> list[str]:
    """Parse an inline list; text starts with '['."""
    items: list[str] = []
    i = 1
    n = len(text)

    def skip_ws(j: int) -> int:
        while j < n and text[j] in " \t":
            j += 1
        return j

    i = skip_ws(i)
    if i < n and text[i] == "]":
        _strip_comment_tail(text[i + 1 :], lineno, "list")
        return items
    while True:
        i = skip_ws(i)
        if i >= n:
            raise FrontmatterError(f"line {lineno}: unterminated inline list")
        ch = text[i]
        if ch == '"':
            value, i = _parse_quoted(text, i, lineno)
        elif ch == "'":
            raise FrontmatterError(f"line {lineno}: single quotes are not supported, use double quotes")
        elif ch in "[{":
            raise FrontmatterError(f"line {lineno}: nested list or map inside a list is not supported")
        elif ch in ",]":
            raise FrontmatterError(f"line {lineno}: empty list item")
        else:
            j = i
            while j < n and text[j] not in ",]":
                if text[j] in "\"'[{}":
                    raise FrontmatterError(
                        f"line {lineno}: unexpected {text[j]!r} in bare list item, quote the item"
                    )
                j += 1
            if j >= n:
                raise FrontmatterError(f"line {lineno}: unterminated inline list")
            value = text[i:j].strip()
            _check_bare(value, lineno, "list item")
            if ": " in value or value.endswith(":"):
                raise FrontmatterError(
                    f"line {lineno}: nested map inside a list is not supported (quote items containing ': ')"
                )
            if " #" in value or "\t#" in value:
                raise FrontmatterError(f"line {lineno}: ' #' in a bare list item starts a comment, quote the item")
            i = j
        items.append(value)
        i = skip_ws(i)
        if i >= n:
            raise FrontmatterError(f"line {lineno}: unterminated inline list")
        if text[i] == ",":
            i += 1
            if skip_ws(i) < n and text[skip_ws(i)] == "]":
                raise FrontmatterError(f"line {lineno}: trailing comma in inline list")
            continue
        if text[i] == "]":
            _strip_comment_tail(text[i + 1 :], lineno, "list")
            return items
        raise FrontmatterError(f"line {lineno}: expected ',' or ']' in inline list")


def _check_bare(text: str, lineno: int, what: str) -> None:
    """Reject a bare scalar or list item YAML would read as null or a block indicator."""
    if text in _NULL_WORDS:
        raise FrontmatterError(f"line {lineno}: bare {text!r} is a YAML null, use \"\" or quote the {what}")
    if text in ("-", "?") or text.startswith(("- ", "? ", "-\t", "?\t")):
        raise FrontmatterError(
            f"line {lineno}: bare {what} starting with {text[0]!r} is YAML block syntax, quote the {what}"
        )


def _parse_value(raw: str, lineno: int) -> str | bool | list[str]:
    text = raw.strip()
    if not text or text.startswith("#"):
        raise FrontmatterError(
            f"line {lineno}: empty value (nested maps and multi-line values are not supported; use \"\" or [])"
        )
    first = text[0]
    if first == '"':
        value, end = _parse_quoted(text, 0, lineno)
        _strip_comment_tail(text[end:], lineno, "quoted string")
        return value
    if first == "'":
        raise FrontmatterError(f"line {lineno}: single quotes are not supported, use double quotes")
    if first == "[":
        return _parse_list(text, lineno)
    if first == "{":
        raise FrontmatterError(f"line {lineno}: nested map is not supported")
    if first in "|>":
        raise FrontmatterError(f"line {lineno}: multi-line value is not supported")
    if first in "&*!%@`":
        raise FrontmatterError(f"line {lineno}: unsupported YAML syntax {first!r}")
    # Bare scalar: strip a trailing " # comment".
    m = re.search(r"\s#", text)
    if m:
        text = text[: m.start()].rstrip()
    if ": " in text or text.endswith(":"):
        raise FrontmatterError(f"line {lineno}: nested map is not supported (quote values containing ': ')")
    if any(c in text for c in "\"'"):
        raise FrontmatterError(f"line {lineno}: quote character inside a bare value, quote the whole value")
    _check_bare(text, lineno, "value")
    if text == "true":
        return True
    if text == "false":
        return False
    return text


def _parse_block(lines: list[str], first_lineno: int) -> dict:
    mapping: dict = {}
    for offset, line in enumerate(lines):
        lineno = first_lineno + offset
        if not line.strip():
            continue
        if line.startswith("#"):
            continue
        if line[:1] in " \t":
            raise FrontmatterError(
                f"line {lineno}: indented line (nested maps and multi-line values are not supported)"
            )
        if line.startswith("- "):
            raise FrontmatterError(f"line {lineno}: block list item is not supported, use an inline list")
        m = _KEY_RE.match(line)
        if not m:
            raise FrontmatterError(f"line {lineno}: expected 'key: value', got {line!r}")
        key, rest = m.group(1), m.group(2)
        if rest and not rest.startswith(" "):
            raise FrontmatterError(f"line {lineno}: expected a space after '{key}:'")
        if key in mapping:
            raise FrontmatterError(f"line {lineno}: duplicate key {key!r}")
        mapping[key] = _parse_value(rest, lineno)
    return mapping


def parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Return (mapping, body, error). On error mapping is None."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return None, text, "line 1: missing opening '---'"
    close = None
    for idx in range(1, len(lines)):
        if lines[idx].rstrip("\r") == "---":
            close = idx
            break
    if close is None:
        return None, text, "unterminated frontmatter: no closing '---'"
    block = [ln.rstrip("\r") for ln in lines[1:close]]
    body = "\n".join(lines[close + 1 :])
    try:
        mapping = _parse_block(block, 2)
    except FrontmatterError as exc:
        return None, body, str(exc)
    return mapping, body, None


def _needs_quote(value: str) -> bool:
    if value == "" or value in ("true", "false") or value in _NULL_WORDS:
        return True
    if value != value.strip():
        return True
    if any(c in _QUOTE_CHARS for c in value):
        return True
    if any(c in value for c in "\n\r\t\0"):
        return True
    if value[0] in _LEADING_SPECIAL:
        return True
    return False


def _quote(value: str) -> str:
    out = ['"']
    for ch in value:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\0":
            out.append("\\0")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _dump_scalar(value: object, force_quote: bool = False) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = "" if value is None else str(value)
    if force_quote or _needs_quote(text):
        return _quote(text)
    return text


def dump_frontmatter(mapping: dict) -> str:
    """Render mapping as a frontmatter block, `---` lines included.

    parse_frontmatter(dump_frontmatter(m) + body) returns (m, body, None)
    for any mapping of str, bool and list[str] values.
    """
    lines = ["---"]
    for key, value in mapping.items():
        if isinstance(value, (list, tuple)):
            items = [str(item) for item in value]
            rendered = "[" + ", ".join(_dump_scalar(item, force_quote=" " in item) for item in items) + "]"
        else:
            rendered = _dump_scalar(value, force_quote=key in ALWAYS_QUOTED)
        lines.append(f"{key}: {rendered}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def read_unit(path: str | Path) -> tuple[dict | None, str, str | None]:
    """Read a unit file and parse its frontmatter."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, "", f"cannot read {path}: {exc}"
    return parse_frontmatter(text)


def split_sections(body: str) -> list[tuple[str, str]]:
    """Return [(heading, text)] for every `## ` heading outside code fences.

    Text before the first H2 is ignored. Section text is stripped.
    """
    sections: list[tuple[str, list[str]]] = []
    in_fence = False
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
        if not in_fence and line.startswith("## "):
            sections.append((line[3:].strip(), []))
            continue
        if sections:
            sections[-1][1].append(line)
    return [(heading, "\n".join(text).strip()) for heading, text in sections]


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: kb_frontmatter.py <unit.md>", file=sys.stderr)
        return 2
    mapping, _body, error = read_unit(args[0])
    if error:
        print(f"{args[0]}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(mapping, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
