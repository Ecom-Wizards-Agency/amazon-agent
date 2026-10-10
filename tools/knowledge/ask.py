#!/usr/bin/env python3
"""Answer an Amazon question from the local libraries, ranked by authority.

  python3 tools/knowledge/ask.py "<question or exact error text>" [--json] [--per-layer N]

One search across every library, then the hits are grouped into the lookup
layers the library map names, in this order:

  1. knowledge units (our verified answers; draft and unverified labels shown)
  2. our skills and their references (own workflows first)
  3. first-party Amazon help captures (rules and current UI)
  4. SOP drafts (ours, emerging)
  5. MAG SOPs (external; shown last with status and site revision date)

Scores come from tools/search_amazon_libraries.py; the layer order is fixed, so
a MAG SOP never outranks our own procedure however well it matches. This is the
lookup order, not the authority order: when sources disagree, first-party pages
win on rules and current UI (docs/knowledge-library.md). The text output is a
short answer sheet; --json returns the same structure for tools.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
_SEARCH_PATH = WORKSPACE_ROOT / "tools" / "search_amazon_libraries.py"
_spec = importlib.util.spec_from_file_location("search_amazon_libraries", _SEARCH_PATH)
assert _spec is not None and _spec.loader is not None
search = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(search)

FIRST_PARTY = ("Amazon Seller Help", "Amazon Ads Help", "Advertising Help After Login", "AdLabs Help")
LAYERS = (
    ("units", "Knowledge units", ("Amazon Knowledge",)),
    ("skills", "Our skills", ("Skills",)),
    ("first-party", "First-party help", FIRST_PARTY),
    ("drafts", "SOP drafts", ("SOP Drafts",)),
    ("mag", "MAG SOPs (external)", ("MAG SOPs",)),
)
DEFAULT_PER_LAYER = {"units": 3, "skills": 3, "first-party": 3, "drafts": 2, "mag": 2}


def _ddmmyyyy(value: str | None) -> str:
    if not value:
        return ""
    try:
        return dt.date.fromisoformat(value[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return value


def roots_for(root: Path) -> list[tuple[str, Path]]:
    return [
        ("Amazon Knowledge", root / "knowledge"),
        ("Skills", root / "skills"),
        ("MAG SOPs", root / "MAG SOPs"),
        ("SOP Drafts", root / "sop-drafts"),
        ("Amazon Seller Help", root / "Amazon Seller Help"),
        ("Amazon Ads Help", root / "Amazon Ads Help"),
        ("Advertising Help After Login", root / "Advertising Help After Login"),
        ("AdLabs Help", root / "AdLabs Help"),
    ]


def load_sop_index(root: Path) -> dict[str, dict]:
    path = root / "MAG SOPs" / "_index" / "sop-index.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {e.get("file", ""): e for e in data.get("captured", []) if isinstance(e, dict)}


def _skill_file(path: Path, skills_root: Path) -> bool:
    rel = path.relative_to(skills_root)
    return path.name == "SKILL.md" or (len(rel.parts) >= 3 and rel.parts[1] == "references" and path.suffix == ".md")


def collect(question: str, root: Path = WORKSPACE_ROOT) -> list[dict]:
    terms = search.tokenize(question)
    if not terms:
        raise ValueError("the question must contain at least one searchable term")
    knowledge_root = root / "knowledge"
    mag_root = root / "MAG SOPs"
    skills_root = root / "skills"
    sop_index = load_sop_index(root)
    hits: list[dict] = []
    retired = knowledge_root / "_retired"
    for label, lib_root in roots_for(root):
        for path in search.iter_files(lib_root) or []:
            if label == "Skills" and not _skill_file(path, skills_root):
                continue
            if label == "Amazon Knowledge" and (path == knowledge_root / "README.md" or retired in path.parents):
                continue
            if "_index" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            meta = None
            if label == "Amazon Knowledge" and path.suffix.lower() == ".md":
                meta = search.knowledge_meta(text)
                if meta is not None and meta.get("status") == "retired":
                    continue
            title = search.title_for(path, text)
            if meta is not None and isinstance(meta.get("title"), str) and meta["title"]:
                title = meta["title"]
            score = search.score_text(text, title, path, terms)
            if not score:
                continue
            if meta is not None:
                score += search.knowledge_boost(meta, terms)
            hit = {"score": score, "library": label, "path": str(path.relative_to(root)), "title": title, "snippet": search.snippet(text, terms)}
            if meta is not None:
                for key in ("id", "status", "verification", "topic", "skills"):
                    hit[key] = meta.get(key)
            if label == "MAG SOPs":
                rel = path.relative_to(mag_root).as_posix()
                entry = sop_index.get(rel, {})
                hit["external"] = True
                hit["sop_status"] = entry.get("status", "unknown")
                hit["revised_at"] = entry.get("revised_at") or ""
                captured = entry.get("captured_at") or ""
                hit["changed_since_capture"] = bool(hit["revised_at"] and captured and hit["revised_at"][:10] > captured[:10])
                if entry.get("status") == "superseded":
                    score //= 2
                    hit["score"] = score
                    hit["superseded_by"] = entry.get("superseded_by", "")
            hits.append(hit)
    hits.sort(key=lambda h: (-h["score"], h["library"], h["path"]))
    return hits


def layered(hits: list[dict], per_layer: dict[str, int] | None = None) -> dict:
    per_layer = per_layer or DEFAULT_PER_LAYER
    out: dict = {}
    for key, _label, libraries in LAYERS:
        picks = [h for h in hits if h["library"] in libraries and (key != "units" or h.get("id"))]
        out[key] = picks[: per_layer.get(key, 2)]
    return out


def guidance(layers: dict) -> list[str]:
    lines: list[str] = []
    unit = layers["units"][0] if layers["units"] else None
    skill = layers["skills"][0] if layers["skills"] else None
    page = layers["first-party"][0] if layers["first-party"] else None
    mag = layers["mag"][0] if layers["mag"] else None
    if unit:
        lines.append(f"Answer from {unit.get('id')} ({unit.get('status')}, {unit.get('verification')}): {unit['title']}")
    elif not (skill or page or layers["drafts"] or mag):
        lines.append("Nothing in the libraries matches this wording: try the exact Amazon notice or other words, and add a unit after the question is resolved (/kb-add).")
    else:
        lines.append("No knowledge unit matches yet: answer from the skill and the first-party page, and add a unit afterwards (/kb-add).")
    if skill:
        lines.append(f"Procedure: {skill['path']}")
    if page:
        lines.append(f"Rule check: {page['path']}")
    if mag:
        state = [f"status {mag['sop_status']}"]
        if mag.get("revised_at"):
            state.append(f"site revision {_ddmmyyyy(mag['revised_at'])}")
        if mag.get("changed_since_capture"):
            state.append("changed on the site since our capture, verify live before relying on it")
        if mag.get("superseded_by"):
            state.append(f"superseded by {mag['superseded_by']}")
        lines.append(f"External fallback only: {mag['path']} ({'; '.join(state)})")
    return lines


def render(question: str, layers: dict) -> str:
    out = [f"Question: {question}", ""]
    for line in guidance(layers):
        out.append(f"- {line}")
    for key, label, _libraries in LAYERS:
        picks = layers[key]
        if not picks:
            continue
        out += ["", f"## {label}"]
        for h in picks:
            tags = []
            if h.get("status"):
                tags.append(f"{h['status']}, {h.get('verification')}")
            if h.get("sop_status"):
                tags.append(h["sop_status"])
                if h.get("revised_at"):
                    tags.append(f"revised {_ddmmyyyy(h['revised_at'])}")
                if h.get("changed_since_capture"):
                    tags.append("changed since capture")
            if h.get("superseded_by"):
                tags.append(f"superseded by {h['superseded_by']}")
            tag = f" [{'; '.join(tags)}]" if tags else ""
            out.append(f"- ({h['score']}) {h['title']}{tag}")
            out.append(f"  {h['path']}")
    return "\n".join(out)


def answer(question: str, root: Path = WORKSPACE_ROOT, per_layer: dict[str, int] | None = None) -> dict:
    hits = collect(question, root)
    layers = layered(hits, per_layer)
    return {"question": question, "guidance": guidance(layers), "layers": layers, "total_hits": len(hits)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Answer an Amazon question from the local libraries, ranked by authority.")
    parser.add_argument("question")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--per-layer", type=int, default=None, help="hits per layer (default 3/3/3/2/2)")
    parser.add_argument("--root", default=str(WORKSPACE_ROOT))
    args = parser.parse_args(argv)
    per_layer = {k: args.per_layer for k in DEFAULT_PER_LAYER} if args.per_layer else None
    try:
        result = answer(args.question, Path(args.root), per_layer)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render(args.question, result["layers"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
