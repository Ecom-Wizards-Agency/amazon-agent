#!/usr/bin/env python3
"""Turn sweep candidates into knowledge cards for an extraction agent.

Works on the gitignored sweep store (default _local/knowledge-sweep/):

  candidates.jsonl                 written by slack_collect.py candidates
  cards/candidate|accepted|rejected/CARD-NNNN.json
  cards/state.json                 {"threads": {"<channel_id>:<thread_ts>": {...}},
                                    "cards": {"CARD-NNNN": {...}}, "lessons": {...}}

Commands:
  next --topic T --batch N [--family F]
      Print the next N uncarded candidates for a topic: every message with its
      user ID and ts, then a scrubbed preview (scrub.redact with the regex
      classes and the denylist when present) that shows what must be stripped.
  scaffold --thread CHANNEL:TS [--topic T]
      Write cards/candidate/CARD-NNNN.json (next free number across candidate,
      accepted and rejected) with provenance prefilled from the record and the
      config, and empty content fields for the agent. Marks the thread
      scaffolded.
  validate CARD...
      Schema check against tools/knowledge/card.schema.json plus: title,
      problem_as_asked and generic_lesson are not empty; title,
      generic_lesson, problem_as_asked, root_cause, resolution_steps and verify
      carry no scrub regex hit, no denylist term and no client_specific_to_strip
      token; every path in first_party_source_paths, related_sop_paths,
      coverage_paths and contradicts_paths exists under the repo; every
      marketplace is one the unit lint accepts and every skill has a folder
      under skills/.
  coverage CARD...
      Search the local libraries for the card and set coverage_verdict and
      coverage_paths (see COVERAGE RULE below). net_new is left to the agent.
  mark --thread CHANNEL:TS --status carded|skipped [--card CARD-NNNN] [--reason ...]
      Record the extraction decision in state.json.

CARD arguments are paths or ids (CARD-0042 is looked up in candidate/,
accepted/ and rejected/).

COVERAGE RULE. The card is searched with tools/search_amazon_libraries.py
(subprocess, --library all) once with its symptom keywords joined (the title
when there are none) and once per error_text entry; skills/ and docs/ are
grepped for the two most distinctive title words (the two that appear in the
fewest files, ignoring words absent from both trees).
  full     a knowledge unit or a first-party capture (Amazon Seller Help,
           Amazon Ads Help, Advertising Help After Login) scores >= 300. A
           score that high means the whole query phrase sits in the text and
           most terms hit the title or path.
  partial  any search hit scores >= 150 (the phrase appears in the text), or a
           skills/ or docs/ file contains both distinctive title words.
  none     otherwise.
coverage_paths keeps the top five repo-relative paths, search hits by score
first, then grep hits; paths outside the repo are dropped.

Stdlib only.
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

import scrub  # noqa: E402
import slack_collect as sc  # noqa: E402
from kb_frontmatter import MARKETPLACES  # noqa: E402

WORKSPACE_ROOT = HERE.parents[1]
CARD_SCHEMA_PATH = HERE / "card.schema.json"
DEFAULT_TERMS = WORKSPACE_ROOT / "_local" / "knowledge-redaction-terms.txt"
SEARCH_SCRIPT = Path("tools") / "search_amazon_libraries.py"
PYTHON = "python3"

CARD_DIRS = ("candidate", "accepted", "rejected")
CARD_RE = re.compile(r"^CARD-([0-9]{4,})$")
IDENTIFIER_CLASSES = ("asin", "shipment_id", "order_id", "case_id", "merchant_token")
SCRUBBED_FIELDS = ("title", "generic_lesson", "problem_as_asked", "root_cause", "resolution_steps", "verify")
NONEMPTY_FIELDS = ("title", "problem_as_asked", "generic_lesson")
PATH_FIELDS = ("first_party_source_paths", "related_sop_paths", "coverage_paths", "contradicts_paths")
DONE_STATUSES = ("scaffolded", "carded", "skipped", "promoted", "rejected")

FULL_SCORE = 300
PARTIAL_SCORE = 150
FIRST_PARTY_LIBRARIES = ("Amazon Seller Help", "Amazon Ads Help", "Advertising Help After Login")
FULL_LIBRARIES = ("Amazon Knowledge",) + FIRST_PARTY_LIBRARIES
COVERAGE_TOP = 5
SEARCH_LIMIT = 10
STOPWORDS = frozenset(
    "a an and are as at be by can cannot does doesn don for from has have how in into is it its not of on or"
    " the then this to was what when where which while why will with without after before still shows shown"
    " amazon seller sellers listing listings".split()
)


# ---------------------------------------------------------------- paths and state


class Store:
    def __init__(self, root: Path, repo: Path, config_path: Path | None = None, terms_path: Path | None = None) -> None:
        self.root = root
        self.repo = repo
        self.config_path = config_path or root / "config.json"
        self.terms_path = terms_path or DEFAULT_TERMS
        self.cards = root / "cards"
        self.state_path = self.cards / "state.json"

    def config(self) -> dict:
        return sc.load_config(self.config_path)

    def terms(self) -> list[str]:
        return scrub.load_terms(self.terms_path)

    def load_state(self) -> dict:
        if self.state_path.is_file():
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        else:
            data = {}
        for key in ("threads", "cards", "lessons"):
            data.setdefault(key, {})
        return data

    def save_state(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    def record_path(self, channel_id: str, ts: str) -> Path:
        return self.root / "threads" / channel_id / f"{ts}.json"

    def next_card_id(self) -> str:
        highest = 0
        for sub in CARD_DIRS:
            folder = self.cards / sub
            if not folder.is_dir():
                continue
            for path in folder.glob("CARD-*.json"):
                m = CARD_RE.match(path.stem)
                if m:
                    highest = max(highest, int(m.group(1)))
        return f"CARD-{highest + 1:04d}"

    def find_card(self, ref: str) -> Path:
        path = Path(ref)
        if path.suffix == ".json" and path.is_file():
            return path
        for sub in CARD_DIRS:
            candidate = self.cards / sub / f"{ref}.json"
            if candidate.is_file():
                return candidate
        raise SystemExit(f"extract_cards: card not found: {ref}")


def parse_thread_ref(ref: str) -> tuple[str, str]:
    if ":" not in ref:
        raise SystemExit(f"extract_cards: --thread must be CHANNEL:TS, got {ref!r}")
    channel_id, ts = ref.split(":", 1)
    return channel_id, ts


def thread_key(channel_id: str, ts: str) -> str:
    return f"{channel_id}:{ts}"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_card(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"extract_cards: card is not a JSON object: {path}")
    return data


def write_card(path: Path, card: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- thread text


def thread_lines(record: dict) -> list[str]:
    lines = []
    for message in sc.messages(record):
        files = message.get("files") or []
        suffix = f" [files: {', '.join(map(str, files))}]" if files else ""
        lines.append(f"{message.get('user', '?')} {message.get('ts', '?')}: {message.get('text', '')}{suffix}")
    return lines


def identifiers_in(text: str) -> list[str]:
    found: list[str] = []
    for hit in scrub.find_hits(text):
        if hit.pattern in IDENTIFIER_CLASSES and hit.match not in found:
            found.append(hit.match)
    return found


def date_of_ts(ts: str) -> str:
    try:
        return dt.datetime.fromtimestamp(float(ts), tz=dt.timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return ""


def permalink_for(config: dict, record: dict, channel_id: str, ts: str) -> str:
    host = str(config.get("workspace") or config.get("workspace_host") or "").strip()
    host = re.sub(r"^https?://", "", host).strip("/")
    if host:
        return f"https://{host}/archives/{channel_id}/p{ts.replace('.', '')}"
    return str(record.get("permalink") or "")


# ---------------------------------------------------------------- scaffold


def empty_card(card_id: str, source_kind: str, topic: str, skills: list[str]) -> dict:
    """Every card key in schema order; content fields empty for the agent."""
    return {
        "card_id": card_id,
        "source_kind": source_kind,
        "topic": topic,
        "kind": "diagnosis",
        "title": "",
        "skills": skills,
        "surface": "",
        "surface_verified": False,
        "marketplaces": [],
        "marketplace_inferred": True,
        "symptom_keywords": [],
        "error_text": [],
        "problem_as_asked": "",
        "root_cause": "",
        "resolution_steps": [],
        "verify": "",
        "generic_lesson": "",
        "amazon_rule_or_page": "",
        "first_party_source_paths": [],
        "related_sop_paths": [],
        "resolution_status": "unknown",
        "fix_source": "unknown",
        "evidence_location": "none",
        "confidence": "low",
        "coverage_verdict": "unchecked",
        "coverage_paths": [],
        "net_new": "",
        "contradicts_paths": [],
        "publishable": True,
        "policy_risk": False,
        "policy_risk_reason": "",
        "participants_external": False,
        "language": "",
        "client_specific_to_strip": [],
        "who_asked_role": "",
        "who_answered": "",
        "who_executed": "",
        "date_first_seen": "",
        "date_resolved": "",
        "client_slug": "",
        "channel_id": "",
        "channel_name": "",
        "parent_ts": "",
        "related_ts": [],
        "permalink": "",
        "identifiers": [],
        "notes": "",
    }


def scaffold_from_record(store: Store, record: dict, card_id: str, topic: str, lexicon: sc.Lexicon) -> dict:
    config = store.config()
    team = sc.team_ids(config)
    bots = sc.bot_ids(config)
    channel_id = str(record.get("channel_id", ""))
    ts = str(record.get("thread_ts", ""))
    channels = sc.channel_map(config)
    channel = channels.get(channel_id, {})
    skills = list(lexicon.topics.get(topic, {}).get("skills", []))
    card = empty_card(card_id, "slack-thread", topic, skills)

    full_text = "\n".join(str(m.get("text") or "") for m in sc.messages(record))
    users = sc.participants(record)
    external = {u for u in users if u and u not in team and u not in bots and not u.startswith("bot:")}
    answered = ""
    for reply in record.get("replies") or []:
        if isinstance(reply, dict) and str(reply.get("user")) in team:
            answered = str(reply.get("user"))
            break
    identifiers = identifiers_in(full_text)
    card.update(
        {
            "error_text": lexicon.code_hits(full_text),
            "evidence_location": "slack",
            "participants_external": bool(external),
            "language": str((record.get("first_glance") or {}).get("language") or ""),
            "client_specific_to_strip": list(identifiers),
            "who_answered": answered,
            "date_first_seen": date_of_ts(ts),
            "client_slug": str(record.get("client_slug") or channel.get("slug", "")),
            "channel_id": channel_id,
            "channel_name": str(record.get("channel_name") or channel.get("name", "")),
            "parent_ts": ts,
            "permalink": permalink_for(config, record, channel_id, ts),
            "identifiers": identifiers,
        }
    )
    return card


# ---------------------------------------------------------------- validation


def _field_text(card: dict, key: str) -> str:
    value = card.get(key)
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return "" if value is None else str(value)


def _path_exists(repo: Path, rel: str) -> bool:
    rel = rel.strip()
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        return False
    return (repo / rel).exists()


def validate_card(card: object, repo: Path, terms: list[str], schema: dict | None = None) -> list[str]:
    schema = schema if schema is not None else json.loads(CARD_SCHEMA_PATH.read_text(encoding="utf-8"))
    problems = sc.validate_schema(card, schema)
    if not isinstance(card, dict):
        return problems
    for key in NONEMPTY_FIELDS:
        if isinstance(card.get(key), str) and not card[key].strip():
            problems.append(f"$.{key}: empty")
    strip_tokens = [str(t) for t in card.get("client_specific_to_strip") or [] if str(t).strip()]
    for key in SCRUBBED_FIELDS:
        text = _field_text(card, key)
        if not text:
            continue
        for hit in scrub.find_hits(text, terms):
            problems.append(f"$.{key}: scrub hit {hit.pattern} {hit.match!r}")
        for token in strip_tokens:
            regex = scrub.term_regex(token)
            if regex is not None and regex.search(text):
                problems.append(f"$.{key}: contains client_specific_to_strip token {token!r}")
    for key in PATH_FIELDS:
        for rel in card.get(key) or []:
            if not _path_exists(repo, str(rel)):
                problems.append(f"$.{key}: path does not exist under the repo: {rel!r}")
    # The unit lint enforces these two; catching them here keeps a failed promote rare.
    for market in card.get("marketplaces") or []:
        if market not in MARKETPLACES:
            problems.append(f"$.marketplaces: {market!r} not one of {', '.join(MARKETPLACES)}")
    for skill in card.get("skills") or []:
        if not (repo / "skills" / str(skill)).is_dir():
            problems.append(f"$.skills: no skill folder skills/{skill}")
    return problems


# ---------------------------------------------------------------- coverage


def run_search(repo: Path, query: str) -> list[dict]:
    """Hits from the search helper for one query; [] on failure."""
    proc = subprocess.run(
        [PYTHON, str(repo / SEARCH_SCRIPT), query, "--library", "all", "--limit", str(SEARCH_LIMIT)],
        capture_output=True,
        text=True,
        cwd=str(repo),
        check=False,
    )
    if proc.returncode != 0:
        print(f"extract_cards: search failed for {query!r}: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return []
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return []
    return [h for h in data.get("results") or [] if isinstance(h, dict)]


def _rel(repo: Path, path: str) -> str:
    """Repo-relative path, or "" for a path outside the repo."""
    try:
        return Path(path).resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return ""


def _doc_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for top in ("skills", "docs"):
        base = repo / top
        if base.is_dir():
            files.extend(p for p in sorted(base.rglob("*.md")) if p.is_file())
    return files


def distinctive_words(title: str, files: list[tuple[Path, str]]) -> list[str]:
    words = []
    for word in re.findall(r"[a-z0-9][a-z0-9_-]{3,}", title.lower()):
        if word not in STOPWORDS and word not in words:
            words.append(word)
    counted = []
    for word in words:
        count = sum(1 for _p, text in files if word in text)
        if count:
            counted.append((count, -len(word), word))
    counted.sort()
    return [w for _c, _l, w in counted[:2]]


def assess_coverage(card: dict, repo: Path) -> tuple[str, list[str], dict]:
    queries = []
    keywords = [str(k) for k in card.get("symptom_keywords") or [] if str(k).strip()]
    queries.append(" ".join(keywords) if keywords else str(card.get("title") or ""))
    queries.extend(str(e) for e in card.get("error_text") or [] if str(e).strip())
    hits: list[dict] = []
    for query in queries:
        if re.search(r"[A-Za-z0-9]{2}", query):
            hits.extend(run_search(repo, query))
    hits.sort(key=lambda h: -int(h.get("score") or 0))

    texts = [(p, p.read_text(encoding="utf-8", errors="ignore").lower()) for p in _doc_files(repo)]
    words = distinctive_words(str(card.get("title") or ""), texts)
    grep_paths = []
    if len(words) == 2:
        grep_paths = [_rel(repo, str(p)) for p, text in texts if all(w in text for w in words)]

    verdict = "none"
    if any(h.get("library") in FULL_LIBRARIES and int(h.get("score") or 0) >= FULL_SCORE for h in hits):
        verdict = "full"
    elif any(int(h.get("score") or 0) >= PARTIAL_SCORE for h in hits) or grep_paths:
        verdict = "partial"

    paths: list[str] = []
    for rel in [_rel(repo, str(h.get("path") or "")) for h in hits] + grep_paths:
        if rel and rel not in paths:
            paths.append(rel)
    detail = {"queries": queries, "words": words, "top_hits": [(h.get("score"), h.get("library"), _rel(repo, str(h.get("path")))) for h in hits[:COVERAGE_TOP]]}
    return verdict, paths[:COVERAGE_TOP], detail


# ---------------------------------------------------------------- commands


def _store(args: argparse.Namespace) -> Store:
    root = Path(args.root) if args.root else sc.DEFAULT_ROOT
    repo = Path(args.repo) if args.repo else WORKSPACE_ROOT
    return Store(root, repo, Path(args.config) if args.config else None, Path(args.terms) if args.terms else None)


def _lexicon(args: argparse.Namespace) -> sc.Lexicon:
    return sc.Lexicon(sc.load_topics(args.topics or sc.TOPICS_PATH))


def load_candidates(store: Store) -> list[dict]:
    path = store.root / sc.CANDIDATES_NAME
    if not path.is_file():
        raise SystemExit(f"extract_cards: {path} missing; run slack_collect.py candidates first")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def cmd_next(args: argparse.Namespace) -> int:
    store = _store(args)
    state = store.load_state()
    terms = store.terms()
    picked = []
    blocked = sc.load_blocked(store.root)
    for row in load_candidates(store):
        if row.get("topic") != args.topic:
            continue
        if thread_key(str(row.get("channel_id")), str(row.get("thread_ts"))) in blocked:
            continue
        if args.family and row.get("family") != args.family:
            continue
        key = thread_key(str(row.get("channel_id")), str(row.get("thread_ts")))
        if state["threads"].get(key, {}).get("status") in DONE_STATUSES:
            continue
        picked.append(row)
        if len(picked) >= args.batch:
            break
    if not picked:
        print(f"next: no uncarded candidates for topic {args.topic}")
        return 0
    if not store.terms_path.is_file():
        print(f"next: denylist missing at {store.terms_path}; the preview applies the regex classes only", file=sys.stderr)
    for row in picked:
        channel_id, ts = str(row["channel_id"]), str(row["thread_ts"])
        record = json.loads(store.record_path(channel_id, ts).read_text(encoding="utf-8"))
        text = "\n".join(thread_lines(record))
        print(f"=== {channel_id}:{ts} | {row.get('channel_name', '')} | {row.get('family', '')} | {row.get('client_slug', '')}"
              f" | score {row.get('score')} | flags {', '.join(row.get('flags') or []) or 'none'}")
        print(text)
        print("--- scrubbed preview (what the unit may keep) ---")
        print(scrub.redact(text, terms))
        print()
    print(f"next: {len(picked)} candidate(s) for topic {args.topic}")
    return 0


def cmd_scaffold(args: argparse.Namespace) -> int:
    store = _store(args)
    lexicon = _lexicon(args)
    channel_id, ts = parse_thread_ref(args.thread)
    path = store.record_path(channel_id, ts)
    if not path.is_file():
        print(f"scaffold: no thread record at {path}", file=sys.stderr)
        return 1
    record = json.loads(path.read_text(encoding="utf-8"))
    state = store.load_state()
    key = thread_key(channel_id, ts)
    blocked_reason = sc.load_blocked(store.root).get(key)
    if blocked_reason:
        print(f"scaffold: {key} is blocked ({blocked_reason}); it never becomes a card", file=sys.stderr)
        return 2
    existing = state["threads"].get(key)
    if existing and existing.get("card"):
        print(f"scaffold: {key} already has {existing['card']} ({existing.get('status')})", file=sys.stderr)
        return 1
    topic = args.topic
    if not topic:
        for row in load_candidates(store) if (store.root / sc.CANDIDATES_NAME).is_file() else []:
            if row.get("channel_id") == channel_id and row.get("thread_ts") == ts:
                topic = row.get("topic")
                break
    if not topic:
        topic = (record.get("first_glance") or {}).get("topic_guess")
    if topic not in lexicon.topics:
        print(f"scaffold: no usable topic ({topic!r}); pass --topic", file=sys.stderr)
        return 2
    card_id = store.next_card_id()
    card = scaffold_from_record(store, record, card_id, topic, lexicon)
    out = store.cards / "candidate" / f"{card_id}.json"
    write_card(out, card)
    state["threads"][key] = {"status": "scaffolded", "card": card_id, "topic": topic, "updated": now_iso()}
    store.save_state(state)
    print(f"scaffolded {out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    store = _store(args)
    terms = store.terms()
    if not store.terms_path.is_file():
        print(f"validate: denylist missing at {store.terms_path}; only the regex classes were checked", file=sys.stderr)
    bad = 0
    for ref in args.cards:
        path = store.find_card(ref)
        problems = validate_card(load_card(path), store.repo, terms)
        if problems:
            bad += 1
            for problem in problems:
                print(f"{path.stem}: {problem}")
        else:
            print(f"{path.stem}: ok")
    print(f"validate: {len(args.cards)} card(s), {bad} with problems")
    return 1 if bad else 0


def cmd_coverage(args: argparse.Namespace) -> int:
    store = _store(args)
    for ref in args.cards:
        path = store.find_card(ref)
        card = load_card(path)
        verdict, paths, detail = assess_coverage(card, store.repo)
        card["coverage_verdict"] = verdict
        card["coverage_paths"] = paths
        write_card(path, card)
        print(f"{path.stem}: coverage {verdict}; words {detail['words'] or 'none'}")
        for score, library, rel in detail["top_hits"]:
            print(f"  {score}\t{library}\t{rel}")
        if not str(card.get("net_new") or "").strip():
            print(f"  {path.stem}: net_new is empty; the extraction agent writes it in one sentence")
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    store = _store(args)
    channel_id, ts = parse_thread_ref(args.thread)
    if args.status == "carded" and not args.card:
        print("mark: --card is required with --status carded", file=sys.stderr)
        return 2
    state = store.load_state()
    entry = state["threads"].get(thread_key(channel_id, ts), {})
    entry.update({"status": args.status, "updated": now_iso()})
    if args.card:
        entry["card"] = args.card
    if args.reason:
        entry["reason"] = args.reason
    state["threads"][thread_key(channel_id, ts)] = entry
    store.save_state(state)
    print(f"marked {channel_id}:{ts} {args.status}")
    return 0


def common_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="sweep store root (default _local/knowledge-sweep)")
    common.add_argument("--config", help="sweep config (default <root>/config.json)")
    common.add_argument("--terms", help="denylist file (default _local/knowledge-redaction-terms.txt)")
    common.add_argument("--repo", help=argparse.SUPPRESS)
    common.add_argument("--topics", help=argparse.SUPPRESS)
    return common


def build_parser() -> argparse.ArgumentParser:
    common = common_parser()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("next", parents=[common], help="print the next uncarded candidates for a topic")
    p.add_argument("--topic", required=True)
    p.add_argument("--batch", type=int, default=5)
    p.add_argument("--family")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("scaffold", parents=[common], help="write a candidate card with provenance prefilled")
    p.add_argument("--thread", required=True, help="CHANNEL:TS")
    p.add_argument("--topic")
    p.set_defaults(func=cmd_scaffold)

    p = sub.add_parser("validate", parents=[common], help="validate cards")
    p.add_argument("cards", nargs="+")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("coverage", parents=[common], help="fill coverage_verdict and coverage_paths")
    p.add_argument("cards", nargs="+")
    p.set_defaults(func=cmd_coverage)

    p = sub.add_parser("mark", parents=[common], help="record an extraction decision")
    p.add_argument("--thread", required=True, help="CHANNEL:TS")
    p.add_argument("--status", required=True, choices=("carded", "skipped"))
    p.add_argument("--card")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_mark)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
