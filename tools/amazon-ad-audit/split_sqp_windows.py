#!/usr/bin/env python3
"""Split a multi-week SQP export into per-window CSVs.

Why this exists: `analyze_audit.parse_sqp` reads EVERY row of each SQP CSV and does
not filter by `windows.sqp_weeks`. That config field is documentation only. So when an
audit needs a specific window (for example a clean pre-incident window separate from
an event window), the window has to be enforced on the FILE, not in the config.

Splitting on "Reporting Date", which the SQP export uses as the week's period-END date.

Usage:
  split_sqp_windows.py --in raw_6wk.csv --out clean.csv --weeks 2026-06-20,2026-06-27
  split_sqp_windows.py --in raw_6wk.csv --list          # show the weeks present
"""
import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

DATE_COL = "Reporting Date"


def weeks_present(path: Path) -> Counter:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        if DATE_COL not in (rd.fieldnames or []):
            sys.exit(f"{path.name}: no '{DATE_COL}' column. Columns: {rd.fieldnames}")
        return Counter(r[DATE_COL].strip() for r in rd)


def split(src: Path, dst: Path, keep: list[str]) -> tuple[int, int]:
    with open(src, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        fields = rd.fieldnames
        rows = [r for r in rd if r[DATE_COL].strip() in keep]
        total = rd.line_num - 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)
    return len(rows), total


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--weeks", help="comma-separated period-END dates to KEEP")
    ap.add_argument("--list", action="store_true", help="list weeks present and exit")
    a = ap.parse_args()

    src = Path(a.src)
    if not src.exists():
        sys.exit(f"missing input: {src}")

    present = weeks_present(src)
    if a.list:
        print(f"{src.name}: {sum(present.values())} rows across {len(present)} weeks")
        for wk in sorted(present):
            print(f"  {wk}  {present[wk]} rows")
        raise SystemExit(0)

    if not (a.dst and a.weeks):
        sys.exit("--out and --weeks are required unless --list")

    keep = [w.strip() for w in a.weeks.split(",") if w.strip()]
    missing = [w for w in keep if w not in present]
    if missing:
        # loud, not silent: a typo'd Saturday would otherwise yield an empty window
        sys.exit(f"requested weeks absent from {src.name}: {missing}\n"
                 f"present: {sorted(present)}")

    kept, total = split(src, Path(a.dst), keep)
    print(f"{src.name} -> {Path(a.dst).name}: kept {kept} of {total} rows, weeks {keep}")
    if kept == 0:
        sys.exit("kept 0 rows: refusing to report success on an empty window")
