#!/usr/bin/env python3
"""List knowledge units that need another look.

Reads knowledge/_index/knowledge-index.json and reports four classes of active
(non-retired) units:
  review_due          review_by month is before the current month
  stale_drafts        status draft and the unit was added more than 30 days ago:
                      the date of the git commit that added the file, or the
                      file mtime when git has no such commit
  changed_sources     verification verified, but a cited amazon_sources capture
                      has a frontmatter downloaded_at later than verified_on
  missing_supersedes  a supersedes path no longer exists

Prints a plain report, or JSON with --json. Always exits 0; this is a worklist,
not a gate. Use --today YYYY-MM-DD to pin the date. Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
INDEX_REL = Path("knowledge") / "_index" / "knowledge-index.json"
DRAFT_MAX_AGE_DAYS = 30
CLASSES = ["review_due", "stale_drafts", "changed_sources", "missing_supersedes"]
TITLES = {
    "review_due": "Past review_by",
    "stale_drafts": f"Drafts older than {DRAFT_MAX_AGE_DAYS} days",
    "changed_sources": "Cited capture downloaded after verified_on",
    "missing_supersedes": "Supersedes path no longer exists",
}
_MONTH_RE = re.compile(r"^[0-9]{4}-[0-9]{2}$")
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def _parse_date(text: str) -> dt.date | None:
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(0))
    except ValueError:
        return None


def git_added_date(root: Path, rel: str) -> dt.date | None:
    """Date of the commit that added `rel`, or None (untracked, no git, error)."""
    try:
        proc = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%cs", "-1", "--", rel],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return _parse_date(proc.stdout.strip())


def draft_added_date(root: Path, rel: str) -> tuple[dt.date, str]:
    """When a draft unit entered the library: (date, "git" or "mtime")."""
    added = git_added_date(root, rel)
    if added is not None:
        return added, "git"
    return dt.date.fromtimestamp((root / rel).stat().st_mtime), "mtime"


def downloaded_at(path: Path) -> dt.date | None:
    """Return the capture's frontmatter downloaded_at date, or None."""
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (OSError, UnicodeDecodeError):
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("downloaded_at:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            return _parse_date(value)
    return None


def status_report(root: Path, today: dt.date) -> dict:
    index_path = root / INDEX_REL
    report: dict = {"today": today.isoformat(), "index": INDEX_REL.as_posix()}
    for name in CLASSES:
        report[name] = []
    if not index_path.is_file():
        report["error"] = f"{INDEX_REL.as_posix()} not found; run tools/knowledge/build_knowledge_index.py"
        return report
    units = json.loads(index_path.read_text(encoding="utf-8")).get("units", [])
    this_month = f"{today.year:04d}-{today.month:02d}"

    for unit in units:
        if unit.get("status") == "retired":
            continue
        uid = unit.get("id", "")
        rel = unit.get("file", "")
        base = {"id": uid, "file": rel, "title": unit.get("title", "")}

        review_by = str(unit.get("review_by", ""))
        if not _MONTH_RE.match(review_by):
            report["review_due"].append({**base, "review_by": review_by, "reason": "review_by missing or invalid"})
        elif review_by < this_month:
            report["review_due"].append({**base, "review_by": review_by, "reason": "past review_by"})

        if unit.get("status") == "draft" and rel:
            path = root / rel
            if path.is_file():
                added, basis = draft_added_date(root, rel)
                age = (today - added).days
                if age > DRAFT_MAX_AGE_DAYS:
                    report["stale_drafts"].append(
                        {**base, "added": added.isoformat(), "added_from": basis, "age_days": age}
                    )

        if unit.get("verification") == "verified":
            verified_on = _parse_date(str(unit.get("verified_on", "")))
            for source in unit.get("amazon_sources", []) or []:
                captured = downloaded_at(root / source)
                if captured is None:
                    continue
                if verified_on is None or captured > verified_on:
                    report["changed_sources"].append(
                        {
                            **base,
                            "source": source,
                            "downloaded_at": captured.isoformat(),
                            "verified_on": unit.get("verified_on", ""),
                        }
                    )

        for target in unit.get("supersedes", []) or []:
            if not (root / target).exists():
                report["missing_supersedes"].append({**base, "path": target})
    return report


def render_text(report: dict) -> str:
    lines = [f"knowledge status on {report['today']}"]
    if report.get("error"):
        lines.append(f"  {report['error']}")
        return "\n".join(lines) + "\n"
    total = 0
    for name in CLASSES:
        entries = report[name]
        total += len(entries)
        lines.append("")
        lines.append(f"{TITLES[name]}: {len(entries)}")
        for entry in entries:
            if name == "review_due":
                detail = f"review_by {entry['review_by'] or 'missing'}"
            elif name == "stale_drafts":
                detail = f"draft, added {entry['added']} per {entry['added_from']} ({entry['age_days']} days)"
            elif name == "changed_sources":
                detail = (
                    f"{entry['source']} downloaded_at {entry['downloaded_at']},"
                    f" verified_on {entry['verified_on'] or 'missing'}"
                )
            else:
                detail = f"missing {entry['path']}"
            lines.append(f"  {entry['id']} {entry['file']}: {detail}")
    lines.append("")
    lines.append(f"total: {total}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print JSON")
    parser.add_argument("--today", help="YYYY-MM-DD, default today")
    parser.add_argument("--root", default=str(WORKSPACE_ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        print(f"kb_status: --today must be YYYY-MM-DD, got {args.today!r}", file=sys.stderr)
        return 0
    report = status_report(Path(args.root), today)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        sys.stdout.write(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
