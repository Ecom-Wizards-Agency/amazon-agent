#!/usr/bin/env python3
"""Search the operator's local Amazon SOP/help libraries.

This script is intentionally local-only and avoids browser/process control.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

ROOTS = [
    ("MAG SOPs", WORKSPACE_ROOT / "MAG SOPs"),
    ("Amazon Seller Help", WORKSPACE_ROOT / "Amazon Seller Help"),
    ("Amazon Ads Help", WORKSPACE_ROOT / "Amazon Ads Help"),
    ("Advertising Help After Login", WORKSPACE_ROOT / "Advertising Help After Login"),
]

LIBRARY_ALIASES = {
    "all": None,
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


def tokenize(query: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_-]+", query)]


def iter_files(root: Path):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in EXTS:
            if "/.direct-build" in str(path) or "/.final-build" in str(path):
                continue
            if "/_index/" in str(path) and path.suffix.lower() == ".json":
                continue
            yield path


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
        help="Limit search to a routed library group.",
    )
    args = parser.parse_args()

    terms = tokenize(args.query)
    if not terms:
        raise SystemExit("Query must contain at least one searchable term.")

    hits = []
    allowed = LIBRARY_ALIASES[args.library]
    for label, root in ROOTS:
        if allowed is not None and label not in allowed:
            continue
        for path in iter_files(root) or []:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            title = title_for(path, text)
            s = score_text(text, title, path, terms)
            if s:
                hits.append(
                    {
                        "score": s,
                        "library": label,
                        "path": str(path),
                        "title": title,
                        "snippet": snippet(text, terms),
                    }
                )

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
