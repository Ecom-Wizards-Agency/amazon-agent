#!/usr/bin/env python3
"""Plan, check and score the Slack thread store of the knowledge sweep.

Collection agents (not this script) read Slack and write thread records into
the gitignored store, following tools/knowledge/prompts/collect-threads.md:

  <root>/threads/<channel_id>/<thread_ts>.json   one record per thread
  <root>/skipped/<channel_id>/<window>.jsonl      parents not stored
  <root>/checkpoints/<channel_id>-<window>.json   one per channel and window

<root> defaults to _local/knowledge-sweep/ and the config to <root>/config.json.
This script never reads Slack, never writes outside <root>, and never prints
anything into a tracked file.

Commands:
  plan [--family F] [--since YYYY-MM] [--json]
      Collection windows per channel with their oldest and latest Unix
      timestamps (UTC, latest exclusive) and the checkpoint status (missing,
      partial, complete). Client and internal channels use half-years
      (2026-H1); low-volume families (client_former, supplier_logistics,
      own_brand) use whole years (2026). Windows start at the config
      date_floor and end at the current month; the open window's latest is
      the current time. The excluded family is never planned.
  validate [paths...]
      Validate thread records against tools/knowledge/thread.schema.json with
      a small stdlib validator. No paths: every record in the store.
  stats
      Per family and per channel: windows complete/partial/missing, parents
      seen, threads stored, parents skipped, resolution hints, language split,
      and the config channels with no checkpoint at all.
  candidates [--min-score N] [--topic T]
      Score every stored thread and write <root>/candidates.jsonl.

Candidate scoring (topic lexicon: tools/knowledge/topics.json):
  - Dropped: records whose parent and every reply are bot posts (user starts
    with "bot:", subtype bot_message, or a user listed under the config
    bots_to_drop), and records with neither a team member nor a resolution
    hint.
  - Topic score: per message, one point for each distinct topic keyword that
    appears in it, plus two points per error-code regex match.
  - The best topic wins; with no keyword or code hit the record keeps
    first_glance.topic_guess.
  - Bonuses, added to the best topic score: +3 when a resolution marker
    appears in a reply (or in the parent of a thread without replies), +2 per
    reply by a team member, at most +6.
  - Flags: german (first_glance.language de or mixed), external_participants
    (a participant outside the config team who is not a bot; a flag, never a
    filter), attachments_only (parent text under 40 characters with files).

Stdlib only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

WORKSPACE_ROOT = HERE.parents[1]
DEFAULT_ROOT = WORKSPACE_ROOT / "_local" / "knowledge-sweep"
TOPICS_PATH = HERE / "topics.json"
THREAD_SCHEMA_PATH = HERE / "thread.schema.json"

HALF_YEAR_FAMILIES = ("client_current", "client_slack_connect", "internal")
YEAR_FAMILIES = ("client_former", "supplier_logistics", "own_brand")
PLANNED_FAMILIES = HALF_YEAR_FAMILIES + YEAR_FAMILIES

RESOLUTION_BONUS = 3
TEAM_REPLY_BONUS = 2
TEAM_REPLY_BONUS_MAX = 6
ERROR_CODE_WEIGHT = 2
ATTACHMENT_ONLY_CHARS = 40
PREVIEW_CHARS = 160
# Keywords this short match whole words only; longer ones may run on into
# German compounds and plurals (versand -> Versandplan).
WHOLE_WORD_MAX = 5
CANDIDATES_NAME = "candidates.jsonl"
BLOCKED_NAME = "blocked-threads.jsonl"  # {channel_id, thread_ts, reason, blocked_on}: never a candidate, never a card


# ---------------------------------------------------------------- loading


def load_json(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"slack_collect: config not found: {path}")
    data = load_json(path)
    if not isinstance(data, dict):
        raise SystemExit(f"slack_collect: config must be a JSON object: {path}")
    return data


def load_topics(path: str | Path = TOPICS_PATH) -> dict:
    return load_json(Path(path))  # type: ignore[return-value]


def team_ids(config: dict) -> set[str]:
    ids: set[str] = set()
    team = config.get("team") or {}
    values = team.values() if isinstance(team, dict) else team
    for value in values:
        if isinstance(value, str):
            ids.add(value)
        elif isinstance(value, list):
            ids.update(str(v) for v in value)
    return ids


def bot_ids(config: dict) -> set[str]:
    ids: set[str] = set()
    bots = config.get("bots_to_drop") or config.get("bots") or {}
    if isinstance(bots, dict):
        for key, value in bots.items():
            if key == "note":
                continue
            if isinstance(value, str):
                ids.add(value)
            elif isinstance(value, list):
                ids.update(str(v) for v in value)
    elif isinstance(bots, list):
        ids.update(str(v) for v in bots)
    return ids


def channel_map(config: dict) -> dict[str, dict]:
    """channel_id -> {id, name, slug, family} for every planned family."""
    out: dict[str, dict] = {}
    families = config.get("channel_families") or {}
    for family, channels in families.items():
        if family == "excluded" or not isinstance(channels, list):
            continue
        for channel in channels:
            if isinstance(channel, dict) and channel.get("id"):
                out[channel["id"]] = {
                    "id": channel["id"],
                    "name": channel.get("name", ""),
                    "slug": channel.get("slug", ""),
                    "family": family,
                }
    return out


# ---------------------------------------------------------------- windows


def _ts(day: dt.date) -> int:
    return int(dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc).timestamp())


def _parse_month(text: str) -> dt.date:
    try:
        year, month = text[:7].split("-")
        return dt.date(int(year), int(month), 1)
    except ValueError as exc:
        raise SystemExit(f"slack_collect: expected YYYY-MM, got {text!r}") from exc


def windows_for(family: str, floor: dt.date, today: dt.date) -> list[dict]:
    """Collection windows from the floor's period up to today's month.

    Each window: {window, oldest, latest, open}. oldest is clamped to the floor;
    latest is the next period's start (exclusive), or now for the open window.
    """
    half = family not in YEAR_FAMILIES
    out: list[dict] = []
    if half:
        start = dt.date(floor.year, 1 if floor.month <= 6 else 7, 1)
    else:
        start = dt.date(floor.year, 1, 1)
    now_ts = int(dt.datetime.combine(today, dt.time(0), tzinfo=dt.timezone.utc).timestamp()) + 86399
    while start <= today:
        if half:
            label = f"{start.year}-H{1 if start.month == 1 else 2}"
            end = dt.date(start.year, 7, 1) if start.month == 1 else dt.date(start.year + 1, 1, 1)
        else:
            label = f"{start.year}"
            end = dt.date(start.year + 1, 1, 1)
        oldest = _ts(max(start, floor))
        latest = _ts(end)
        is_open = latest > now_ts
        out.append({"window": label, "oldest": oldest, "latest": min(latest, now_ts) if is_open else latest, "open": is_open})
        start = end
    return out


def checkpoint_path(root: Path, channel_id: str, window: str) -> Path:
    return root / "checkpoints" / f"{channel_id}-{window}.json"


def read_checkpoint(root: Path, channel_id: str, window: str) -> dict | None:
    path = checkpoint_path(root, channel_id, window)
    if not path.is_file():
        return None
    try:
        data = load_json(path)
    except ValueError:
        return {"complete": False, "notes": "unreadable checkpoint"}
    return data if isinstance(data, dict) else {"complete": False}


def checkpoint_status(checkpoint: dict | None) -> str:
    if checkpoint is None:
        return "missing"
    return "complete" if checkpoint.get("complete") is True else "partial"


def build_plan(config: dict, root: Path, today: dt.date, family: str | None = None, since: str | None = None) -> list[dict]:
    floor_text = str(config.get("date_floor") or "")
    try:
        floor = dt.date.fromisoformat(floor_text)
    except ValueError as exc:
        raise SystemExit(f"slack_collect: config date_floor must be YYYY-MM-DD, got {floor_text!r}") from exc
    since_ts = _ts(_parse_month(since)) if since else None
    rows: list[dict] = []
    families = config.get("channel_families") or {}
    for fam in families:
        if fam not in PLANNED_FAMILIES:
            continue
        if family and fam != family:
            continue
        for channel in families[fam] or []:
            if not isinstance(channel, dict) or not channel.get("id"):
                continue
            for window in windows_for(fam, floor, today):
                if since_ts is not None and window["latest"] <= since_ts:
                    continue
                checkpoint = read_checkpoint(root, channel["id"], window["window"])
                rows.append(
                    {
                        "family": fam,
                        "channel_id": channel["id"],
                        "channel_name": channel.get("name", ""),
                        "client_slug": channel.get("slug", ""),
                        "window": window["window"],
                        "oldest": window["oldest"],
                        "latest": window["latest"],
                        "open": window["open"],
                        "status": checkpoint_status(checkpoint),
                    }
                )
    return rows


# ---------------------------------------------------------------- schema validation


_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
}


def _type_ok(value: object, expected: str) -> bool:
    if expected in ("number", "integer") and isinstance(value, bool):
        return False
    return isinstance(value, _TYPES.get(expected, object))


def validate_schema(instance: object, schema: dict, root_schema: dict | None = None, path: str = "$") -> list[str]:
    """Problems with `instance` against a JSON schema subset.

    Supports type, required, properties, items, enum, const, pattern and local
    $ref (#/$defs/...). Unknown keywords are ignored.
    """
    root_schema = root_schema if root_schema is not None else schema
    problems: list[str] = []
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        target: object = root_schema
        for part in ref[2:].split("/"):
            target = target.get(part, {}) if isinstance(target, dict) else {}
        return validate_schema(instance, target if isinstance(target, dict) else {}, root_schema, path)
    expected = schema.get("type")
    if isinstance(expected, str) and not _type_ok(instance, expected):
        return [f"{path}: expected {expected}, got {type(instance).__name__}"]
    if "const" in schema and instance != schema["const"]:
        problems.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        problems.append(f"{path}: {instance!r} not one of {', '.join(map(str, schema['enum']))}")
    if isinstance(instance, str) and isinstance(schema.get("pattern"), str):
        if not re.search(schema["pattern"], instance):
            problems.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                problems.append(f"{path}: missing required key {key!r}")
        for key, sub in (schema.get("properties") or {}).items():
            if key in instance and isinstance(sub, dict):
                problems.extend(validate_schema(instance[key], sub, root_schema, f"{path}.{key}"))
    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(instance):
            problems.extend(validate_schema(item, schema["items"], root_schema, f"{path}[{i}]"))
    return problems


def validate_record(record: object, schema: dict | None = None) -> list[str]:
    schema = schema if schema is not None else load_json(THREAD_SCHEMA_PATH)  # type: ignore[assignment]
    return validate_schema(record, schema)  # type: ignore[arg-type]


# ---------------------------------------------------------------- store


def iter_records(root: Path):
    """Yield (path, record or None, error) for every thread record in the store."""
    threads = root / "threads"
    if not threads.is_dir():
        return
    for path in sorted(threads.glob("*/*.json")):
        try:
            data = load_json(path)
        except (OSError, ValueError) as exc:
            yield path, None, f"unreadable: {exc}"
            continue
        if not isinstance(data, dict):
            yield path, None, "not a JSON object"
            continue
        yield path, data, None


def messages(record: dict) -> list[dict]:
    out = []
    parent = record.get("parent")
    if isinstance(parent, dict):
        out.append(parent)
    for reply in record.get("replies") or []:
        if isinstance(reply, dict):
            out.append(reply)
    return out


def is_bot(message: dict, bots: set[str]) -> bool:
    user = str(message.get("user") or "")
    return user.startswith("bot:") or message.get("subtype") == "bot_message" or user in bots or bool(message.get("bot_id"))


def all_bot(record: dict, bots: set[str]) -> bool:
    msgs = messages(record)
    return bool(msgs) and all(is_bot(m, bots) for m in msgs)


def participants(record: dict) -> set[str]:
    users = {str(u) for u in record.get("participants") or []}
    users.update(str(m.get("user")) for m in messages(record) if m.get("user"))
    return users


# ---------------------------------------------------------------- scoring


def keyword_regex(keyword: str, whole_word: bool = False) -> re.Pattern[str]:
    body = r"\s+".join(re.escape(part) for part in keyword.split())
    tail = r"(?!\w)" if whole_word or len(keyword) <= WHOLE_WORD_MAX else ""
    return re.compile(r"(?<!\w)" + body + tail, re.IGNORECASE)


class Lexicon:
    """Compiled topics.json."""

    def __init__(self, topics: dict) -> None:
        self.raw = topics
        self.topics: dict[str, dict] = {}
        for name, spec in (topics.get("topics") or {}).items():
            self.topics[name] = {
                "skills": list(spec.get("skills") or []),
                "keywords": [(k, keyword_regex(k)) for k in spec.get("keywords") or []],
                "codes": [re.compile(c, re.IGNORECASE) for c in spec.get("error_codes") or []],
            }
        # Markers need a boundary on both sides: "done" must not hit "doner".
        self.markers = [keyword_regex(m, whole_word=True) for m in topics.get("resolution_markers") or []]

    def topic_scores(self, texts: list[str]) -> dict[str, int]:
        scores: dict[str, int] = {}
        for name, spec in self.topics.items():
            score = 0
            for text in texts:
                score += sum(1 for _k, rx in spec["keywords"] if rx.search(text))
                score += ERROR_CODE_WEIGHT * sum(len(rx.findall(text)) for rx in spec["codes"])
            scores[name] = score
        return scores

    def keyword_hits(self, text: str) -> set[str]:
        return {k for spec in self.topics.values() for k, rx in spec["keywords"] if rx.search(text)}

    def code_hits(self, text: str) -> list[str]:
        found: list[str] = []
        for spec in self.topics.values():
            for rx in spec["codes"]:
                for m in rx.finditer(text):
                    if m.group(0) not in found:
                        found.append(m.group(0))
        return found

    def has_marker(self, text: str) -> bool:
        return any(rx.search(text) for rx in self.markers)


def best_topic(scores: dict[str, int], fallback: str | None) -> tuple[str, int]:
    if scores:
        name = max(scores, key=lambda k: (scores[k], -list(scores).index(k)))
        if scores[name] > 0:
            return name, scores[name]
    return (fallback or "other"), 0


def score_record(record: dict, config: dict, lexicon: Lexicon) -> dict | None:
    """The candidate row for a record, or None when it is dropped."""
    bots = bot_ids(config)
    team = team_ids(config)
    if all_bot(record, bots):
        return None
    glance = record.get("first_glance") or {}
    has_hint = bool(glance.get("has_resolution_hint"))
    users = participants(record)
    has_team = bool(record.get("has_team_member")) or bool(users & team)
    if not (has_team or has_hint):
        return None

    human = [m for m in messages(record) if not is_bot(m, bots)]
    texts = [str(m.get("text") or "") for m in human]
    scores = lexicon.topic_scores(texts)
    topic, topic_score = best_topic(scores, glance.get("topic_guess"))

    replies = [m for m in record.get("replies") or [] if isinstance(m, dict) and not is_bot(m, bots)]
    marker_texts = [str(m.get("text") or "") for m in replies] or texts[:1]
    bonus = RESOLUTION_BONUS if any(lexicon.has_marker(t) for t in marker_texts) else 0
    team_replies = sum(1 for m in replies if str(m.get("user")) in team)
    bonus += min(TEAM_REPLY_BONUS * team_replies, TEAM_REPLY_BONUS_MAX)

    parent = record.get("parent") or {}
    parent_text = str(parent.get("text") or "")
    flags: list[str] = []
    if glance.get("language") in ("de", "mixed"):
        flags.append("german")
    external = {u for u in users if u and u not in team and u not in bots and not u.startswith("bot:")}
    if external:
        flags.append("external_participants")
    if len(parent_text.strip()) < ATTACHMENT_ONLY_CHARS and parent.get("files"):
        flags.append("attachments_only")

    channels = channel_map(config)
    channel = channels.get(str(record.get("channel_id")), {})
    return {
        "channel_id": record.get("channel_id", ""),
        "thread_ts": record.get("thread_ts", ""),
        "channel_name": record.get("channel_name") or channel.get("name", ""),
        "family": record.get("family") or channel.get("family", ""),
        "client_slug": record.get("client_slug") or channel.get("slug", ""),
        "topic": topic,
        "score": topic_score + bonus,
        "flags": flags,
        "has_resolution_hint": has_hint,
        "participants": len(users),
        "parent_preview": " ".join(parent_text.split())[:PREVIEW_CHARS],
    }


def load_blocked(root: Path) -> dict[str, str]:
    """Threads the agency lead blocked from ever becoming cards or units.

    One JSON object per line in <root>/blocked-threads.jsonl with channel_id,
    thread_ts and reason. Returns {"<channel_id>:<thread_ts>": reason}.
    Malformed lines are reported and skipped, never silently accepted.
    """
    path = root / BLOCKED_NAME
    blocked: dict[str, str] = {}
    if not path.is_file():
        return blocked
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
            key = f"{row['channel_id']}:{row['thread_ts']}"
        except (ValueError, KeyError, TypeError):
            print(f"slack_collect: {path}:{lineno}: unreadable blocked-thread line", file=sys.stderr)
            continue
        blocked[key] = str(row.get("reason") or "blocked")
    return blocked


def build_candidates(root: Path, config: dict, lexicon: Lexicon) -> tuple[list[dict], Counter]:
    rows: list[dict] = []
    dropped: Counter = Counter()
    blocked = load_blocked(root)
    for path, record, error in iter_records(root):
        if record is None:
            dropped["unreadable"] += 1
            print(f"slack_collect: skipped {path}: {error}", file=sys.stderr)
            continue
        key = f"{record.get('channel_id')}:{record.get('thread_ts')}"
        if key in blocked:
            dropped["blocked"] += 1
            continue
        row = score_record(record, config, lexicon)
        if row is None:
            dropped["dropped"] += 1
            continue
        rows.append(row)
    rows.sort(key=lambda r: (-r["score"], str(r["channel_id"]), str(r["thread_ts"])))
    return rows, dropped


# ---------------------------------------------------------------- commands


def _today(args: argparse.Namespace) -> dt.date:
    if getattr(args, "today", None):
        return dt.date.fromisoformat(args.today)
    return dt.datetime.now(dt.timezone.utc).date()


def _root(args: argparse.Namespace) -> Path:
    return Path(args.root) if args.root else DEFAULT_ROOT


def _config_path(args: argparse.Namespace) -> Path:
    return Path(args.config) if args.config else _root(args) / "config.json"


def cmd_plan(args: argparse.Namespace) -> int:
    root = _root(args)
    config = load_config(_config_path(args))
    if args.family and args.family not in PLANNED_FAMILIES:
        print(f"slack_collect: family must be one of {', '.join(PLANNED_FAMILIES)}", file=sys.stderr)
        return 2
    rows = build_plan(config, root, _today(args), args.family, args.since)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0
    channels = len({r["channel_id"] for r in rows})
    status = Counter(r["status"] for r in rows)
    print(
        f"windows: {len(rows)} across {channels} channels"
        f" (complete {status['complete']}, partial {status['partial']}, missing {status['missing']})"
    )
    for r in rows:
        open_mark = " open" if r["open"] else ""
        print(
            f"{r['family']}\t{r['channel_name']}\t{r['channel_id']}\t{r['window']}"
            f"\toldest={r['oldest']}\tlatest={r['latest']}\t{r['status']}{open_mark}"
        )
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    schema = load_json(THREAD_SCHEMA_PATH)
    if args.paths:
        targets = []
        for raw in args.paths:
            p = Path(raw)
            targets.extend(sorted(p.rglob("*.json")) if p.is_dir() else [p])
        items = []
        for p in targets:
            try:
                items.append((p, load_json(p), None))
            except (OSError, ValueError) as exc:
                items.append((p, None, f"unreadable: {exc}"))
    else:
        items = list(iter_records(_root(args)))
    bad = 0
    for path, record, error in items:
        problems = [error] if error else validate_record(record, schema)  # type: ignore[arg-type]
        if record is not None and not problems:
            expected = path.stem
            if record.get("thread_ts") != expected:
                problems.append(f"$.thread_ts: {record.get('thread_ts')!r} does not match the file name {expected!r}")
            if record.get("channel_id") != path.parent.name:
                problems.append(f"$.channel_id: {record.get('channel_id')!r} does not match the folder {path.parent.name!r}")
        if problems:
            bad += 1
            for problem in problems:
                print(f"{path}: {problem}")
    print(f"validate: {len(items)} records, {bad} with problems")
    return 1 if bad else 0


def cmd_stats(args: argparse.Namespace) -> int:
    root = _root(args)
    config = load_config(_config_path(args))
    plan = build_plan(config, root, _today(args))
    channels = channel_map(config)
    per_channel: dict[str, dict] = defaultdict(
        lambda: {"complete": 0, "partial": 0, "missing": 0, "parents_seen": 0, "threads_stored": 0, "parents_skipped": 0,
                 "records": 0, "hints": 0, "lang": Counter(), "checkpoints": 0}
    )
    for row in plan:
        stats = per_channel[row["channel_id"]]
        stats[row["status"]] += 1
    checkpoint_dir = root / "checkpoints"
    for path in sorted(checkpoint_dir.glob("*.json")) if checkpoint_dir.is_dir() else []:
        try:
            data = load_json(path)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        cid = str(data.get("channel_id") or path.stem.rsplit("-", 1)[0])
        stats = per_channel[cid]
        stats["checkpoints"] += 1
        for key in ("parents_seen", "threads_stored", "parents_skipped"):
            value = data.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                stats[key] += value
    record_count = 0
    for _path, record, _error in iter_records(root):
        if record is None:
            continue
        record_count += 1
        stats = per_channel[str(record.get("channel_id"))]
        stats["records"] += 1
        glance = record.get("first_glance") or {}
        if glance.get("has_resolution_hint"):
            stats["hints"] += 1
        stats["lang"][str(glance.get("language") or "unknown")] += 1

    no_checkpoint = [cid for cid in channels if per_channel[cid]["checkpoints"] == 0]
    if record_count == 0 and len(no_checkpoint) == len(channels):
        print(f"store is empty: no checkpoints and no thread records under {root}")

    by_family: dict[str, list[str]] = defaultdict(list)
    for cid in per_channel:
        family = channels.get(cid, {}).get("family", "unknown")
        by_family[family].append(cid)
    for family in [*PLANNED_FAMILIES, "unknown"]:
        cids = by_family.get(family)
        if not cids:
            continue
        total = Counter()
        lang = Counter()
        for cid in cids:
            s = per_channel[cid]
            for key in ("complete", "partial", "missing", "parents_seen", "threads_stored", "parents_skipped", "records", "hints"):
                total[key] += s[key]
            lang.update(s["lang"])
        print(
            f"\n[{family}] windows complete {total['complete']} / partial {total['partial']} / missing {total['missing']};"
            f" parents seen {total['parents_seen']}, stored {total['threads_stored']} (records on disk {total['records']}),"
            f" skipped {total['parents_skipped']}, resolution hints {total['hints']}, languages {_lang(lang)}"
        )
        for cid in sorted(cids, key=lambda c: channels.get(c, {}).get("name", c)):
            s = per_channel[cid]
            if s["checkpoints"] == 0 and s["records"] == 0:
                continue
            name = channels.get(cid, {}).get("name", "?")
            print(
                f"  {name} {cid}: windows {s['complete']}/{s['partial']}/{s['missing']} (complete/partial/missing),"
                f" seen {s['parents_seen']}, stored {s['threads_stored']} (on disk {s['records']}),"
                f" skipped {s['parents_skipped']}, hints {s['hints']}, languages {_lang(s['lang'])}"
            )
    print(f"\nchannels in the config with no checkpoint: {len(no_checkpoint)} of {len(channels)}")
    for cid in no_checkpoint:
        info = channels[cid]
        print(f"  {info['family']}\t{info['name']}\t{cid}")
    return 0


def _lang(counter: Counter) -> str:
    return ", ".join(f"{k} {v}" for k, v in sorted(counter.items())) or "none"


def cmd_candidates(args: argparse.Namespace) -> int:
    root = _root(args)
    config = load_config(_config_path(args))
    lexicon = Lexicon(load_topics(args.topics or TOPICS_PATH))
    rows, dropped = build_candidates(root, config, lexicon)
    if args.min_score is not None:
        rows = [r for r in rows if r["score"] >= args.min_score]
    if args.topic:
        rows = [r for r in rows if r["topic"] == args.topic]
    out = root / CANDIDATES_NAME
    root.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"candidates: {len(rows)} written to {out}; dropped {dropped['dropped']}, blocked {dropped['blocked']}, unreadable {dropped['unreadable']}")
    by_topic = Counter(r["topic"] for r in rows)
    by_family = Counter(r["family"] for r in rows)
    print("per topic: " + (", ".join(f"{k} {v}" for k, v in sorted(by_topic.items())) or "none"))
    print("per family: " + (", ".join(f"{k} {v}" for k, v in sorted(by_family.items())) or "none"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", help="sweep store root (default _local/knowledge-sweep)")
    common.add_argument("--config", help="sweep config (default <root>/config.json)")
    common.add_argument("--today", help=argparse.SUPPRESS)
    common.add_argument("--topics", help=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", parents=[common], help="list collection windows and checkpoint status")
    p.add_argument("--family")
    p.add_argument("--since", help="YYYY-MM: only windows that end after this month starts")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("validate", parents=[common], help="validate thread records against the schema")
    p.add_argument("paths", nargs="*")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("stats", parents=[common], help="coverage and volume per family and channel")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("candidates", parents=[common], help="score stored threads into candidates.jsonl")
    p.add_argument("--min-score", type=int)
    p.add_argument("--topic")
    p.set_defaults(func=cmd_candidates)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
