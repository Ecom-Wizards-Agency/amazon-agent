#!/usr/bin/env python3
"""Slim the MAG SOPs index and regenerate the library README.

The original capture embedded full SOP body text and image lists in
`MAG SOPs/_index/sop-index.json` (~5.7 MB). Nothing consumes those fields:
full-text search runs over the markdown files themselves. This script keeps
the index metadata-only (like the other three library indexes), drops entries
whose file was deleted from the curated tree, and marks entries that were
moved under `MAG SOPs/_archive/` as archived.

Triage fields (status, superseded_by, merge_into, triaged_on, flags,
knowledge_value, revised_at, revision_checked_at) are kept. Every
superseded_by or merge_into target must exist as a workspace path or a MAG SOP
file, otherwise nothing is written and the script exits 1. The optional
top-level `dropped` list ({"what", "date"}) records removed SOP sets and is
rendered into the README; it is seeded with the historical removals on the
first run that finds it absent.

Rerunnable and idempotent. Use --readme to also regenerate `MAG SOPs/README.md`.
"""

from __future__ import annotations

import argparse
import copy
import json
import textwrap
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
SOP_DIRNAME = "MAG SOPs"
SOP_ROOT = WORKSPACE_ROOT / SOP_DIRNAME
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
    "status",
    "superseded_by",
    "merge_into",
    "triaged_on",
    "flags",
    "knowledge_value",
    "revised_at",
    "revision_checked_at",
]

TARGET_FIELDS = ("superseded_by", "merge_into")

# Removals made before the `dropped` list existed (seeded on first run).
DEFAULT_DROPPED = [
    {"what": "AI ChatGPT prompts", "date": "2026-07-08"},
    {"what": "Product Development", "date": "2026-07-08"},
    {"what": "parts of Business Analysis", "date": "2026-07-08"},
    {"what": "the Walmart SOPs", "date": "2026-07-27"},
]

# Rendered verbatim while the index has no `dropped` key.
LEGACY_CURATION_LINES = [
    "This runtime tree is curated for Amazon work. Categories irrelevant to the",
    "agent were removed: AI ChatGPT prompts, Product Development, parts of",
    "Business Analysis, and the Walmart SOPs (dropped 2026-07-27). The complete",
    "535-file capture with all assets lives in the pCloud visual archive",
    "(see `docs/mag-sops-assets.md`).",
]
ARCHIVE_SENTENCE = (
    "The complete 535-file capture with all assets lives in the pCloud visual"
    " archive (see `docs/mag-sops-assets.md`)."
)
WRAP_WIDTH = 74


class MissingTargets(Exception):
    """Raised when a superseded_by or merge_into target does not exist."""

    def __init__(self, missing: list[str]):
        super().__init__(f"{len(missing)} missing superseded_by/merge_into targets")
        self.missing = missing


def slim_entry(entry: dict, sop_root: Path | None = None) -> dict | None:
    sop_root = SOP_ROOT if sop_root is None else sop_root
    rel = entry.get("file", "")
    if not rel:
        return None
    slim = {k: entry[k] for k in KEEP_FIELDS if k in entry}
    if rel.startswith("_archive/"):
        if (sop_root / rel).exists():
            slim["archived"] = True
            return slim
        return None
    if (sop_root / rel).exists():
        return slim
    archived_rel = f"_archive/{rel}"
    if (sop_root / archived_rel).exists():
        slim["file"] = archived_rel
        slim["archived"] = True
        return slim
    return None


def _join_words(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def render_dropped(dropped: list) -> list[str]:
    """Render the curation paragraph from the `dropped` list, wrapped like the README."""
    groups: list[tuple[str, list[str]]] = []
    for item in dropped:
        if not isinstance(item, dict) or not item.get("what"):
            continue
        date = str(item.get("date", "")).strip()
        if groups and groups[-1][0] == date:
            groups[-1][1].append(str(item["what"]))
        else:
            groups.append((date, [str(item["what"])]))
    parts = [
        _join_words(whats) + (f" (dropped {date})" if date else "") for date, whats in groups
    ]
    text = "This runtime tree is curated for Amazon work."
    if parts:
        if len(parts) == 1:
            listed = parts[0]
        else:
            listed = ", ".join(parts[:-1]) + ", and " + parts[-1]
        text += f" SOPs irrelevant or unusable for the agent were removed: {listed}."
    text += " " + ARCHIVE_SENTENCE
    return textwrap.wrap(
        text, width=WRAP_WIDTH, break_long_words=False, break_on_hyphens=False
    )


def _entry_line(entry: dict) -> str:
    line = f"- [{entry['title']}]({entry['file']})"
    status = entry.get("status")
    if status == "superseded":
        target = entry.get("superseded_by")
        line += f" (superseded by `{target}`)" if target else " (superseded)"
    elif status == "merged" and entry.get("merge_into"):
        line += f" (merged into `{entry['merge_into']}`)"
    return line


def build_readme(data: dict) -> str:
    active: dict[str, list[dict]] = {}
    archived: dict[str, list[dict]] = {}
    for entry in data["captured"]:
        bucket = archived if entry.get("archived") else active
        bucket.setdefault(entry.get("category", "Uncategorized"), []).append(entry)

    superseded = sum(
        1 for entries in active.values() for e in entries if e.get("status") == "superseded"
    )
    curation = (
        render_dropped(data["dropped"]) if "dropped" in data else list(LEGACY_CURATION_LINES)
    )
    lines = [
        "# MAG SOP Library",
        "",
        f"Captured from My Amazon Guy SOP Library on `{data.get('captured_at', 'unknown')}`.",
        "",
        *curation,
        "",
        f"Active SOP entries: **{sum(len(v) for v in active.values())}**"
        + (f" ({superseded} superseded)" if superseded else "")
        + f" (plus {sum(len(v) for v in archived.values())} archived)",
    ]
    for category in sorted(active):
        entries = sorted(active[category], key=lambda e: e.get("title", ""))
        lines += ["", f"## {category} ({len(entries)})", ""]
        lines += [_entry_line(e) for e in entries]
    if archived:
        lines += ["", "## Archived (excluded from search)", ""]
        for category in sorted(archived):
            entries = sorted(archived[category], key=lambda e: e.get("title", ""))
            lines += [f"### {category} ({len(entries)})", ""]
            lines += [_entry_line(e) for e in entries]
            lines += [""]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def target_exists(value: str, workspace_root: Path) -> bool:
    path = value.split("#", 1)[0].strip()
    if not path:
        return False
    return (workspace_root / path).exists() or (workspace_root / SOP_DIRNAME / path).exists()


def missing_targets(entries: list[dict], workspace_root: Path) -> list[str]:
    missing = []
    for entry in entries:
        for field in TARGET_FIELDS:
            raw = entry.get(field)
            if not raw:
                continue
            for value in str(raw).split(";"):
                value = value.strip()
                if value and not target_exists(value, workspace_root):
                    missing.append(f"{entry.get('file', '?')}: {field} {value}")
    return missing


def run(write_readme: bool = False, root: Path | None = None) -> dict:
    """Slim the index (and optionally regenerate the README); return the counts.

    Raises MissingTargets before writing anything when a superseded_by or
    merge_into target does not exist.
    """
    workspace = WORKSPACE_ROOT if root is None else Path(root).resolve()
    sop_root = workspace / SOP_DIRNAME
    index_path = sop_root / "_index" / "sop-index.json"

    data = json.loads(index_path.read_text(encoding="utf-8"))
    before = len(data.get("captured", []))
    slimmed = [s for s in (slim_entry(e, sop_root) for e in data.get("captured", [])) if s]

    missing = missing_targets(slimmed, workspace)
    if missing:
        raise MissingTargets(missing)

    data["captured"] = slimmed
    data["total_entries"] = len(slimmed)
    data["captured_count"] = len(slimmed)
    data["archived_count"] = sum(1 for e in slimmed if e.get("archived"))
    data["categories"] = sorted({e.get("category", "") for e in slimmed if not e.get("archived")})
    seeded = "dropped" not in data
    if seeded:
        data["dropped"] = copy.deepcopy(DEFAULT_DROPPED)

    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    readme_path = None
    if write_readme:
        readme_path = sop_root / "README.md"
        readme_path.write_text(build_readme(data), encoding="utf-8")

    return {
        "before": before,
        "after": len(slimmed),
        "archived": data["archived_count"],
        "superseded": sum(
            1 for e in slimmed if e.get("status") == "superseded" and not e.get("archived")
        ),
        "merged": sum(1 for e in slimmed if e.get("status") == "merged"),
        "dropped_seeded": seeded,
        "size_kb": index_path.stat().st_size / 1024,
        "index_path": str(index_path),
        "readme_path": str(readme_path) if readme_path else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--readme", action="store_true", help="Also regenerate MAG SOPs/README.md")
    args = parser.parse_args()

    try:
        result = run(write_readme=args.readme)
    except MissingTargets as exc:
        for item in exc.missing:
            print(f"missing target: {item}")
        print("nothing written")
        return 1

    print(
        f"sop-index.json: {result['before']} -> {result['after']} entries"
        f" ({result['archived']} archived), {result['size_kb']:.0f} KB"
    )
    if result["dropped_seeded"]:
        print(f"seeded the dropped list with {len(DEFAULT_DROPPED)} historical removals")
    if result["readme_path"]:
        print(f"regenerated {result['readme_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
