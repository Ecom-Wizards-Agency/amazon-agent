#!/usr/bin/env python3
"""Slim the MAG SOPs index and regenerate the library README.

The original capture embedded full SOP body text and image lists in
`MAG SOPs/_index/sop-index.json` (~5.7 MB). Nothing consumes those fields:
full-text search runs over the markdown files themselves. This script keeps
the index metadata-only (like the other three library indexes), drops entries
whose file was deleted from the curated tree, and marks entries that were
moved under `MAG SOPs/_archive/` as archived.

Rerunnable and idempotent. Use --readme to also regenerate `MAG SOPs/README.md`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SOP_ROOT = WORKSPACE_ROOT / "MAG SOPs"
INDEX_PATH = SOP_ROOT / "_index" / "sop-index.json"

KEEP_FIELDS = [
    "title",
    "category",
    "chapter",
    "url",
    "captured_at",
    "file",
    "body_length",
    "image_count",
]


def slim_entry(entry: dict) -> dict | None:
    rel = entry.get("file", "")
    if not rel:
        return None
    slim = {k: entry[k] for k in KEEP_FIELDS if k in entry}
    if rel.startswith("_archive/"):
        if (SOP_ROOT / rel).exists():
            slim["archived"] = True
            return slim
        return None
    if (SOP_ROOT / rel).exists():
        return slim
    archived_rel = f"_archive/{rel}"
    if (SOP_ROOT / archived_rel).exists():
        slim["file"] = archived_rel
        slim["archived"] = True
        return slim
    return None


def build_readme(data: dict) -> str:
    active: dict[str, list[dict]] = {}
    archived: dict[str, list[dict]] = {}
    for entry in data["captured"]:
        bucket = archived if entry.get("archived") else active
        bucket.setdefault(entry.get("category", "Uncategorized"), []).append(entry)

    lines = [
        "# MAG SOP Library",
        "",
        f"Captured from My Amazon Guy SOP Library on `{data.get('captured_at', 'unknown')}`.",
        "",
        "This runtime tree is curated for Amazon work. Categories irrelevant to the",
        "agent were removed (AI ChatGPT prompts, Product Development, parts of",
        "Business Analysis); Walmart is parked under `_archive/` and excluded from",
        "search. The complete 535-file capture with all assets lives in the pCloud",
        "visual archive (see `docs/mag-sops-assets.md`).",
        "",
        f"Active SOP entries: **{sum(len(v) for v in active.values())}**"
        f" (plus {sum(len(v) for v in archived.values())} archived)",
    ]
    for category in sorted(active):
        entries = sorted(active[category], key=lambda e: e.get("title", ""))
        lines += ["", f"## {category} ({len(entries)})", ""]
        lines += [f"- [{e['title']}]({e['file']})" for e in entries]
    if archived:
        lines += ["", "## Archived (excluded from search)", ""]
        for category in sorted(archived):
            entries = sorted(archived[category], key=lambda e: e.get("title", ""))
            lines += [f"### {category} ({len(entries)})", ""]
            lines += [f"- [{e['title']}]({e['file']})" for e in entries]
            lines += [""]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readme", action="store_true", help="Also regenerate MAG SOPs/README.md")
    args = parser.parse_args()

    data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    before = len(data.get("captured", []))
    slimmed = [s for s in (slim_entry(e) for e in data.get("captured", [])) if s]
    data["captured"] = slimmed
    data["total_entries"] = len(slimmed)
    data["captured_count"] = len(slimmed)
    data["archived_count"] = sum(1 for e in slimmed if e.get("archived"))
    data["categories"] = sorted({e.get("category", "") for e in slimmed if not e.get("archived")})

    INDEX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    size_kb = INDEX_PATH.stat().st_size / 1024
    print(
        f"sop-index.json: {before} -> {len(slimmed)} entries"
        f" ({data['archived_count']} archived), {size_kb:.0f} KB"
    )

    if args.readme:
        readme_path = SOP_ROOT / "README.md"
        readme_path.write_text(build_readme(data), encoding="utf-8")
        print(f"regenerated {readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
