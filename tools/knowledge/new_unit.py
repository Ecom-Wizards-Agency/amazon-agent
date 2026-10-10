#!/usr/bin/env python3
"""Create one knowledge unit from a sweep card or from a title and topic.

Usage:
  python3 tools/knowledge/new_unit.py --from-card <card.json>
  python3 tools/knowledge/new_unit.py --title "..." --topic <topic> [--kind K]
      [--skills a,b] [--marketplaces US,DE]
Options: --id KC-NNNN (must be unused), --dry-run (print, write nothing),
--no-ledger (do not stage a ledger row), --today YYYY-MM-DD (the creation
date; review_by is its month plus 12 months, so a unit built from an old
thread is not stale on arrival; observed stays the card's first-seen month).

The id is 1 + the highest KC number across every topic folder and _retired.
The file is knowledge/<topic>/<id>_<slug>.md, built from the TEMPLATE key and
section order. Unless --no-ledger, one row is appended to the gitignored
_local/knowledge-sweep/ledger-staging.md; `ledger.py append --from-staging`
moves it into the team vault later. The unit never carries identifiers; the
staged row does.

Writing is refused when a scrub pattern class matches the generated file or
when a card token from client_specific_to_strip appears in it. Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from kb_frontmatter import KINDS, SECTION_ORDER, TOPICS, dump_frontmatter, parse_frontmatter  # noqa: E402
from ledger import STAGING_REL, append_rows, header_text, parse_table  # noqa: E402

WORKSPACE_ROOT = HERE.parents[1]
RETIRED_DIR = "_retired"
SLUG_MAX = 60
STOP_BEFORE_DEFAULT = (
    "Stop before any submission, appeal, case send, refund, price change or listing change"
    " unless the operator approved that exact action."
)
_ID_FILE_RE = re.compile(r"^KC-([0-9]+)(?:_|\.md$)")
_ID_RE = re.compile(r"^KC-[0-9]{4}$")
_DATE_RE = re.compile(r"^([0-9]{4})-([0-9]{2})-[0-9]{2}")
_STEP_PREFIX = re.compile(r"^\s*(?:[0-9]+[.)]|[-*])\s+")


# ---------------------------------------------------------------- ids, slugs


def used_numbers(root: Path) -> set[int]:
    """KC numbers already taken in any topic folder or _retired."""
    numbers: set[int] = set()
    knowledge = root / "knowledge"
    for folder in [*TOPICS, RETIRED_DIR]:
        directory = knowledge / folder
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            match = _ID_FILE_RE.match(path.name)
            if match:
                numbers.add(int(match.group(1)))
    return numbers


def next_id(root: Path) -> str:
    numbers = used_numbers(root)
    return f"KC-{(max(numbers) if numbers else 0) + 1:04d}"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:SLUG_MAX].strip("-")
    return slug or "unit"


# ---------------------------------------------------------------- dates


def month_of(date_text: str | None, today: dt.date) -> str:
    match = _DATE_RE.match(date_text or "")
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return f"{today.year:04d}-{today.month:02d}"


def plus_twelve_months(month: str) -> str:
    year, mon = month.split("-")
    return f"{int(year) + 1:04d}-{mon}"


# ---------------------------------------------------------------- mapping


def _asked_as(question: object) -> list[str]:
    """The first sentence of the question as asked, as one short phrasing."""
    text = re.sub(r"\s+", " ", str(question or "")).strip()
    if not text:
        return []
    first = re.split(r"(?<=[.?!])\s", text, maxsplit=1)[0]
    return [first[:200]]


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _norm_path(value: str) -> str:
    text = value.strip().strip("`").strip()
    if text.startswith("./"):
        text = text[2:]
    return text


def _exists_in_repo(root: Path, rel: str) -> bool:
    if not rel or Path(rel).is_absolute():
        return False
    target = (root / rel).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return target.exists()


def _split_paths(root: Path, values: object) -> tuple[list[str], list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for raw in _list(values):
        rel = _norm_path(raw)
        if not rel:
            continue
        (present if _exists_in_repo(root, rel) else missing).append(rel)
    return present, missing


def card_from_args(args: argparse.Namespace) -> dict:
    card: dict = {"title": args.title, "topic": args.topic, "kind": args.kind or "diagnosis"}
    if args.skills:
        card["skills"] = [s.strip() for s in args.skills.split(",") if s.strip()]
    if args.marketplaces:
        card["marketplaces"] = [m.strip() for m in args.marketplaces.split(",") if m.strip()]
    return card


def build_unit(card: dict, unit_id: str, root: Path, today: dt.date) -> tuple[dict, str]:
    """Return (frontmatter mapping, body) for a card."""
    title = str(card.get("title", "")).strip()
    marketplaces = _list(card.get("marketplaces"))
    if marketplaces:
        inferred = bool(card.get("marketplace_inferred", False))
    else:
        marketplaces, inferred = ["all"], True
    sources, sources_missing = _split_paths(root, card.get("first_party_source_paths"))
    sops, sops_missing = _split_paths(root, card.get("related_sop_paths"))
    contradicts, contradicts_missing = _split_paths(root, card.get("contradicts_paths"))
    observed = month_of(card.get("date_first_seen"), today)

    mapping = {
        "id": unit_id,
        "title": title,
        "kind": card.get("kind") or "diagnosis",
        "topic": card.get("topic", ""),
        "status": "draft",
        "skills": _list(card.get("skills")),
        "marketplaces": marketplaces,
        "marketplace_inferred": inferred,
        "surface": str(card.get("surface") or ""),
        "surface_verified": bool(card.get("surface_verified", False)),
        "symptom_keywords": _list(card.get("symptom_keywords")),
        "error_text": _list(card.get("error_text")),
        "asked_as": _asked_as(card.get("problem_as_asked")),
        "synonyms": [],
        "resolution_status": card.get("resolution_status") or "unknown",
        "fix_source": card.get("fix_source") or "unknown",
        "evidence_location": card.get("evidence_location") or "none",
        "confidence": card.get("confidence") or "low",
        "verification": "unverified",
        "verified_on": "",
        "verified_how": "",
        "amazon_sources": sources,
        "related_sops": sops,
        "supersedes": [],
        "contradicts": contradicts,
        "observed": observed,
        "review_by": plus_twelve_months(month_of(None, today)),
        "provenance": f"ledger:{unit_id}",
    }

    steps = [_STEP_PREFIX.sub("", str(s)).strip() for s in _list(card.get("resolution_steps"))]
    steps = [s for s in steps if s]
    fix = "\n".join(f"{n}. {s}" for n, s in enumerate(steps, 1)) if steps else "1. See Answer."

    source_lines = [f"- First-party: `{p}`" for p in sources] or ["- First-party: none captured yet."]
    source_lines += [f"- Also in: `{p}`" for p in sops] or ["- Also in: none."]
    source_lines.append("- Evidence: team vault ledger row for this id.")

    gaps: list[str] = []
    net_new = str(card.get("net_new") or "").strip()
    if net_new:
        gaps.append(f"Net new versus existing sources: {net_new}")
    verdict = str(card.get("coverage_verdict") or "").strip()
    coverage_paths = [_norm_path(p) for p in _list(card.get("coverage_paths"))]
    if verdict and verdict != "unchecked":
        line = f"Existing coverage: {verdict}"
        if coverage_paths:
            line += " (" + ", ".join(f"`{p}`" for p in coverage_paths) + ")"
        gaps.append(line + ".")
    elif verdict == "unchecked":
        gaps.append("Existing coverage was not checked.")
    gaps += [f"not captured locally: `{p}`" for p in sources_missing]
    gaps += [f"related SOP not found locally: `{p}`" for p in sops_missing]
    gaps += [f"contradicted source not found locally: `{p}`" for p in contradicts_missing]
    gaps_text = "\n".join(f"- {g}" for g in gaps) if gaps else "None known."

    sections = {
        "Question": str(card.get("problem_as_asked") or "").strip() or title,
        "Answer": str(card.get("generic_lesson") or "").strip() or "Not written yet.",
        "Cause": str(card.get("root_cause") or "").strip() or "Not established in the source.",
        "Fix": fix,
        "Verify": str(card.get("verify") or "").strip() or "Not stated in the source.",
        "Stop before": STOP_BEFORE_DEFAULT,
        "Sources": "\n".join(source_lines),
        "Gaps": gaps_text,
    }
    body = "".join(f"\n## {name}\n\n{sections[name]}\n" for name in SECTION_ORDER)
    return mapping, body


def render_unit(mapping: dict, body: str) -> str:
    return dump_frontmatter(mapping) + body


# ---------------------------------------------------------------- scrub


def _load_scrub():
    try:
        import scrub  # type: ignore  # noqa: PLC0415
    except ImportError:
        return None
    return scrub


def scrub_hits(text: str) -> list[str] | None:
    """Return scrub pattern-class hits, or None when no scrub check could run."""
    module = _load_scrub()
    if module is None:
        print("notice: tools/knowledge/scrub.py not found, scrub check skipped", file=sys.stderr)
        return None
    find_hits = getattr(module, "find_hits", None)
    if callable(find_hits):
        terms: list[str] = []
        load_terms = getattr(module, "load_terms", None)
        terms_path = getattr(module, "DEFAULT_TERMS_PATH", None)
        if callable(load_terms) and terms_path is not None:
            terms = load_terms(terms_path)
        return [str(getattr(hit, "pattern", hit)) for hit in find_hits(text, terms)]
    patterns = None
    for name in ("PATTERN_CLASSES", "PATTERNS", "CLASSES"):
        patterns = getattr(module, name, None)
        if patterns:
            break
    if isinstance(patterns, dict):
        items = list(patterns.items())
    elif isinstance(patterns, (list, tuple)):
        items = [(getattr(p, "pattern", str(p)), p) for p in patterns]
    else:
        print("notice: scrub.py exposes no recognised scan function or pattern table, scrub check skipped", file=sys.stderr)
        return None
    hits: list[str] = []
    for label, pattern in items:
        regex = re.compile(pattern) if isinstance(pattern, str) else pattern
        if hasattr(regex, "search") and regex.search(text):
            hits.append(str(label))
    return hits


def strip_token_hits(text: str, card: dict) -> list[str]:
    """Card tokens marked client-specific that still appear in the text."""
    lowered = text.lower()
    hits = []
    for token in _list(card.get("client_specific_to_strip")):
        if len(token) >= 3 and token.lower() in lowered:
            hits.append(token)
    return hits


# ---------------------------------------------------------------- ledger staging


def staging_row(card: dict, unit_id: str) -> dict:
    notes = str(card.get("notes") or "").strip()
    related = _list(card.get("related_ts"))
    if related:
        extra = "related_ts: " + ", ".join(related)
        notes = f"{notes}; {extra}" if notes else extra
    return {
        "kb_id": unit_id,
        "client_slug": card.get("client_slug", ""),
        "channel": card.get("channel_name") or card.get("channel_id") or "",
        "parent_ts": card.get("parent_ts", ""),
        "permalink": card.get("permalink", ""),
        "first_seen": card.get("date_first_seen", ""),
        "resolved_on": card.get("date_resolved", ""),
        "resolution_status": card.get("resolution_status", ""),
        "who_diagnosed": card.get("who_answered", ""),
        "who_executed": card.get("who_executed", ""),
        "fix_source": card.get("fix_source", ""),
        "evidence_location": card.get("evidence_location", ""),
        "identifiers": "; ".join(_list(card.get("identifiers"))),
        "notes": notes,
    }


def stage_row(staging_path: Path, row: dict) -> int:
    """Append a row to the staging table, creating it with its header. Return the row count."""
    staging_path.parent.mkdir(parents=True, exist_ok=True)
    text = staging_path.read_text(encoding="utf-8") if staging_path.is_file() else ""
    if not parse_table(text).found:
        if text and not text.endswith("\n"):
            text += "\n"
        text += header_text()
    text = append_rows(text, [row])
    staging_path.write_text(text, encoding="utf-8")
    return len(parse_table(text).rows)


# ---------------------------------------------------------------- main


def _fail(message: str) -> int:
    print(f"new_unit: {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from-card", help="card JSON per tools/knowledge/card.schema.json")
    parser.add_argument("--title")
    parser.add_argument("--topic", choices=TOPICS)
    parser.add_argument("--kind", choices=KINDS)
    parser.add_argument("--skills", help="comma-separated skill names")
    parser.add_argument("--marketplaces", help="comma-separated marketplaces, for example US,DE")
    parser.add_argument("--id", dest="unit_id", help="force an unused id KC-NNNN")
    parser.add_argument("--dry-run", action="store_true", help="print the unit, write nothing")
    parser.add_argument("--no-ledger", action="store_true", help="do not stage a ledger row")
    parser.add_argument("--today", help="creation date YYYY-MM-DD, default today; review_by is its month plus 12 months")
    parser.add_argument("--staging", help="staging file (default _local/knowledge-sweep/ledger-staging.md)")
    parser.add_argument("--root", default=str(WORKSPACE_ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = Path(args.root)

    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        return _fail(f"--today must be YYYY-MM-DD, got {args.today!r}")

    if args.from_card:
        if args.title or args.topic:
            return _fail("use --from-card or --title/--topic, not both")
        try:
            card = json.loads(Path(args.from_card).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return _fail(f"cannot read card {args.from_card}: {exc}")
        if not isinstance(card, dict):
            return _fail("card must be a JSON object")
        if card.get("publishable") is False:
            return _fail("card is marked publishable: false; it stays in the vault, not in knowledge/")
        if card.get("policy_risk") is True:
            print("notice: card has policy_risk true; the reviewing owner decides before review", file=sys.stderr)
        if args.kind:
            card["kind"] = args.kind
    else:
        if not args.title or not args.topic:
            return _fail("--title and --topic are required without --from-card")
        card = card_from_args(args)

    if not str(card.get("title", "")).strip():
        return _fail("title is empty")
    if card.get("topic") not in TOPICS:
        return _fail(f"topic must be one of {', '.join(TOPICS)}, got {card.get('topic')!r}")
    if (card.get("kind") or "diagnosis") not in KINDS:
        return _fail(f"kind must be one of {', '.join(KINDS)}, got {card.get('kind')!r}")

    if args.unit_id:
        if not _ID_RE.match(args.unit_id):
            return _fail(f"--id must look like KC-NNNN, got {args.unit_id!r}")
        if int(args.unit_id[3:]) in used_numbers(root):
            return _fail(f"{args.unit_id} is already used")
        unit_id = args.unit_id
    else:
        unit_id = next_id(root)

    mapping, body = build_unit(card, unit_id, root, today)
    text = render_unit(mapping, body)
    parsed, _body, error = parse_frontmatter(text)
    if error or parsed != mapping:
        return _fail(f"generated frontmatter does not parse back: {error}")

    path = root / "knowledge" / mapping["topic"] / f"{unit_id}_{slugify(mapping['title'])}.md"
    rel = path.relative_to(root).as_posix()

    problems: list[str] = []
    hits = scrub_hits(text)
    if hits:
        problems.append("scrub pattern classes matched: " + ", ".join(sorted(set(hits))))
    tokens = strip_token_hits(text, card)
    if tokens:
        problems.append(f"{len(tokens)} client-specific card token(s) appear in the unit")

    if args.dry_run:
        sys.stdout.write(text)
        for problem in problems:
            print(f"new_unit: refused on write: {problem}", file=sys.stderr)
        return 1 if problems else 0

    if problems:
        for problem in problems:
            print(f"new_unit: refused: {problem}", file=sys.stderr)
        return 1
    if path.exists():
        return _fail(f"{rel} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel}")

    if args.no_ledger:
        print("ledger staging skipped (--no-ledger)")
        return 0
    staging_path = Path(args.staging) if args.staging else root / STAGING_REL
    count = stage_row(staging_path, staging_row(card, unit_id))
    print(f"staged ledger rows: {count} in {staging_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
