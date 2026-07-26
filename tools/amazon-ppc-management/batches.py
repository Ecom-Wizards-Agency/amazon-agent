#!/usr/bin/env python3
"""Batch log for staged PPC applies (client-agnostic).

Staged-apply standard: a batch is ONE opt-group, never the whole account; several
levers may land together inside a group's batch, each row labeled with its lever.
Before any apply, snapshot the old -> new rows here; the file is the revert source
and the cooldown ledger. Data lives under _local/ppc-manage/<client>/batches/
(gitignored).

Commands:
  snapshot       write a batch file from a rows JSON (fails on cooldown conflicts)
  validate       caps-are-ceilings check: error on over-cap deltas, flag at-cap
                 and off-formula rows (a cap clamps the formula, it is never the step)
  check          report which candidate entities are still inside the cooldown
  status         list batches for a client (age, status, scored or open)
  score          record the read-before-write verdict on a batch
  revert         emit the old values as an update payload (the write itself
                 stays in the agent's preview -> approval -> apply gate)
  mark-reverted  flag a batch as reverted after the revert write is applied

rows JSON shape (list): {"entity_type": "keyword|target|campaign|ad_group|placement",
"entity_id": "...", "field": "bid|budget|state|tos_modifier|...", "old": ..., "new": ...,
"name": "optional label"}
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = REPO_ROOT / "_local" / "ppc-manage"
KNOWN_LEVERS = {
    "waste-cut", "bid-down", "push", "budget", "placement",
    "harvest", "negative", "pause", "revert", "other",
}
ROW_KEYS = {"entity_type", "entity_id", "field", "old", "new"}


def batches_dir(base: Path, client: str) -> Path:
    return base / client / "batches"


def load_batches(base: Path, client: str):
    out = []
    d = batches_dir(base, client)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.json")):
        try:
            out.append((p, json.loads(p.read_text())))
        except json.JSONDecodeError:
            print(f"WARN: unreadable batch file skipped: {p}", file=sys.stderr)
    return out


def entity_key(row) -> str:
    return f"{row['entity_type']}:{row['entity_id']}"


def cooldown_conflicts(base: Path, client: str, rows, cooldown_days: int, today: dt.date):
    """Entities in `rows` that an applied batch touched within the cooldown."""
    conflicts = []
    candidate = {entity_key(r) for r in rows}
    for path, batch in load_batches(base, client):
        if batch.get("status") != "applied":
            continue
        applied = dt.date.fromisoformat(batch["date"])
        age = (today - applied).days
        if age >= cooldown_days:
            continue
        for r in batch.get("rows", []):
            k = entity_key(r)
            if k in candidate:
                conflicts.append({
                    "entity": k,
                    "name": r.get("name", ""),
                    "batch": batch["tag"],
                    "applied": batch["date"],
                    "days_ago": age,
                    "free_on": (applied + dt.timedelta(days=cooldown_days)).isoformat(),
                })
    return conflicts


def validate_rows(rows):
    if not isinstance(rows, list) or not rows:
        sys.exit("rows JSON must be a non-empty list")
    for i, r in enumerate(rows):
        missing = ROW_KEYS - set(r)
        if missing:
            sys.exit(f"row {i} missing keys: {sorted(missing)}")


def cmd_snapshot(a, base):
    rows = json.loads(Path(a.rows).read_text())
    validate_rows(rows)
    for lever in a.lever.split(","):
        if lever not in KNOWN_LEVERS:
            print(f"WARN: lever '{lever}' not in {sorted(KNOWN_LEVERS)}", file=sys.stderr)
    today = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    conflicts = cooldown_conflicts(base, a.client, rows, a.cooldown_days, today)
    if conflicts and not a.bypass_cooldown:
        print(json.dumps(conflicts, indent=2))
        sys.exit(f"{len(conflicts)} entities inside the {a.cooldown_days}d cooldown; "
                 "drop them from the batch or pass --bypass-cooldown <reason>")
    path = batches_dir(base, a.client) / f"{a.tag}.json"
    if path.exists() and not a.force:
        sys.exit(f"batch exists: {path} (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "tag": a.tag,
        "client": a.client,
        "date": today.isoformat(),
        "lever": a.lever,
        "opt_group": a.group,
        "note": a.note,
        "status": "applied",
        "cooldown_bypass": a.bypass_cooldown,
        "score": None,
        "rows": rows,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"snapshot written: {path} ({len(rows)} rows"
          + (f", cooldown bypassed: {a.bypass_cooldown}" if a.bypass_cooldown else "") + ")")


def cmd_validate(a, base):
    """Caps are ceilings, never steps: flag deltas that exceed the group's max
    change, and at-cap deltas that look authored instead of formula-clamped."""
    rows = json.loads(Path(a.rows).read_text())
    validate_rows(rows)
    errors, flagged, checked = [], [], 0
    for r in rows:
        old, new = r["old"], r["new"]
        if not (isinstance(old, (int, float)) and isinstance(new, (int, float))) or old <= 0:
            continue
        checked += 1
        delta = (new - old) / old
        label = f"{entity_key(r)} {r.get('name', '')} {r['field']} {old} -> {new} ({delta:+.1%})"
        cap = a.max_increase if delta > 0 else a.max_decrease
        if cap is None:
            continue
        if abs(delta) > cap + a.at_cap_tolerance:
            errors.append(f"OVER CAP ({cap:.0%}): {label}")
        elif abs(abs(delta) - cap) <= a.at_cap_tolerance:
            flagged.append(f"AT CAP ({cap:.0%}): {label}")
        if a.tacos and r.get("clicks") and r.get("revenue") and r["field"] == "bid":
            expected = r["revenue"] / r["clicks"] * a.tacos
            if expected > 0 and abs(new - expected) / expected > 0.25:
                flagged.append(f"OFF FORMULA (rpc x tacos = {expected:.2f}): {label}")
    for line in errors + flagged:
        print(line)
    print(f"{checked} numeric rows checked: {len(errors)} over cap, "
          f"{len(flagged)} flagged (at-cap / off-formula)", file=sys.stderr)
    if errors:
        sys.exit("over-cap deltas present: a cap is a ceiling, never the step; "
                 "re-derive these from the optimizer preview")
    if flagged and a.strict:
        sys.exit("flagged rows present with --strict")


def cmd_check(a, base):
    rows = json.loads(Path(a.rows).read_text()) if a.rows else [
        {"entity_type": t, "entity_id": i, "field": "-", "old": None, "new": None}
        for t, _, i in (s.partition(":") for s in a.ids.split(","))
    ]
    today = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    conflicts = cooldown_conflicts(base, a.client, rows, a.cooldown_days, today)
    print(json.dumps(conflicts, indent=2))
    print(f"{len(conflicts)} of {len(rows)} candidate entities inside the "
          f"{a.cooldown_days}d cooldown", file=sys.stderr)


def cmd_status(a, base):
    today = dt.date.fromisoformat(a.date) if a.date else dt.date.today()
    batches = load_batches(base, a.client)
    if not batches:
        print(f"no batches for {a.client}")
        return
    for _, b in batches:
        age = (today - dt.date.fromisoformat(b["date"])).days
        scored = "scored" if b.get("score") else (
            "DUE FOR SCORING" if age >= a.cooldown_days and b["status"] == "applied" else "open")
        print(f"{b['tag']}  {b['date']} ({age}d)  {b['opt_group']}/{b['lever']}  "
              f"{len(b.get('rows', []))} rows  {b['status']}  {scored}")


def find_batch(base, client, tag):
    for path, b in load_batches(base, client):
        if b["tag"] == tag:
            return path, b
    sys.exit(f"no batch tagged {tag} for {client}")


def cmd_score(a, base):
    path, b = find_batch(base, a.client, a.tag)
    b["score"] = {"date": (a.date or dt.date.today().isoformat()), "verdict": a.verdict}
    path.write_text(json.dumps(b, indent=2, ensure_ascii=False) + "\n")
    print(f"scored {a.tag}: {a.verdict}")


def cmd_revert(a, base):
    _, b = find_batch(base, a.client, a.tag)
    payload = [{
        "entity_type": r["entity_type"],
        "entity_id": r["entity_id"],
        "name": r.get("name", ""),
        "field": r["field"],
        "value": r["old"],
        "reverts": r["new"],
    } for r in b["rows"]]
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(text + "\n")
        print(f"revert payload ({len(payload)} rows) -> {a.out}")
    else:
        print(text)
    print(f"apply via update_entities behind the write gate, then: "
          f"batches.py mark-reverted --client {a.client} --tag {a.tag}", file=sys.stderr)


def cmd_mark_reverted(a, base):
    path, b = find_batch(base, a.client, a.tag)
    b["status"] = "reverted"
    b["reverted"] = {"date": (a.date or dt.date.today().isoformat()), "note": a.note}
    path.write_text(json.dumps(b, indent=2, ensure_ascii=False) + "\n")
    print(f"{a.tag} marked reverted")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-dir", default=str(DEFAULT_BASE),
                    help="batch store root (default: _local/ppc-manage)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, cooldown=True):
        p.add_argument("--client", required=True, help="client slug")
        p.add_argument("--date", help="override today (YYYY-MM-DD), e.g. for backfill")
        if cooldown:
            p.add_argument("--cooldown-days", type=int, default=7)

    p = sub.add_parser("snapshot", help="write a batch file before applying")
    common(p)
    p.add_argument("--tag", required=True, help="<client>-<YYYY>W<ww>-<group>-<lever>")
    p.add_argument("--lever", required=True)
    p.add_argument("--group", required=True, help="opt-group (rank/discovery/profit/shield/...)")
    p.add_argument("--note", required=True, help="same note passed to the apply call")
    p.add_argument("--rows", required=True, help="path to rows JSON")
    p.add_argument("--bypass-cooldown", metavar="REASON",
                   help="stock gate / fraud budget cap / pacing act")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("validate", help="caps-are-ceilings check on a rows JSON")
    p.add_argument("--rows", required=True, help="path to rows JSON")
    p.add_argument("--max-increase", type=float, help="group cap as fraction, e.g. 0.25")
    p.add_argument("--max-decrease", type=float, help="group cap as fraction, e.g. 0.10")
    p.add_argument("--at-cap-tolerance", type=float, default=0.005)
    p.add_argument("--tacos", type=float,
                   help="group target ACOS as fraction; enables rpc x tacos formula check "
                        "on rows that carry clicks + revenue")
    p.add_argument("--strict", action="store_true", help="fail on at-cap/off-formula flags too")

    p = sub.add_parser("check", help="cooldown check for candidate entities")
    common(p)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--rows", help="path to rows JSON")
    g.add_argument("--ids", help="comma-separated entity_type:entity_id list")

    p = sub.add_parser("status", help="list batches")
    common(p)

    p = sub.add_parser("score", help="record the read-before-write verdict")
    common(p, cooldown=False)
    p.add_argument("--tag", required=True)
    p.add_argument("--verdict", required=True,
                   help="e.g. 'worked: ACOS -4pp, rank held' / 'confounded: OOS day 2'")

    p = sub.add_parser("revert", help="emit old values as an update payload")
    common(p, cooldown=False)
    p.add_argument("--tag", required=True)
    p.add_argument("--out")

    p = sub.add_parser("mark-reverted", help="flag a batch reverted after the write")
    common(p, cooldown=False)
    p.add_argument("--tag", required=True)
    p.add_argument("--note", default="")

    a = ap.parse_args()
    base = Path(a.base_dir)
    {"snapshot": cmd_snapshot, "validate": cmd_validate, "check": cmd_check,
     "status": cmd_status, "score": cmd_score, "revert": cmd_revert,
     "mark-reverted": cmd_mark_reverted}[a.cmd](a, base)


if __name__ == "__main__":
    main()
