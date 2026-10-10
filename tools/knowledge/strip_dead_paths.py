#!/usr/bin/env python3
"""Strip references to removed repo files from knowledge units and sweep cards.

Dropping a MAG SOP leaves every unit and card that cited it with a dead path, and
the strict lint and the review queue then reject them. sop_apply_triage.py calls
run() after its removals; the CLI exists for a manual pass.

  python3 tools/knowledge/strip_dead_paths.py [--date YYYY-MM-DD] [--dry-run]

Units: the `related_sops` list loses paths that no longer exist, and a body line
`- Also in: ...` that cites only removed pages is deleted (a mixed line keeps
the live citations and names the removed one as removed; code fences are left
alone and `#anchor` suffixes are ignored). Cards under cards/candidate: the four
path list fields lose dead paths and `verifier_notes` records which. Every dead
path goes, not only the files of the current run. The knowledge
index and README are rebuilt when a unit changed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kb_frontmatter  # noqa: E402

WORKSPACE_ROOT = HERE.parents[1]
CARD_PATH_FIELDS = ("first_party_source_paths", "related_sop_paths", "coverage_paths", "contradicts_paths")
BACKTICK_PATH = re.compile(r"`((?:MAG SOPs|sop-drafts|Amazon Seller Help|Amazon Ads Help|Advertising Help After Login|AdLabs Help|knowledge|skills|docs)/[^`#]+)(?:#[^`]*)?`")
LABELS = (("MAG SOPs/", "a MAG SOP"), ("sop-drafts/", "a SOP draft"), ("knowledge/", "a knowledge unit"), ("skills/", "a skill reference"), ("docs/", "a repo doc"))


def _ddmmyyyy(date: str) -> str:
    try:
        return dt.date.fromisoformat(date).strftime("%d.%m.%Y")
    except ValueError:
        return date


def _exists(root: Path, rel: str) -> bool:
    return (root / rel.split("#", 1)[0]).exists()


def _label(rel: str) -> str:
    for prefix, label in LABELS:
        if rel.startswith(prefix):
            return label
    return "a help capture"


def strip_units(root: Path, date: str, dry_run: bool) -> list[dict]:
    changes: list[dict] = []
    for path in sorted((root / "knowledge").glob("*/KC-*.md")) if (root / "knowledge").exists() else []:
        text = path.read_text(encoding="utf-8")
        mapping, body, error = kb_frontmatter.parse_frontmatter(text)
        if error or mapping is None:
            continue
        removed: list[str] = []
        related = mapping.get("related_sops")
        if isinstance(related, list):
            keep = [p for p in related if _exists(root, str(p))]
            removed += [str(p) for p in related if str(p) not in keep]
            mapping["related_sops"] = keep
        body_lines = body.split("\n")
        new_body: list[str] = []
        body_removed: list[str] = []
        in_fence = False
        for line in body_lines:
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
            cited = [] if in_fence else BACKTICK_PATH.findall(line)
            dead = [c for c in cited if not _exists(root, c)]
            if not dead:
                new_body.append(line)
                continue
            body_removed += dead
            if line.lstrip().startswith("- Also in:") and len(dead) == len(cited):
                continue
            for c in dead:
                line = re.sub(rf"`{re.escape(c)}(?:#[^`]*)?`", f"{_label(c)} removed on {_ddmmyyyy(date)}", line)
            new_body.append(line)
        if not removed and not body_removed:
            continue
        changes.append({"file": str(path.relative_to(root)), "frontmatter_removed": removed, "body_removed": body_removed})
        if not dry_run:
            path.write_text(kb_frontmatter.dump_frontmatter(mapping) + "\n".join(new_body), encoding="utf-8")
    return changes


def strip_cards(root: Path, store: Path, date: str, dry_run: bool) -> list[dict]:
    changes: list[dict] = []
    if not store.exists():
        return changes
    for path in sorted(store.glob("CARD-*.json")):
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        removed: dict[str, list[str]] = {}
        for field in CARD_PATH_FIELDS:
            value = card.get(field)
            if not isinstance(value, list):
                continue
            keep = [p for p in value if isinstance(p, str) and _exists(root, p)]
            gone = [str(p) for p in value if p not in keep]
            if gone:
                card[field] = keep
                removed[field] = gone
        if not removed:
            continue
        names = ", ".join(sorted({Path(p).name for gone in removed.values() for p in gone}))
        note = f" [paths of repo files removed on {_ddmmyyyy(date)} stripped: {names}]"
        previous = card.get("verifier_notes")
        if isinstance(previous, list):
            previous = "; ".join(str(x) for x in previous)
        card["verifier_notes"] = (str(previous) if previous not in (None, "") else "") + note
        changes.append({"file": str(path), "removed": removed})
        if not dry_run:
            path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changes


def rebuild_index(root: Path) -> bool:
    builder = root / "tools" / "knowledge" / "build_knowledge_index.py"
    if not builder.exists():
        return False
    result = subprocess.run([sys.executable, str(builder), "--readme"], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"knowledge index rebuild failed: {result.stderr.strip()[-300:]}", file=sys.stderr)
    return result.returncode == 0


def run(root: Path = WORKSPACE_ROOT, date: str | None = None, dry_run: bool = False, store: Path | None = None) -> dict:
    root = Path(root)
    date = date or dt.date.today().isoformat()
    store = Path(store) if store else root / "_local" / "knowledge-sweep" / "cards" / "candidate"
    units = strip_units(root, date, dry_run)
    cards = strip_cards(root, store, date, dry_run)
    rebuilt = bool(units) and not dry_run and rebuild_index(root)
    return {
        "units_changed": len(units),
        "unit_paths_removed": sum(len(u["frontmatter_removed"]) + len(u["body_removed"]) for u in units),
        "cards_changed": len(cards),
        "card_paths_removed": sum(len(v) for c in cards for v in c["removed"].values()),
        "index_rebuilt": rebuilt,
        "dry_run": dry_run,
        "units": units,
        "cards": cards,
    }


def summary(result: dict) -> str:
    mode = "would strip" if result["dry_run"] else "stripped"
    return (
        f"dead paths: {mode} {result['unit_paths_removed']} from {result['units_changed']} unit(s) and "
        f"{result['card_paths_removed']} from {result['cards_changed']} card(s)"
        + ("; knowledge index rebuilt" if result["index_rebuilt"] else "")
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=str(WORKSPACE_ROOT))
    parser.add_argument("--store", default=None, help="card folder (default _local/knowledge-sweep/cards/candidate)")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD recorded in the notes (default today)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    result = run(Path(args.root), args.date, args.dry_run, Path(args.store) if args.store else None)
    print(summary(result))
    for unit in result["units"]:
        print(f"  unit {unit['file']}: {len(unit['frontmatter_removed'])} frontmatter, {len(unit['body_removed'])} body")
    return 0


if __name__ == "__main__":
    sys.exit(main())
