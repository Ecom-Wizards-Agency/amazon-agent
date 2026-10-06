#!/usr/bin/env python3
"""Compute triage signals for the captured MAG SOPs and manage the triage sheet.

Subcommands:
  signals (default)   walk every active index entry, compute signals, write
                      signals.jsonl and triage.csv (verdict columns already in
                      an existing triage.csv are preserved per file key)
  merge-verdicts      merge verdict columns from a partial CSV into triage.csv
  summary             counts per verdict and per category from triage.csv

The signals are heuristics for a human or review agent. Nothing here deletes,
moves or edits a SOP; `sop_apply_triage.py` does that after approval.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SOP_DIRNAME = "MAG SOPs"
INDEX_REL = Path(SOP_DIRNAME) / "_index" / "sop-index.json"
DEFAULT_OUT_DIR = Path("_local") / "knowledge-sop-triage"

SIGNAL_COLUMNS = [
    "file",
    "title",
    "category",
    "pre_verdict",
    "pre_reason",
    "drop_class",
    "sibling_group",
    "helium10_body_heavy",
    "years",
    "tools",
    "old_nav_hits",
    "faq_unsourced_hits",
    "url_tokens",
    "overlap_files",
]
VERDICT_COLUMNS = [
    "verdict",
    "verdict_reason",
    "superseded_by",
    "merge_into",
    "flags",
    "knowledge_value",
    "policy_risk",
]
CSV_COLUMNS = SIGNAL_COLUMNS + VERDICT_COLUMNS
VERDICTS = {"", "keep", "update", "supersede", "merge", "drop"}
LIST_SEP = "; "

TOOLS_RE = re.compile(
    r"helium 10|helium10|cerebro|magnet|scribbles|jungle scout|keepa|datadive|"
    r"sellerboard|flatfilepro|asana|hubspot|justcall|fireflies|google meet|youtube",
    re.IGNORECASE,
)
OLD_NAV_RE = re.compile(
    r"Get help and resources|Call me now|Contact us|Help > Get support|Seller Support >|Case Log",
    re.IGNORECASE,
)
FAQ_UNSOURCED_RE = re.compile(
    r"While the SOP does not|does not specify|typically|generally", re.IGNORECASE
)
YEAR_RE = re.compile(r"(?<!\d)(20(?:1[5-9]|2[0-6]))(?!\d)")
URL_RE = re.compile(r"https?://[^\s)\"'<>\]]+")
URL_TOKEN_RE = re.compile(r"[?&](?:sv|sig|se)=")
IMAGE_MD_RE = re.compile(r"!\[[^\]]*\]\(")
HELIUM_BODY_RE = re.compile(r"helium|cerebro|magnet|scribbles", re.IGNORECASE)

VENDOR_TITLE_RE = re.compile(r"vendor central|\bvendor\b", re.IGNORECASE)
WALMART_RE = re.compile(r"walmart", re.IGNORECASE)
TOOL_TITLE_RE = re.compile(
    r"helium 10|helium10|cerebro|magnet|scribbles|hubspot|justcall|google meet|"
    r"fireflies|excel macro|deduplicator|bulk comparison|jan['’]s tool|"
    r"bulk negation tool|youtube",
    re.IGNORECASE,
)

OVERLAP_STOPWORDS = {
    "sop", "amazon", "catalog", "seller", "central", "report", "how", "create", "download",
}
OVERLAP_EXTS = {".md", ".txt", ".yaml", ".yml", ".json"}
OVERLAP_DIRS = ("skills", "docs")
OVERLAP_CAP = 8
SIBLING_PREFIX_WORDS = 6

PRE_REASONS = {
    "vendor-central-category": "Vendor Central SOP; the agent operates Seller Central and Amazon Ads only.",
    "vendor-titled": "Vendor-specific title; the agent does not operate Vendor Central.",
    "walmart": "Walmart SOP; Walmart is outside the agent's scope.",
    "tool-in-title": "Procedure built around a third-party or internal tool the agent does not use.",
}


# ---------------------------------------------------------------- helpers

def strip_frontmatter(text: str) -> str:
    """Return the text after a leading YAML frontmatter block, if any."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            nl = text.find("\n", end + 4)
            return text[nl + 1:] if nl != -1 else ""
    return text


def join_list(values) -> str:
    return LIST_SEP.join(str(v) for v in values)


def split_list(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def load_index(root: Path) -> dict:
    return json.loads((root / INDEX_REL).read_text(encoding="utf-8"))


def active_entries(data: dict) -> list[dict]:
    return [
        e for e in data.get("captured", [])
        if e.get("file") and not e.get("archived") and not e["file"].startswith("_archive/")
    ]


def title_words(title: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", title.lower())


def normalize_title(title: str) -> str:
    low = re.sub(r"\s*-\d{1,2}\s*$", "", title.lower().strip())
    return " ".join(re.findall(r"[a-z0-9]+", low))


def distinctive_words(title: str) -> list[str]:
    """Three longest title words of 5+ letters outside the stopword list."""
    seen: list[str] = []
    for word in re.findall(r"[a-z]+", title.lower()):
        if len(word) >= 5 and word not in OVERLAP_STOPWORDS and word not in seen:
            seen.append(word)
    # stable: longest first, ties keep title order
    return sorted(seen, key=lambda w: -len(w))[:3]


def load_overlap_corpus(root: Path) -> list[tuple[str, str]]:
    corpus: list[tuple[str, str]] = []
    for dirname in OVERLAP_DIRS:
        base = root / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in OVERLAP_EXTS or not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            corpus.append((path.relative_to(root).as_posix(), text))
    return corpus


def overlap_files(title: str, corpus: list[tuple[str, str]]) -> list[str]:
    words = distinctive_words(title)
    if len(words) < 2:
        return []
    patterns = [re.compile(r"\b" + re.escape(w)) for w in words]
    hits: list[tuple[int, str]] = []
    for rel, text in corpus:
        matched = sum(1 for p in patterns if p.search(text))
        if matched >= 2:
            hits.append((-matched, rel))
    hits.sort()
    return [rel for _, rel in hits[:OVERLAP_CAP]]


def drop_class(entry: dict) -> str:
    title = entry.get("title", "")
    rel = entry.get("file", "")
    if entry.get("category") == "Vendor Central" or rel.startswith("vendor-central/"):
        return "vendor-central-category"
    if VENDOR_TITLE_RE.search(title):
        return "vendor-titled"
    if WALMART_RE.search(title) or WALMART_RE.search(rel):
        return "walmart"
    if TOOL_TITLE_RE.search(title):
        return "tool-in-title"
    return ""


def sibling_groups(entries: list[dict]) -> dict[str, str]:
    """Map file -> group id for entries sharing a normalized title or its first six words."""
    parent = {e["file"]: e["file"] for e in entries}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    first_by_key: dict[str, str] = {}
    for e in entries:
        norm = normalize_title(e.get("title", ""))
        if not norm:
            continue
        prefix = " ".join(norm.split()[:SIBLING_PREFIX_WORDS])
        for key in {f"full:{norm}", f"prefix:{prefix}"}:
            if key in first_by_key:
                union(first_by_key[key], e["file"])
            else:
                first_by_key[key] = e["file"]

    members: dict[str, list[str]] = {}
    for f in parent:
        members.setdefault(find(f), []).append(f)
    title_by_file = {e["file"]: e.get("title", "") for e in entries}
    result: dict[str, str] = {}
    for files in members.values():
        if len(files) < 2:
            continue
        files.sort()
        words = normalize_title(title_by_file[files[0]]).split()[:SIBLING_PREFIX_WORDS]
        slug = "-".join(words)[:48].strip("-")
        digest = hashlib.sha1("\n".join(files).encode("utf-8")).hexdigest()[:6]
        gid = f"sib-{slug}-{digest}"
        for f in files:
            result[f] = gid
    return result


def compute_signal(entry: dict, text: str, corpus: list[tuple[str, str]]) -> dict:
    body = strip_frontmatter(text)
    image_md = len(IMAGE_MD_RE.findall(body))
    image_count = entry.get("image_count")
    if not isinstance(image_count, int):
        image_count = image_md
    body_length = entry.get("body_length")
    if not isinstance(body_length, int):
        body_length = len(body)
    urls = URL_RE.findall(body)
    return {
        "file": entry["file"],
        "title": entry.get("title", ""),
        "category": entry.get("category", ""),
        "body_length": body_length,
        "image_count": image_count,
        "images_document360": body.count("files.document360.io"),
        "images_mag_2025": body.count("gallery/2025"),
        "no_images": image_count == 0 and image_md == 0,
        "years": sorted(set(YEAR_RE.findall(body))),
        "tools": sorted({m.lower() for m in TOOLS_RE.findall(body)}),
        "old_nav_hits": len(OLD_NAV_RE.findall(body)),
        "faq_unsourced_hits": len(FAQ_UNSOURCED_RE.findall(body)),
        "url_tokens": sum(1 for u in urls if URL_TOKEN_RE.search(u)),
        "overlap_files": overlap_files(entry.get("title", ""), corpus),
        "helium_body_matches": len(HELIUM_BODY_RE.findall(body)),
    }


def finish_signal(sig: dict, entry: dict, group: str) -> dict:
    dc = drop_class(entry)
    heavy = sig.pop("helium_body_matches") >= 3 and not dc
    sig["sibling_group"] = group
    sig["drop_class"] = dc
    sig["helium10_body_heavy"] = heavy
    if dc:
        sig["pre_verdict"] = "drop"
        sig["pre_reason"] = PRE_REASONS[dc]
    elif group:
        sig["pre_verdict"] = "merge-candidate"
        sig["pre_reason"] = "Shares its title or opening words with another SOP; check for a duplicate or near-duplicate."
    else:
        sig["pre_verdict"] = "review"
        sig["pre_reason"] = (
            "No automatic drop or merge signal; a reviewer decides keep, update or supersede"
            + (" (body leans on Helium 10 tools)." if heavy else ".")
        )
    return sig


def collect_signals(root: Path) -> tuple[list[dict], list[str]]:
    data = load_index(root)
    entries = active_entries(data)
    sop_root = root / SOP_DIRNAME
    present: list[dict] = []
    missing: list[str] = []
    texts: dict[str, str] = {}
    for e in entries:
        path = sop_root / e["file"]
        if not path.is_file():
            missing.append(e["file"])
            continue
        texts[e["file"]] = path.read_text(encoding="utf-8", errors="replace")
        present.append(e)
    corpus = load_overlap_corpus(root)
    groups = sibling_groups(present)
    signals = []
    for e in present:
        sig = compute_signal(e, texts[e["file"]], corpus)
        signals.append(finish_signal(sig, e, groups.get(e["file"], "")))
    return signals, missing


def signal_to_row(sig: dict) -> dict:
    row = {}
    for col in SIGNAL_COLUMNS:
        value = sig.get(col, "")
        if isinstance(value, bool):
            value = "true" if value else "false"
        elif isinstance(value, list):
            value = join_list(value)
        row[col] = value
    for col in VERDICT_COLUMNS:
        row[col] = ""
    return row


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), [dict(r) for r in reader]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in CSV_COLUMNS})
    tmp.replace(path)


def resolve_out_dir(root: Path, out_dir: str | None) -> Path:
    path = Path(out_dir) if out_dir else DEFAULT_OUT_DIR
    return path if path.is_absolute() else root / path


# ---------------------------------------------------------------- commands

def cmd_signals(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    signals, missing = collect_signals(root)

    if args.drop_list:
        paths = sorted(f"{SOP_DIRNAME}/{s['file']}" for s in signals if s["pre_verdict"] == "drop")
        for p in paths:
            print(p)
        return 0

    out_dir = resolve_out_dir(root, args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "signals.jsonl"
    with jsonl.open("w", encoding="utf-8") as fh:
        for sig in signals:
            fh.write(json.dumps(sig, ensure_ascii=False) + "\n")

    csv_path = out_dir / "triage.csv"
    previous: dict[str, dict] = {}
    if csv_path.exists():
        _, old_rows = read_csv(csv_path)
        previous = {r.get("file", ""): r for r in old_rows}
    rows = []
    preserved = 0
    for sig in signals:
        row = signal_to_row(sig)
        old = previous.get(sig["file"])
        if old:
            kept = {c: old.get(c, "") or "" for c in VERDICT_COLUMNS}
            if any(kept.values()):
                preserved += 1
            row.update(kept)
        rows.append(row)
    write_csv(csv_path, rows)

    print(f"SOPs scanned: {len(signals)}")
    if missing:
        print(f"index entries without a file (skipped): {len(missing)}")
        for f in missing:
            print(f"  missing: {f}")
    print("pre_verdict:")
    for key, n in sorted(Counter(s["pre_verdict"] for s in signals).items()):
        print(f"  {key}: {n}")
    print("drop_class:")
    for key, n in sorted(Counter(s["drop_class"] or "(none)" for s in signals).items()):
        print(f"  {key}: {n}")
    print(f"helium10_body_heavy: {sum(1 for s in signals if s['helium10_body_heavy'])}")
    print(f"sibling groups: {len({s['sibling_group'] for s in signals if s['sibling_group']})}")
    if preserved:
        print(f"verdicts preserved from the previous triage.csv: {preserved}")
    print(f"wrote {jsonl}")
    print(f"wrote {csv_path}")
    return 0


def cmd_merge_verdicts(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    csv_path = resolve_out_dir(root, args.out_dir) / "triage.csv"
    if not csv_path.exists():
        print(f"error: {csv_path} not found; run signals first", file=sys.stderr)
        return 1
    _, rows = read_csv(csv_path)
    by_file = {r.get("file", ""): r for r in rows}
    src_fields, src_rows = read_csv(Path(args.from_csv))
    if "file" not in src_fields:
        print("error: source CSV has no 'file' column", file=sys.stderr)
        return 1
    cols = [c for c in VERDICT_COLUMNS if c in src_fields]
    if not cols:
        print("error: source CSV has none of the verdict columns", file=sys.stderr)
        return 1

    problems = []
    for i, src in enumerate(src_rows, start=2):
        key = (src.get("file") or "").strip()
        if key not in by_file:
            problems.append(f"line {i}: unknown file key {key!r}")
        verdict = (src.get("verdict") or "").strip()
        if "verdict" in cols and verdict not in VERDICTS:
            problems.append(f"line {i}: invalid verdict {verdict!r} for {key}")
    if problems:
        for p in problems:
            print(p)
        print("nothing merged")
        return 1

    updated = 0
    for src in src_rows:
        row = by_file[src["file"].strip()]
        changed = False
        for c in cols:
            value = (src.get(c) or "").strip()
            if value and row.get(c, "") != value:
                row[c] = value
                changed = True
        updated += changed
    write_csv(csv_path, rows)
    print(f"merged {updated} rows ({len(src_rows)} in source, columns: {', '.join(cols)})")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    csv_path = resolve_out_dir(root, args.out_dir) / "triage.csv"
    if not csv_path.exists():
        print(f"error: {csv_path} not found; run signals first", file=sys.stderr)
        return 1
    _, rows = read_csv(csv_path)
    print(f"rows: {len(rows)}")
    print("verdict:")
    for key, n in sorted(Counter((r.get("verdict") or "(none)") for r in rows).items()):
        print(f"  {key}: {n}")
    print("category:")
    for key, n in sorted(Counter((r.get("category") or "(none)") for r in rows).items()):
        print(f"  {key}: {n}")
    print("category x verdict:")
    pairs = Counter((r.get("category") or "(none)", r.get("verdict") or "(none)") for r in rows)
    for (cat, verdict), n in sorted(pairs.items()):
        print(f"  {cat} / {verdict}: {n}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=str(DEFAULT_ROOT), help="workspace root")
    common.add_argument(
        "--out-dir", default=None, help=f"output directory (default {DEFAULT_OUT_DIR}, relative to --root)"
    )
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    p_sig = sub.add_parser("signals", parents=[common], help="compute signals, write signals.jsonl and triage.csv")
    p_sig.add_argument(
        "--drop-list", action="store_true",
        help="print only the sorted repo-relative paths of pre_verdict=drop SOPs; writes nothing",
    )
    p_sig.set_defaults(func=cmd_signals)
    p_merge = sub.add_parser("merge-verdicts", parents=[common], help="merge verdict columns from a CSV")
    p_merge.add_argument("--from", dest="from_csv", required=True, help="CSV with file + verdict columns")
    p_merge.set_defaults(func=cmd_merge_verdicts)
    p_sum = sub.add_parser("summary", parents=[common], help="counts per verdict and category")
    p_sum.set_defaults(func=cmd_summary)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in {"signals", "merge-verdicts", "summary", "-h", "--help"}:
        argv = ["signals"] + argv
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
