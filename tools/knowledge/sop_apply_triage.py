#!/usr/bin/env python3
"""Apply approved MAG SOP triage verdicts from triage.csv.

Modes (exactly one):
  --check                       validate verdicts and targets; exit 1 on problems
  --dry-run                     print the git commands and index changes; write nothing
  --apply --approved-by NAME    git rm drop rows, git mv merge rows into
                                MAG SOPs/_archive/<category-folder>/, set index
                                status fields, then slim the index and
                                regenerate the README through slim_sop_index

Status values written to the index: keep -> active, update -> needs-update,
supersede -> superseded, merge -> merged. Drop rows lose their index entry when
slim_sop_index finds the file gone. Rows with an empty verdict are untouched.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import slim_sop_index  # noqa: E402
import sop_triage  # noqa: E402

SOP_DIRNAME = sop_triage.SOP_DIRNAME
STATUS_BY_VERDICT = {
    "keep": "active",
    "update": "needs-update",
    "supersede": "superseded",
    "merge": "merged",
}


def row_key(value: str) -> str:
    value = value.strip()
    prefix = f"{SOP_DIRNAME}/"
    return value[len(prefix):] if value.startswith(prefix) else value


def load_rows(csv_path: Path) -> list[dict]:
    _, rows = sop_triage.read_csv(csv_path)
    for row in rows:
        for key in list(row):
            row[key] = (row[key] or "").strip()
        row["verdict"] = row.get("verdict", "").lower()
    return rows


def check(rows: list[dict], root: Path) -> list[str]:
    problems: list[str] = []
    sop_root = root / SOP_DIRNAME
    by_file: dict[str, dict] = {}
    for row in rows:
        f = row.get("file", "")
        if not f:
            problems.append("row without a file key")
            continue
        if f in by_file:
            problems.append(f"{f}: duplicate row")
        by_file[f] = row

    for row in rows:
        f = row.get("file", "")
        verdict = row.get("verdict", "")
        if verdict not in sop_triage.VERDICTS:
            problems.append(f"{f}: invalid verdict {verdict!r}")
            continue
        if verdict == "supersede":
            target = row.get("superseded_by", "")
            if not target:
                problems.append(f"{f}: supersede without superseded_by")
            elif not slim_sop_index.target_exists(target, root):
                problems.append(f"{f}: superseded_by target does not exist: {target}")
            else:
                other = by_file.get(row_key(target))
                if other and other.get("verdict") in {"drop", "merge"}:
                    problems.append(
                        f"{f}: superseded_by target {target} is itself marked {other['verdict']}"
                    )
        elif verdict == "merge":
            target = row.get("merge_into", "")
            if not target:
                problems.append(f"{f}: merge without merge_into")
            elif row_key(target) == f:
                problems.append(f"{f}: merge_into points at itself")
            elif not slim_sop_index.target_exists(target, root):
                problems.append(f"{f}: merge_into target does not exist: {target}")
            else:
                other = by_file.get(row_key(target))
                if other and other.get("verdict") in {"merge", "drop"}:
                    problems.append(
                        f"{f}: merge_into target {target} is itself marked {other['verdict']}"
                    )
            if not (sop_root / f).exists() and not (sop_root / "_archive" / f).exists():
                problems.append(f"{f}: merge row but the SOP file does not exist")
    return problems


def archive_dest(row: dict) -> str:
    rel = Path(row["file"])
    if len(rel.parts) > 1:
        folder = rel.parts[0]
    else:
        folder = "-".join(row.get("category", "uncategorized").lower().split()) or "uncategorized"
    return f"{SOP_DIRNAME}/_archive/{folder}/{rel.name}"


def plan_git(rows: list[dict], root: Path) -> tuple[list[list[str]], list[str]]:
    sop_root = root / SOP_DIRNAME
    commands: list[list[str]] = []
    problems: list[str] = []
    for row in rows:
        f = row.get("file", "")
        verdict = row.get("verdict", "")
        if verdict == "drop" and (sop_root / f).is_file():
            commands.append(["git", "rm", "-q", "--", f"{SOP_DIRNAME}/{f}"])
        elif verdict == "merge" and (sop_root / f).is_file():
            dest = archive_dest(row)
            if (root / dest).exists():
                problems.append(f"{f}: archive destination already exists: {dest}")
                continue
            commands.append(["git", "mv", "--", f"{SOP_DIRNAME}/{f}", dest])
    return commands, problems


def update_index(data: dict, rows: list[dict], date: str) -> tuple[dict, list[str]]:
    counts = {v: 0 for v in STATUS_BY_VERDICT}
    unmatched: list[str] = []
    entries: dict[str, dict] = {}
    for entry in data.get("captured", []):
        rel = entry.get("file", "")
        entries[rel[len("_archive/"):] if rel.startswith("_archive/") else rel] = entry
    for row in rows:
        verdict = row.get("verdict", "")
        if verdict not in STATUS_BY_VERDICT:
            continue
        entry = entries.get(row["file"])
        if entry is None:
            unmatched.append(row["file"])
            continue
        entry["status"] = STATUS_BY_VERDICT[verdict]
        if verdict == "supersede":
            entry["superseded_by"] = row["superseded_by"]
        else:
            entry.pop("superseded_by", None)
        if verdict == "merge":
            entry["merge_into"] = row["merge_into"]
        else:
            entry.pop("merge_into", None)
        entry["triaged_on"] = date
        flags = sop_triage.split_list(row.get("flags", ""))
        if flags:
            entry["flags"] = flags
        if row.get("knowledge_value"):
            entry["knowledge_value"] = row["knowledge_value"]
        counts[verdict] += 1
    return counts, unmatched


def valid_date(value: str) -> str:
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a YYYY-MM-DD date: {value}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=str(sop_triage.DEFAULT_ROOT), help="workspace root")
    parser.add_argument("--csv", default=None, help="triage CSV (default _local/knowledge-sop-triage/triage.csv)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approved-by", default="", help="name of the operator who approved the verdicts")
    parser.add_argument("--date", type=valid_date, default=dt.date.today().isoformat(), help="triaged_on date")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    csv_path = Path(args.csv) if args.csv else root / sop_triage.DEFAULT_OUT_DIR / "triage.csv"
    if not csv_path.is_absolute():
        csv_path = root / csv_path
    if args.apply and not args.approved_by.strip():
        print("refusing to apply: --approved-by NAME is required", file=sys.stderr)
        return 2
    if not csv_path.exists():
        print(f"error: {csv_path} not found", file=sys.stderr)
        return 1

    rows = load_rows(csv_path)
    problems = check(rows, root)
    if args.check:
        for p in problems:
            print(p)
        decided = sum(1 for r in rows if r.get("verdict"))
        print(f"check: {len(rows)} rows, {decided} with a verdict, {len(problems)} problems")
        return 1 if problems else 0

    commands, plan_problems = plan_git(rows, root)
    problems += plan_problems
    if problems:
        for p in problems:
            print(p)
        print("not applied: fix the problems above (see --check)")
        return 1

    verdict_counts = {v: sum(1 for r in rows if r.get("verdict") == v) for v in sop_triage.VERDICTS if v}
    if args.dry_run:
        for cmd in commands:
            print(shlex.join(cmd))
        print(
            "would set index status: "
            + ", ".join(f"{STATUS_BY_VERDICT[v]} {verdict_counts[v]}" for v in STATUS_BY_VERDICT)
        )
        print(f"would run {len(commands)} git commands; nothing written")
        return 0

    index_path = root / SOP_DIRNAME / "_index" / "sop-index.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries_before = len(data.get("captured", []))

    dropped = merged_moves = 0
    for cmd in commands:
        if cmd[1] == "mv":
            (root / cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"failed: {shlex.join(cmd)}\n{result.stderr.strip()}")
            print(f"stopped after {dropped} removals and {merged_moves} moves; index not updated")
            return 1
        if cmd[1] == "rm":
            dropped += 1
        else:
            merged_moves += 1

    counts, unmatched = update_index(data, rows, args.date)
    if dropped:
        data.setdefault("dropped", [dict(d) for d in slim_sop_index.DEFAULT_DROPPED])
        data["dropped"].append({"what": f"{dropped} SOPs triaged as unusable", "date": args.date})
    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    try:
        result = slim_sop_index.run(write_readme=True, root=root)
    except slim_sop_index.MissingTargets as exc:
        for item in exc.missing:
            print(f"missing target: {item}")
        print("index statuses written but slimming and README regeneration stopped")
        return 1

    for f in unmatched:
        print(f"warning: no index entry for {f}")
    print(f"approved by: {args.approved_by.strip()} on {args.date}")
    print(f"dropped {dropped}")
    print(f"merged {counts['merge']} ({merged_moves} files moved to the archive)")
    print(f"superseded {counts['supersede']}")
    print(f"updated {counts['update']}")
    print(f"kept {counts['keep']}")
    print(f"index entries: {entries_before} before, {result['after']} after")
    print(f"README regenerated: {result['readme_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
