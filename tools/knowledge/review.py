#!/usr/bin/env python3
"""Human review queue, promotion and run notes for knowledge sweep cards.

Works on the gitignored sweep store (default _local/knowledge-sweep/); see
extract_cards.py for the card layout and state.json.

Commands:
  queue [--topic T]
      Render <root>/review-queue.md: one line per candidate card that passes
      extract_cards validation, grouped by topic,
        - [ ] CARD-NNNN · topic · title · resolution_status · confidence · flags · coverage_verdict
      Ticks ("[x]") already in the file are kept.
  promote --card CARD-NNNN --ticked-by ROLE [--confirm-tick] [--agency-lead-override]
      Refuses (exit 2) unless the card's queue line is ticked or --confirm-tick
      is given; when the role may not tick this topic; and when the card has
      policy_risk true or publishable false without --agency-lead-override
      from the agency lead. Then runs new_unit.py --from-card,
      build_knowledge_index.py --readme and lint_knowledge.py --strict. On a
      lint failure the unit file is removed, the staged ledger row is undone,
      the index is rebuilt, the card stays in candidate/ and exit is 1. On
      success the card moves to accepted/, state.json and <root>/ledger.jsonl
      record the promotion, and the unit path is printed.
  reject --card CARD-NNNN --reason TEXT
      Move the card to rejected/ with the reason in state.json.
  import-lessons --vault PATH [--since YYYY-MM-DD] [--min-hits N]
      Read <vault>/Lessons/wizards-ai-lessons.md (never edited) and scaffold
      one card per Amazon-operational lesson: at least N distinct topic
      keywords (default 2) or one error code from topics.json. Lessons already
      imported are skipped.
  run-note --date YYYY-MM-DD --vault PATH [--out PATH] [--force]
      Write <vault>/Runs/<date>-knowledge-sweep.md (or --out) from state.json
      and ledger.jsonl. Refused when WIZARDS_AI_MODE=1. An existing note is
      kept unless --force.

Roles (docs/knowledge-library.md): agency-lead ticks any card, ads-lead ads
cards, operations-lead logistics, catalog, support-cases and account-health
cards. Only the agency lead decides policy-risk or not-publishable cards.

Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import extract_cards as ec  # noqa: E402
import scrub  # noqa: E402
import slack_collect as sc  # noqa: E402

PYTHON = "python3"
QUEUE_NAME = "review-queue.md"
LEDGER_NAME = "ledger.jsonl"
STAGING_NAME = "ledger-staging.md"
LESSONS_REL = Path("Lessons") / "wizards-ai-lessons.md"
RUNS_REL = Path("Runs")
SEP = " \u2014 "
DOT = " · "
TITLE_MAX = 110

ROLE_TOPICS = {
    "agency-lead": None,
    "ads-lead": {"ads"},
    "operations-lead": {"logistics", "catalog", "support-cases", "account-health"},
}
QUEUE_LINE = re.compile(r"^- \[([ xX])\] (CARD-[0-9]{4,})\b")
LESSON_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2})" + re.escape(SEP))
UNIT_WROTE = re.compile(r"^wrote (knowledge/\S+\.md)\s*$", re.M)


def _store(args: argparse.Namespace) -> ec.Store:
    return ec._store(args)


def _today(args: argparse.Namespace) -> str:
    return args.today or dt.date.today().isoformat()


# ---------------------------------------------------------------- queue


def card_flags(card: dict) -> list[str]:
    flags = []
    if card.get("policy_risk") is True:
        flags.append("policy_risk")
    if card.get("publishable") is False:
        flags.append("publishable=false")
    if card.get("participants_external") is True:
        flags.append("external")
    return flags


def queue_line(card: dict, ticked: bool) -> str:
    title = " ".join(str(card.get("title") or "").split())
    parts = [
        str(card.get("card_id")),
        str(card.get("topic")),
        title,
        str(card.get("resolution_status")),
        str(card.get("confidence")),
        ", ".join(card_flags(card)) or "no flags",
        str(card.get("coverage_verdict") or "unchecked"),
    ]
    return f"- [{'x' if ticked else ' '}] " + DOT.join(parts)


def read_ticks(path: Path) -> dict[str, bool]:
    ticks: dict[str, bool] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            m = QUEUE_LINE.match(line)
            if m:
                ticks[m.group(2)] = m.group(1) in "xX"
    return ticks


def render_queue(store: ec.Store, topic: str | None, queue_path: Path) -> tuple[str, int, list[str]]:
    terms = store.terms()
    schema = json.loads(ec.CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    ticks = read_ticks(queue_path)
    grouped: dict[str, list[dict]] = defaultdict(list)
    invalid: list[str] = []
    folder = store.cards / "candidate"
    for path in sorted(folder.glob("CARD-*.json")) if folder.is_dir() else []:
        card = ec.load_card(path)
        if topic and card.get("topic") != topic:
            continue
        if ec.validate_card(card, store.repo, terms, schema):
            invalid.append(path.stem)
            continue
        grouped[str(card.get("topic"))].append(card)
    lines = [
        "# Knowledge sweep review queue",
        "",
        "Tick a line with [x] to approve the card for promotion, then run",
        "`python3 tools/knowledge/review.py promote --card CARD-NNNN --ticked-by <role>`.",
        "Flags: policy_risk and publishable=false need the agency lead; external means client, supplier or Amazon staff wrote in the thread.",
        "",
    ]
    count = 0
    for name in sorted(grouped):
        lines.append(f"## {name}")
        lines.append("")
        for card in sorted(grouped[name], key=lambda c: str(c.get("card_id"))):
            lines.append(queue_line(card, ticks.get(str(card.get("card_id")), False)))
            count += 1
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n", count, invalid


def cmd_queue(args: argparse.Namespace) -> int:
    store = _store(args)
    queue_path = Path(args.queue) if args.queue else store.root / QUEUE_NAME
    text, count, invalid = render_queue(store, args.topic, queue_path)
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    queue_path.write_text(text, encoding="utf-8")
    print(f"queue: {count} card(s) in {queue_path}")
    if invalid:
        print(f"queue: {len(invalid)} candidate card(s) left out because they fail validation: {', '.join(invalid)}")
    return 0


# ---------------------------------------------------------------- promote


def run_tool(repo: Path, script: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PYTHON, str(repo / "tools" / "knowledge" / script), *extra],
        capture_output=True,
        text=True,
        cwd=str(repo),
        check=False,
    )


def _echo(proc: subprocess.CompletedProcess) -> None:
    for stream in (proc.stdout, proc.stderr):
        if stream and stream.strip():
            print(stream.rstrip())


def append_ledger(store: ec.Store, row: dict) -> None:
    path = store.root / LEDGER_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _set_status(unit_path: Path, status: str) -> None:
    """Rewrite the unit's frontmatter status line in place (draft to reviewed on a human tick)."""
    text = unit_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("status:"):
            lines[i] = f"status: {status}"
            break
        if i > 0 and line.strip() == "---":
            break
    unit_path.write_text("\n".join(lines), encoding="utf-8")


def cmd_promote(args: argparse.Namespace) -> int:
    store = _store(args)
    card_path = store.cards / "candidate" / f"{args.card}.json"
    if not card_path.is_file():
        print(f"promote: {args.card} is not in {card_path.parent}", file=sys.stderr)
        return 2
    card = ec.load_card(card_path)
    topic = str(card.get("topic"))

    if args.ticked_by not in ROLE_TOPICS:
        print(f"promote: --ticked-by must be one of {', '.join(ROLE_TOPICS)}", file=sys.stderr)
        return 2
    allowed = ROLE_TOPICS[args.ticked_by]
    if allowed is not None and topic not in allowed:
        print(f"promote: {args.ticked_by} does not tick {topic} cards; the agency lead does", file=sys.stderr)
        return 2

    queue_path = Path(args.queue) if args.queue else store.root / QUEUE_NAME
    if not read_ticks(queue_path).get(args.card) and not args.confirm_tick:
        print(
            f"promote: {args.card} is not ticked [x] in {queue_path}; tick it there, or pass --confirm-tick"
            f" when {args.ticked_by} approved it in this session",
            file=sys.stderr,
        )
        return 2

    risky = card.get("policy_risk") is True or card.get("publishable") is False
    if risky:
        if not args.agency_lead_override or args.ticked_by != "agency-lead":
            print(
                f"promote: {args.card} has {', '.join(f for f in card_flags(card) if f != 'external')};"
                " only the agency lead decides it (--ticked-by agency-lead --agency-lead-override)",
                file=sys.stderr,
            )
            return 2
        if card.get("publishable") is False:
            print(
                f"promote: {args.card} is publishable: false and new_unit.py refuses such cards. If the agency lead"
                " decided it generalises, set publishable to true in the card and promote again; otherwise reject it.",
                file=sys.stderr,
            )
            return 2

    problems = ec.validate_card(card, store.repo, store.terms())
    if problems:
        for problem in problems:
            print(f"promote: {args.card}: {problem}", file=sys.stderr)
        return 1

    staging = store.root / STAGING_NAME
    staging_before = staging.read_text(encoding="utf-8") if staging.is_file() else None
    today = _today(args)
    root_args = ["--root", str(store.repo)]

    proc = run_tool(store.repo, "new_unit.py", "--from-card", str(card_path), "--staging", str(staging), "--today", today, *root_args)
    _echo(proc)
    match = UNIT_WROTE.search(proc.stdout or "")
    if proc.returncode != 0 or not match:
        print(f"promote: new_unit.py failed (exit {proc.returncode}); {args.card} stays in candidate/", file=sys.stderr)
        return 1
    unit_rel = match.group(1)
    unit_path = store.repo / unit_rel

    build = run_tool(store.repo, "build_knowledge_index.py", "--readme", *root_args)
    _echo(build)
    lint_args = ["--strict", *root_args]
    if args.terms:
        lint_args += ["--terms", args.terms]
    lint = run_tool(store.repo, "lint_knowledge.py", *lint_args) if build.returncode == 0 else build
    if build.returncode != 0 or lint.returncode != 0:
        if lint is not build:
            _echo(lint)
        if unit_path.is_file():
            unit_path.unlink()
        if staging_before is None:
            if staging.is_file():
                staging.unlink()
        else:
            staging.write_text(staging_before, encoding="utf-8")
        rebuild = run_tool(store.repo, "build_knowledge_index.py", "--readme", *root_args)
        step = "build_knowledge_index.py" if build.returncode != 0 else "lint_knowledge.py --strict"
        print(
            f"promote: {step} failed; removed {unit_rel}, restored the ledger staging file,"
            f" rebuilt the index (exit {rebuild.returncode}); {args.card} stays in candidate/",
            file=sys.stderr,
        )
        return 1

    # The human tick is what promote verified, so the unit leaves draft here.
    _set_status(unit_path, "reviewed")
    rebuild_after_tick = run_tool(store.repo, "build_knowledge_index.py", "--readme", *root_args)
    if rebuild_after_tick.returncode != 0:
        _echo(rebuild_after_tick)
    accepted = store.cards / "accepted" / card_path.name
    accepted.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(card_path), str(accepted))
    unit_id = Path(unit_rel).name.split("_", 1)[0]
    state = store.load_state()
    state["cards"][args.card] = {
        "status": "promoted",
        "card": args.card,
        "unit_id": unit_id,
        "unit_path": unit_rel,
        "topic": topic,
        "ticked_by": args.ticked_by,
        "promoted_on": today,
    }
    channel_id, parent_ts = str(card.get("channel_id") or ""), str(card.get("parent_ts") or "")
    if channel_id and parent_ts:
        entry = state["threads"].get(ec.thread_key(channel_id, parent_ts), {})
        entry.update({"status": "promoted", "card": args.card, "updated": ec.now_iso()})
        state["threads"][ec.thread_key(channel_id, parent_ts)] = entry
    store.save_state(state)
    append_ledger(
        store,
        {
            "card": args.card,
            "unit_id": unit_id,
            "unit_path": unit_rel,
            "topic": topic,
            "source_kind": card.get("source_kind", ""),
            "channel_id": channel_id,
            "channel_name": card.get("channel_name", ""),
            "client_slug": card.get("client_slug", ""),
            "parent_ts": parent_ts,
            "permalink": card.get("permalink", ""),
            "ticked_by": args.ticked_by,
            "promoted_on": today,
        },
    )
    print(unit_rel)
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    store = _store(args)
    card_path = store.cards / "candidate" / f"{args.card}.json"
    if not card_path.is_file():
        print(f"reject: {args.card} is not in {card_path.parent}", file=sys.stderr)
        return 2
    card = ec.load_card(card_path)
    target = store.cards / "rejected" / card_path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(card_path), str(target))
    state = store.load_state()
    today = _today(args)
    state["cards"][args.card] = {"status": "rejected", "card": args.card, "reason": args.reason, "rejected_on": today,
                                 "topic": card.get("topic", "")}
    channel_id, parent_ts = str(card.get("channel_id") or ""), str(card.get("parent_ts") or "")
    if channel_id and parent_ts:
        entry = state["threads"].get(ec.thread_key(channel_id, parent_ts), {})
        entry.update({"status": "rejected", "card": args.card, "reason": args.reason, "updated": ec.now_iso()})
        state["threads"][ec.thread_key(channel_id, parent_ts)] = entry
    store.save_state(state)
    print(f"rejected {args.card}: {target}")
    return 0


# ---------------------------------------------------------------- lessons


def parse_lesson(line: str) -> dict | None:
    """{date, agent, text, evidence} for one Lessons entry, or None."""
    if not LESSON_LINE.match(line):
        return None
    parts = line[2:].split(SEP)
    if len(parts) < 3:
        return None
    date, agent = parts[0].strip(), parts[1].strip()
    if len(parts) == 3:
        text, evidence = parts[2], ""
    else:
        text, evidence = SEP.join(parts[2:-1]), parts[-1]
    return {"date": date, "agent": agent, "text": text.strip(), "evidence": evidence.strip()}


def first_clause(text: str) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0].rstrip(".")
    if len(sentence) <= TITLE_MAX:
        return sentence
    cut = sentence[:TITLE_MAX]
    return cut[: cut.rfind(" ")] if " " in cut else cut


def lesson_card(card_id: str, lesson: dict, topic: str, lexicon: sc.Lexicon, terms: list[str]) -> dict:
    card = ec.empty_card(card_id, "lesson", topic, list(lexicon.topics[topic]["skills"]))
    full = f"{lesson['text']} {lesson['evidence']}"
    identifiers = ec.identifiers_in(full)
    strip = list(identifiers)
    for hit in scrub.find_hits(full, terms):
        if hit.pattern.startswith("term:") and hit.match not in strip:
            strip.append(hit.match)
    card.update(
        {
            "kind": "rule",
            "title": first_clause(lesson["text"]),
            "generic_lesson": lesson["text"],
            "error_text": lexicon.code_hits(full),
            "fix_source": "agency",
            "evidence_location": "run-note" if lesson["evidence"] else "none",
            "client_specific_to_strip": strip,
            "identifiers": identifiers,
            "date_first_seen": lesson["date"],
            "notes": lesson["evidence"],
        }
    )
    return card


def cmd_import_lessons(args: argparse.Namespace) -> int:
    store = _store(args)
    lexicon = sc.Lexicon(sc.load_topics(args.topics or sc.TOPICS_PATH))
    path = Path(args.vault) / LESSONS_REL
    if not path.is_file():
        print(f"import-lessons: {path} not found", file=sys.stderr)
        return 1
    terms = store.terms()
    state = store.load_state()
    created, skipped_known, skipped_other = [], 0, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        lesson = parse_lesson(line)
        if lesson is None:
            continue
        if args.since and lesson["date"] < args.since:
            continue
        text = lesson["text"]
        hits = lexicon.keyword_hits(text)
        codes = lexicon.code_hits(text)
        if len(hits) < args.min_hits and not codes:
            skipped_other += 1
            continue
        key = hashlib.sha1(line.strip().encode("utf-8")).hexdigest()[:16]
        if key in state["lessons"]:
            skipped_known += 1
            continue
        topic, _score = sc.best_topic(lexicon.topic_scores([text]), None)
        if topic not in lexicon.topics:
            skipped_other += 1
            continue
        card_id = store.next_card_id()
        card = lesson_card(card_id, lesson, topic, lexicon, terms)
        ec.write_card(store.cards / "candidate" / f"{card_id}.json", card)
        state["lessons"][key] = {"card": card_id, "date": lesson["date"], "topic": topic, "imported": ec.now_iso()}
        created.append(f"{card_id} {topic}")
    store.save_state(state)
    for line in created:
        print(f"scaffolded {line}")
    print(f"import-lessons: {len(created)} card(s); {skipped_known} already imported; {skipped_other} not Amazon-operational")
    return 0


# ---------------------------------------------------------------- run note


def _cell(value: object) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def build_run_note(store: ec.Store, date: str) -> str:
    state = store.load_state()
    rows = []
    ledger = store.root / LEDGER_NAME
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                if row.get("promoted_on") == date:
                    rows.append(row)
    rejected = [c for c, v in state["cards"].items() if v.get("status") == "rejected" and v.get("rejected_on") == date]
    folder = store.cards / "candidate"
    pending = len(list(folder.glob("CARD-*.json"))) if folder.is_dir() else 0
    lines = [
        "---",
        "type: run",
        f"date: {date}",
        "workflow: knowledge-sweep",
        "status: complete",
        "---",
        "",
        f"# Knowledge sweep {date}",
        "",
        f"Promoted {len(rows)} card(s) into knowledge units and rejected {len(rejected)}. {pending} candidate card(s)"
        " wait for review. Units enter as draft and unverified; the ledger rows were staged by new_unit.py and"
        " move into Runs/amazon-knowledge-ledger.md with `ledger.py append --from-staging`.",
        "",
        "| Card | Unit | Topic | Channel | Client slug | Permalink | Ticked by |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(
                _cell(row.get(k)) for k in ("card", "unit_id", "topic", "channel_name", "client_slug", "permalink", "ticked_by")
            ) + " |"
        )
    if not rows:
        lines.append("| none | | | | | | |")
    if rejected:
        lines += ["", "Rejected: " + ", ".join(sorted(rejected)) + "."]
    return "\n".join(lines) + "\n"


def cmd_run_note(args: argparse.Namespace) -> int:
    if os.environ.get("WIZARDS_AI_MODE", "").strip() == "1":
        print("run-note: writes the team vault and is attended only; refused because WIZARDS_AI_MODE=1", file=sys.stderr)
        return 2
    try:
        dt.date.fromisoformat(args.date)
    except ValueError:
        print(f"run-note: --date must be YYYY-MM-DD, got {args.date!r}", file=sys.stderr)
        return 2
    store = _store(args)
    if args.out:
        target = Path(args.out)
    else:
        if not args.vault:
            print("run-note: --vault or --out is required", file=sys.stderr)
            return 2
        target = Path(args.vault) / RUNS_REL / f"{args.date}-knowledge-sweep.md"
    if target.exists() and not args.force:
        print(f"run-note: {target} exists; pass --force to rewrite it", file=sys.stderr)
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_run_note(store, args.date), encoding="utf-8")
    print(f"wrote {target}")
    return 0


# ---------------------------------------------------------------- cli


def build_parser() -> argparse.ArgumentParser:
    common = ec.common_parser()
    common.add_argument("--today", help=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("queue", parents=[common], help="render the review queue")
    p.add_argument("--topic")
    p.add_argument("--queue", help="queue file (default <root>/review-queue.md)")
    p.set_defaults(func=cmd_queue)

    p = sub.add_parser("promote", parents=[common], help="promote a ticked card into a unit")
    p.add_argument("--card", required=True)
    p.add_argument("--ticked-by", required=True, help="agency-lead, ads-lead or operations-lead")
    p.add_argument("--queue", help="queue file (default <root>/review-queue.md)")
    p.add_argument("--confirm-tick", action="store_true", help="the named role approved this card outside the queue file")
    p.add_argument("--agency-lead-override", action="store_true", help="the agency lead decided a policy-risk card")
    p.set_defaults(func=cmd_promote)

    p = sub.add_parser("reject", parents=[common], help="reject a candidate card")
    p.add_argument("--card", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_reject)

    p = sub.add_parser("import-lessons", parents=[common], help="scaffold cards from the vault Lessons file")
    p.add_argument("--vault", required=True)
    p.add_argument("--since", help="YYYY-MM-DD")
    p.add_argument("--min-hits", type=int, default=2, help="distinct topic keywords a lesson needs (default 2)")
    p.set_defaults(func=cmd_import_lessons)

    p = sub.add_parser("run-note", parents=[common], help="write the sweep run note")
    p.add_argument("--date", required=True)
    p.add_argument("--vault")
    p.add_argument("--out")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_run_note)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
