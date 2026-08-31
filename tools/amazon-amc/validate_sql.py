#!/usr/bin/env python3
"""Static safety checks for AMC SQL before it is sent to AdLabs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TOKENS = (
    "BUILT_IN_PARAMETER('TIME_WINDOW_START')",
    "BUILT_IN_PARAMETER('TIME_WINDOW_END')",
)


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def top_level_text(sql: str) -> str:
    """Return characters outside parentheses while preserving quoted strings."""
    out = []
    depth = 0
    quote = None
    i = 0
    while i < len(sql):
        ch = sql[i]
        if quote:
            if ch == quote:
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    i += 2
                    continue
                quote = None
            if depth == 0:
                out.append(ch)
        elif ch in ("'", '"'):
            quote = ch
            if depth == 0:
                out.append(ch)
        elif ch == "(":
            depth += 1
            out.append(" ")
        elif ch == ")":
            depth = max(0, depth - 1)
            out.append(" ")
        elif depth == 0:
            out.append(ch)
        else:
            out.append(" ")
        i += 1
    return "".join(out)


def outer_select(sql: str) -> str:
    flat = top_level_text(sql)
    matches = list(re.finditer(r"\bSELECT\b", flat, flags=re.I))
    if not matches:
        return ""
    start = matches[-1].end()
    end_match = re.search(r"\bFROM\b", flat[start:], flags=re.I)
    return flat[start:start + end_match.start()] if end_match else flat[start:]


def validate(sql: str, mode: str) -> tuple[list[str], list[str]]:
    clean = strip_comments(sql)
    upper = clean.upper()
    top = top_level_text(clean)
    selected = outer_select(clean)
    errors: list[str] = []
    warnings: list[str] = []

    if not selected:
        errors.append("no outer SELECT found")
    if re.search(r"\bSELECT\s+(?:[A-Z_][A-Z0-9_]*\.)?\*", upper):
        errors.append("SELECT * is not allowed in AMC SQL")
    if re.search(r"\bRIGHT\s+(?:OUTER\s+)?JOIN\b", upper):
        errors.append("RIGHT JOIN is not allowed in AMC SQL")
    if re.search(r"\bORDER\s+BY\b", top, flags=re.I):
        errors.append("outer ORDER BY is not supported; sort fetched results downstream")
    if re.search(r"\bLIMIT\b", top, flags=re.I):
        errors.append("outer LIMIT is not supported; limit fetched results downstream")

    present = [token in upper for token in TOKENS]
    if mode == "query":
        for token, found in zip(TOKENS, present):
            if not found:
                errors.append(f"measurement query is missing {token}")
        if re.search(r"\bUSER_ID\b", selected, flags=re.I):
            errors.append("measurement output must not expose user_id")
    else:
        if any(present):
            errors.append("audience SQL must not use BUILT_IN_PARAMETER time-window tokens")
        if not re.search(r"\bUSER_ID\b", selected, flags=re.I):
            errors.append("audience SQL outer SELECT must output user_id")

    if re.search(r"\bOVER\s*\(", upper):
        warnings.append("window aggregate found; prefer a totals CTE for portable percentage-of-total metrics")
    if not re.search(r"\bNULLIF\s*\(", upper) and "/" in clean:
        warnings.append("division found without NULLIF; verify divide-by-zero handling")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AMC SQL before an AdLabs run")
    parser.add_argument("sql_file", type=Path)
    parser.add_argument("--mode", choices=("query", "audience"), default="query")
    args = parser.parse_args()
    sql = args.sql_file.read_text(encoding="utf-8-sig")
    errors, warnings = validate(sql, args.mode)
    for warning in warnings:
        print(f"[WARN] {warning}")
    for error in errors:
        print(f"[FAIL] {error}")
    if errors:
        print(f"AMC SQL validation: FAIL ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"AMC SQL validation: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
