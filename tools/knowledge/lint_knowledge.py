#!/usr/bin/env python3
"""Lint the knowledge library: format, enums, paths, privacy scrub and index drift.

Checks every unit under `knowledge/<topic>/` and `knowledge/_retired/`
against `docs/knowledge-library.md`: frontmatter keys and order, enums, id
and file name, topic folder, skills and source paths, provenance, dates,
body sections, length, spaced em-dashes and `scrub.find_hits`. Then it
appends `build_knowledge_index.check_drift` so a stale index or README fails.
`knowledge/TEMPLATE.md` is checked only for parseability and key order.

Stdlib only, because Grimoire runs on the PATH python3 without PyYAML.

Usage: python3 tools/knowledge/lint_knowledge.py [--strict] [--terms FILE]
`--strict` also fails when the denylist terms file is missing.
Prints the problems and exits 1, or prints `lint_knowledge: clean (N units)`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_knowledge_index  # noqa: E402
import scrub  # noqa: E402
from kb_frontmatter import (  # noqa: E402
    CONFIDENCES,
    EVIDENCE_LOCATIONS,
    FIX_SOURCES,
    ID_RE,
    KEY_ORDER,
    KINDS,
    LINE_CAP,
    MARKETPLACES,
    RESOLUTION_STATUSES,
    SECTION_ORDER,
    STATUSES,
    TOPICS,
    VERIFICATIONS,
    VERIFIED_HOWS,
    parse_frontmatter,
    split_sections,
)

ROOT = Path(__file__).resolve().parents[2]
TERMS_REL = Path("_local") / "knowledge-redaction-terms.txt"
RETIRED_DIR = build_knowledge_index.RETIRED_DIR
TEMPLATE_NAME = "TEMPLATE.md"
# Folders under knowledge/ that are not topics but are expected.
KNOWN_DIRS = {RETIRED_DIR, "_index"}
KNOWN_ROOT_FILES = {"README.md", TEMPLATE_NAME, ".gitkeep"}

ENUMS = {
    "kind": KINDS,
    "status": STATUSES,
    "resolution_status": RESOLUTION_STATUSES,
    "fix_source": FIX_SOURCES,
    "evidence_location": EVIDENCE_LOCATIONS,
    "confidence": CONFIDENCES,
    "verification": VERIFICATIONS,
    "verified_how": VERIFIED_HOWS,
}
LIST_KEYS = {
    "skills",
    "marketplaces",
    "symptom_keywords",
    "error_text",
    "amazon_sources",
    "related_sops",
    "supersedes",
    "contradicts",
}
BOOL_KEYS = {"marketplace_inferred", "surface_verified"}
PATH_KEYS = ("amazon_sources", "related_sops", "supersedes", "contradicts")
MONTH_RE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
DAY_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
FILE_RE = re.compile(r"^(KC-[0-9]{4})_[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
SPACED_EM_DASH = " \u2014 "
_LINE_PREFIX = re.compile(r"^line (\d+): (.*)$")


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _key_lines(text: str) -> dict[str, int]:
    """Line number of each frontmatter key, for pointing at the problem."""
    lines: dict[str, int] = {}
    for idx, line in enumerate(text.split("\n")[1:], start=2):
        if line.rstrip("\r") == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):", line)
        if m and m.group(1) not in lines:
            lines[m.group(1)] = idx
    return lines


def _heading_lines(text: str) -> dict[str, int]:
    lines: dict[str, int] = {}
    for idx, line in enumerate(text.split("\n"), start=1):
        if line.startswith("## "):
            lines.setdefault(line[3:].strip(), idx)
    return lines


def _parse_error(rel: str, error: str) -> str:
    m = _LINE_PREFIX.match(error)
    if m:
        return f"{rel}:{m.group(1)}: frontmatter: {m.group(2)}"
    return f"{rel}:1: frontmatter: {error}"


def _check_key_order(mapping: dict, rel: str, key_line: dict[str, int]) -> list[str]:
    keys = list(mapping)
    if keys == KEY_ORDER:
        return []
    problems: list[str] = []
    missing = [k for k in KEY_ORDER if k not in mapping]
    unknown = [k for k in keys if k not in KEY_ORDER]
    for key in missing:
        problems.append(f"{rel}:1: missing key {key!r}")
    for key in unknown:
        problems.append(f"{rel}:{key_line.get(key, 1)}: unknown key {key!r}")
    known = [k for k in keys if k in KEY_ORDER]
    expected = [k for k in KEY_ORDER if k in mapping]
    for got, want in zip(known, expected):
        if got != want:
            problems.append(
                f"{rel}:{key_line.get(got, 1)}: key {got!r} out of order, expected {want!r} here"
                f" (order: {', '.join(KEY_ORDER)})"
            )
            break
    return problems


def _valid_repo_path(root: Path, value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value:
        return False
    if any(part == ".." for part in Path(value).parts):
        return False
    return (root / value).exists()


def _check_unit(
    path: Path,
    folder: str,
    root: Path,
    terms: list[str],
    seen_ids: dict[str, str],
) -> list[str]:
    rel = _rel(path, root)
    problems: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{rel}:1: cannot read: {exc}"]

    # Text checks run even when the frontmatter is broken.
    line_count = len(text.splitlines())
    if line_count > LINE_CAP:
        problems.append(f"{rel}:{LINE_CAP + 1}: {line_count} lines, cap is {LINE_CAP}")
    for idx, line in enumerate(text.split("\n"), start=1):
        if SPACED_EM_DASH in line:
            problems.append(f"{rel}:{idx}: spaced em-dash, rewrite the sentence")
    for hit in scrub.find_hits(text, terms):
        problems.append(f"{rel}:{hit.line_no}: scrub {hit.pattern} {hit.match}")

    mapping, body, error = parse_frontmatter(text)
    if error or mapping is None:
        problems.append(_parse_error(rel, error or "unparseable"))
        return problems

    key_line = _key_lines(text)

    def at(key: str) -> str:
        return f"{rel}:{key_line.get(key, 1)}"

    problems.extend(_check_key_order(mapping, rel, key_line))

    # Types.
    for key in LIST_KEYS:
        if key in mapping and not isinstance(mapping[key], list):
            problems.append(f"{at(key)}: {key} must be an inline list")
    for key in BOOL_KEYS:
        if key in mapping and not isinstance(mapping[key], bool):
            problems.append(f"{at(key)}: {key} must be true or false")
    for key in KEY_ORDER:
        if key in mapping and key not in LIST_KEYS and key not in BOOL_KEYS:
            if not isinstance(mapping[key], str):
                problems.append(f"{at(key)}: {key} must be a string")

    def text_value(key: str) -> str:
        value = mapping.get(key)
        return value if isinstance(value, str) else ""

    def list_value(key: str) -> list[str]:
        value = mapping.get(key)
        return [str(v) for v in value] if isinstance(value, list) else []

    # Enums.
    for key, allowed in ENUMS.items():
        if key in mapping and isinstance(mapping[key], str) and mapping[key] not in allowed:
            problems.append(f"{at(key)}: {key} {mapping[key]!r} not in {', '.join(a for a in allowed if a)}")
    topic = text_value("topic")
    if "topic" in mapping and topic not in TOPICS:
        problems.append(f"{at('topic')}: topic {topic!r} not in {', '.join(TOPICS)}")
    markets = list_value("marketplaces")
    if "marketplaces" in mapping:
        if not markets:
            problems.append(f"{at('marketplaces')}: marketplaces is empty, use [all] or codes")
        for item in markets:
            if item not in MARKETPLACES:
                problems.append(f"{at('marketplaces')}: marketplace {item!r} not in {', '.join(MARKETPLACES)}")
        if "all" in markets and len(markets) > 1:
            problems.append(f"{at('marketplaces')}: 'all' must stand alone")

    # Identity.
    unit_id = text_value("id")
    if "id" in mapping:
        if not ID_RE.match(unit_id):
            problems.append(f"{at('id')}: id {unit_id!r} does not match KC-NNNN")
        prefix = path.name.split("_", 1)[0]
        if unit_id != prefix:
            problems.append(f"{at('id')}: id {unit_id!r} does not match file name prefix {prefix!r}")
        if unit_id in seen_ids:
            problems.append(f"{at('id')}: duplicate id {unit_id!r}, also {seen_ids[unit_id]}")
        else:
            seen_ids[unit_id] = rel
    if not FILE_RE.match(path.name):
        problems.append(f"{rel}:1: file name must be KC-NNNN_<lowercase-kebab-slug>.md")
    if "title" in mapping and not text_value("title").strip():
        problems.append(f"{at('title')}: title is empty")

    # Folder and status.
    status = text_value("status")
    if folder == RETIRED_DIR:
        if status != "retired":
            problems.append(f"{at('status')}: units under knowledge/{RETIRED_DIR}/ must have status retired")
    else:
        if "topic" in mapping and topic != folder:
            problems.append(f"{at('topic')}: topic {topic!r} does not match folder {folder!r}")
        if status == "retired":
            problems.append(f"{at('status')}: retired units belong under knowledge/{RETIRED_DIR}/")

    # Skills and paths.
    for skill in list_value("skills"):
        if not skill or "/" in skill or not (root / "skills" / skill).is_dir():
            problems.append(f"{at('skills')}: skill {skill!r} is not a directory under skills/")
    for key in PATH_KEYS:
        for value in list_value(key):
            if not _valid_repo_path(root, value):
                problems.append(f"{at(key)}: {key} path does not exist in the repo: {value}")

    # Provenance and dates.
    if "provenance" in mapping and text_value("provenance") != f"ledger:{unit_id}":
        problems.append(f"{at('provenance')}: provenance must be 'ledger:{unit_id}'")
    for key in ("observed", "review_by"):
        if key in mapping and not MONTH_RE.match(text_value(key)):
            problems.append(f"{at(key)}: {key} {text_value(key)!r} is not YYYY-MM")
    observed, review_by = text_value("observed"), text_value("review_by")
    if MONTH_RE.match(observed) and MONTH_RE.match(review_by) and review_by < observed:
        problems.append(f"{at('review_by')}: review_by {review_by} is before observed {observed}")
    verification = text_value("verification")
    verified_on = text_value("verified_on")
    verified_how = text_value("verified_how")
    if verification == "verified":
        valid_day = False
        if DAY_RE.match(verified_on):
            try:
                dt.date.fromisoformat(verified_on)
                valid_day = True
            except ValueError:
                pass
        if not valid_day:
            problems.append(f"{at('verified_on')}: verified_on must be YYYY-MM-DD when verification is verified")
        if not verified_how:
            problems.append(f"{at('verified_how')}: verified_how is required when verification is verified")
    elif verification == "unverified":
        if verified_on:
            problems.append(f"{at('verified_on')}: verified_on must be empty when verification is unverified")
        if verified_how:
            problems.append(f"{at('verified_how')}: verified_how must be empty when verification is unverified")

    # Sections.
    sections = split_sections(body)
    headings = [h for h, _ in sections]
    heading_line = _heading_lines(text)
    if headings != SECTION_ORDER:
        for name in SECTION_ORDER:
            if name not in headings:
                problems.append(f"{rel}:1: missing section '## {name}'")
        for name in headings:
            if name not in SECTION_ORDER:
                problems.append(f"{rel}:{heading_line.get(name, 1)}: unexpected section '## {name}'")
        for name in {h for h in headings if headings.count(h) > 1}:
            problems.append(f"{rel}:{heading_line.get(name, 1)}: duplicate section '## {name}'")
        present = [h for h in headings if h in SECTION_ORDER]
        expected = [h for h in SECTION_ORDER if h in present]
        if len(present) == len(set(present)) and present != expected:
            problems.append(f"{rel}:1: sections out of order, expected {' > '.join(SECTION_ORDER)}")
    for name, section_text in sections:
        if name in SECTION_ORDER and not section_text.strip():
            problems.append(f"{rel}:{heading_line.get(name, 1)}: section '## {name}' is empty")
    return problems


def _check_template(path: Path, root: Path) -> list[str]:
    rel = _rel(path, root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{rel}:1: cannot read: {exc}"]
    mapping, _body, error = parse_frontmatter(text)
    if error or mapping is None:
        return [_parse_error(rel, error or "unparseable")]
    return _check_key_order(mapping, rel, _key_lines(text))


def _layout_problems(root: Path) -> list[str]:
    """Units outside a topic or _retired folder would be silently skipped."""
    knowledge = root / "knowledge"
    problems: list[str] = []
    if not knowledge.is_dir():
        return [f"knowledge: directory missing under {root}"]
    for entry in sorted(knowledge.iterdir()):
        if entry.is_dir() and entry.name not in TOPICS and entry.name not in KNOWN_DIRS:
            problems.append(f"{_rel(entry, root)}:1: unknown folder, use a topic folder or {RETIRED_DIR}/")
        elif entry.is_file() and entry.suffix == ".md" and entry.name not in KNOWN_ROOT_FILES:
            problems.append(f"{_rel(entry, root)}:1: unit outside a topic folder")
    return problems


def unit_files(root: str | Path = ROOT) -> list[tuple[str, Path]]:
    """(folder, path) for every unit, the same walk the index builder uses."""
    return build_knowledge_index._unit_files(Path(root))


def lint_knowledge(
    root: str | Path = ROOT,
    strict: bool = False,
    terms_path: str | Path | None = None,
) -> list[str]:
    """Return one `path:line: message` string per problem; empty means clean."""
    root = Path(root)
    problems: list[str] = []
    terms_file = Path(terms_path) if terms_path else root / TERMS_REL
    terms: list[str] = []
    if terms_file.is_file():
        terms = scrub.load_terms(terms_file)
    elif strict:
        problems.append(
            f"{_rel(terms_file, root)}:1: denylist terms file missing,"
            " run python3 tools/knowledge/seed_redaction_terms.py"
        )

    problems.extend(_layout_problems(root))
    template = root / "knowledge" / TEMPLATE_NAME
    if template.is_file():
        problems.extend(_check_template(template, root))

    seen_ids: dict[str, str] = {}
    for folder, path in unit_files(root):
        problems.extend(_check_unit(path, folder, root, terms, seen_ids))

    problems.extend(build_knowledge_index.check_drift(root))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="fail when the denylist terms file is missing")
    parser.add_argument("--terms", help=f"denylist file (default {TERMS_REL.as_posix()})")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(args.root)
    problems = lint_knowledge(root, strict=args.strict, terms_path=args.terms)
    if problems:
        for problem in problems:
            print(problem)
        print(f"lint_knowledge: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"lint_knowledge: clean ({len(unit_files(root))} units)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
