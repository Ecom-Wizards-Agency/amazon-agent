#!/usr/bin/env python3
"""Search the operator's local Amazon SOP/help libraries.

Libraries: the authored knowledge library (`knowledge/`), MAG SOPs, SOP drafts,
the Amazon Seller Help, Amazon Ads Help and Advertising Help After Login
captures, and AdLabs Help. `--library all` searches every one of them.

Knowledge units get boosts from their frontmatter: a query phrase inside a
symptom keyword, an `asked_as` phrasing or a synonym, every query term across
those lists, an error text
hit and a verified unit. An error text hits when one query term equals a whole
entry (a code such as FBA_INB_0008), or when the normalised query equals the
entry's tokens or, with two or more terms, sits inside them (a pasted notice
or a run of words from it). Retired units and `knowledge/_retired/` are skipped.
MAG SOPs whose index entry has `status: superseded` score half and carry
`superseded_by` in the hit.

This script is intentionally local-only and avoids browser/process control.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_ROOT = WORKSPACE_ROOT / "knowledge"
MAG_ROOT = WORKSPACE_ROOT / "MAG SOPs"
MAG_INDEX = MAG_ROOT / "_index" / "sop-index.json"

# Frontmatter parser for knowledge units. Without it, units score as plain text.
sys.path.insert(0, str(WORKSPACE_ROOT / "tools" / "knowledge"))
try:
    from kb_frontmatter import parse_frontmatter
except Exception:  # pragma: no cover - degrade to plain scoring
    parse_frontmatter = None

ROOTS = [
    ("Amazon Knowledge", KNOWLEDGE_ROOT),
    ("MAG SOPs", MAG_ROOT),
    ("SOP Drafts", WORKSPACE_ROOT / "sop-drafts"),
    ("Amazon Seller Help", WORKSPACE_ROOT / "Amazon Seller Help"),
    ("Amazon Ads Help", WORKSPACE_ROOT / "Amazon Ads Help"),
    ("Advertising Help After Login", WORKSPACE_ROOT / "Advertising Help After Login"),
    ("AdLabs Help", WORKSPACE_ROOT / "AdLabs Help"),
]

LIBRARY_ALIASES = {
    "all": None,
    "kb": {"Amazon Knowledge"},
    "knowledge": {"Amazon Knowledge"},
    "drafts": {"SOP Drafts"},
    "adlabs": {"AdLabs Help"},
    "mag": {"MAG SOPs"},
    "sop": {"MAG SOPs"},
    "sops": {"MAG SOPs"},
    "seller": {"Amazon Seller Help"},
    "seller-help": {"Amazon Seller Help"},
    "ads-api": {"Amazon Ads Help"},
    "amazon-ads-help": {"Amazon Ads Help"},
    "ads-support": {"Advertising Help After Login"},
    "ads-ui": {"Advertising Help After Login"},
    "advertising-help": {"Advertising Help After Login"},
    "ads": {"Amazon Ads Help", "Advertising Help After Login"},
}

EXTS = {".md", ".json", ".txt"}
SKIP_NAMES = {"TEMPLATE.md", ".gitkeep"}


def tokenize(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]+", query)]


def iter_files(root: Path):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTS:
            if path.name in SKIP_NAMES:
                continue
            if _is_under(path, KNOWLEDGE_ROOT / "_retired"):
                continue
            # Generated unit list; the units themselves are the hits.
            if path == KNOWLEDGE_ROOT / "README.md":
                continue
            if "/.direct-build" in str(path) or "/.final-build" in str(path):
                continue
            if "/_archive/" in str(path):
                continue
            if "/_index/" in str(path) and path.suffix.lower() == ".json":
                continue
            yield path


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def knowledge_meta(text: str) -> dict | None:
    """The unit's frontmatter, or None when it cannot be parsed."""
    if parse_frontmatter is None:
        return None
    try:
        mapping, _body, error = parse_frontmatter(text)
    except Exception:
        return None
    if error or not isinstance(mapping, dict):
        return None
    return mapping


def error_text_hit(entries: list[str], terms: list[str]) -> bool:
    """True when the query matches an error_text entry.

    Either one query term equals a whole entry (a single-token code), or the
    query's joined lowercase terms equal the entry's joined tokens, or, for a
    query of two or more terms, appear inside them on token boundaries (a
    verbatim notice, whole or in part). One common word alone never matches
    inside a longer notice.
    """
    if not entries or not terms:
        return False
    whole = {e.strip().lower() for e in entries}
    if any(t in whole for t in terms):
        return True
    phrase = " ".join(terms)
    for entry in entries:
        normalised = " ".join(tokenize(entry))
        if not normalised:
            continue
        if phrase == normalised:
            return True
        if len(terms) > 1 and f" {phrase} " in f" {normalised} ":
            return True
    return False


def knowledge_boost(meta: dict, terms: list[str]) -> int:
    """Extra score for a unit whose symptoms, error text or verification match."""
    boost = 0
    phrase = " ".join(terms)
    keywords = [k.lower() for k in _as_list(meta.get("symptom_keywords")) + _as_list(meta.get("asked_as")) + _as_list(meta.get("synonyms"))]
    if keywords:
        if any(phrase in k for k in keywords):
            boost += 60
        joined = " ".join(keywords)
        if all(t in joined for t in terms):
            boost += 40
    if error_text_hit(_as_list(meta.get("error_text")), terms):
        boost += 120
    if meta.get("verification") == "verified":
        boost += 15
    return boost


def load_superseded(index_path: Path = MAG_INDEX) -> dict[str, str]:
    """Map MAG SOP file (relative to MAG SOPs/) to its superseded_by target.

    Tolerates a missing index, a missing `captured` list and entries without a
    `status` field; any of those yields no down-ranking.
    """
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    entries = data.get("captured") if isinstance(data, dict) else None
    out: dict[str, str] = {}
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict) or entry.get("status") != "superseded":
            continue
        rel = entry.get("file")
        if isinstance(rel, str) and rel:
            out[rel] = str(entry.get("superseded_by") or "")
    return out


def score_text(text: str, title: str, path: Path, terms: list[str]) -> int:
    low = text.lower()
    title_low = title.lower()
    path_low = str(path).lower()
    score = 0
    matched = 0
    for term in terms:
        count = low.count(term)
        if count:
            matched += 1
        score += min(count, 8) * 5
        if term in title_low:
            score += 35
        if term in path_low:
            score += 20
    phrase = " ".join(terms)
    if len(terms) > 1:
        if matched < max(1, (len(terms) + 1) // 2):
            return 0
        if phrase in low:
            score += 160
        if phrase in title_low:
            score += 250
        if phrase.replace(" ", "-") in path_low:
            score += 200
    return score


def snippet(text: str, terms: list[str], length: int = 360) -> str:
    low = text.lower()
    positions = [low.find(t) for t in terms if low.find(t) >= 0]
    start = max(0, min(positions) - 120) if positions else 0
    raw = re.sub(r"\s+", " ", text[start : start + length]).strip()
    return raw


def title_for(path: Path, text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        return m.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return str(data.get("title") or data.get("source") or path.stem)
    except Exception:
        pass
    return path.stem.replace("-", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local Amazon SOP/help libraries.")
    parser.add_argument("query", help="Search query, e.g. 'create shipment' or 'bid adjustment'")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument(
        "--library",
        choices=sorted(LIBRARY_ALIASES),
        default="all",
        help="Limit search to a routed library group: kb/knowledge, mag, drafts, seller, ads, adlabs, or all.",
    )
    args = parser.parse_args()

    terms = tokenize(args.query)
    if not terms:
        raise SystemExit("Query must contain at least one searchable term.")

    hits = []
    allowed = LIBRARY_ALIASES[args.library]
    superseded: dict[str, str] | None = None
    for label, root in ROOTS:
        if allowed is not None and label not in allowed:
            continue
        if root == MAG_ROOT and superseded is None:
            superseded = load_superseded(MAG_INDEX)
        for path in iter_files(root) or []:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            meta = None
            if root == KNOWLEDGE_ROOT and path.suffix.lower() == ".md":
                meta = knowledge_meta(text)
                if meta is not None and meta.get("status") == "retired":
                    continue
            title = title_for(path, text)
            if meta is not None and isinstance(meta.get("title"), str) and meta["title"]:
                title = meta["title"]
            s = score_text(text, title, path, terms)
            if s and meta is not None:
                s += knowledge_boost(meta, terms)
            superseded_by = None
            if s and root == MAG_ROOT and superseded:
                rel = path.relative_to(MAG_ROOT).as_posix()
                if rel in superseded:
                    s = s // 2
                    superseded_by = superseded[rel]
            if s:
                hit = {
                    "score": s,
                    "library": label,
                    "path": str(path),
                    "title": title,
                    "snippet": snippet(text, terms),
                }
                if meta is not None:
                    for key in ("id", "status", "verification", "topic"):
                        hit[key] = meta.get(key)
                if superseded_by is not None:
                    hit["superseded_by"] = superseded_by
                hits.append(hit)

    hits.sort(key=lambda h: (-h["score"], h["library"], h["path"]))
    print(
        json.dumps(
            {
                "query": args.query,
                "library": args.library,
                "count": len(hits),
                "results": hits[: args.limit],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
