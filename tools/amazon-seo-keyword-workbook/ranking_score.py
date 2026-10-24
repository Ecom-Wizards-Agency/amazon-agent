#!/usr/bin/env python3
"""
Keyword ranking score: a calculated equivalent of DataDive's Ranking Juice.

Scores listing copy against a master keyword list (keyword + search volume)
from any keyword source, so a workbook built from SoldScope data can score
copy the same way a DataDive niche does.

Method (decoded from a DataDive niche on 2026-10-24, see
skills/amazon-seo/references/seo-writing-methodology.md section 2):

* Fields and weights: total = 3 x title + 2 x bullets + 1 x description.
* Incremental credit: a field earns a keyword's SV only for the match quality
  it adds over the higher-priority fields (title, then bullets, then
  description): credit = SV x max(0, tier_in_field - best_tier_in_higher_fields).
* Match tiers: exact contiguous phrase 1.0; exact phrase after simple
  singularization 0.75; all keyword tokens in any order 0.5; all tokens after
  singularization 0.25; else 0.
* Item Highlights count with the title by default (configurable). Backend
  search terms are not scored.

CLI
---
    python3 tools/amazon-seo-keyword-workbook/ranking_score.py \
        --keywords <core-mkl.csv | get_niche_keywords.json> \
        [--listing <listing-reference.json>] [--seo-content <seo_content.json>] \
        [--compare-datadive <ranking-juice.json>] [--json]
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import statistics
import sys
import unicodedata
from typing import Any, Iterable

DEFAULT_WEIGHTS = {"title": 3.0, "bullets": 2.0, "description": 1.0}
FIELDS = ("title", "bullets", "description")
HIGHLIGHT_FIELDS = ("title", "bullets", "description", "none")
TIER_EXACT = 1.0
TIER_EXACT_SINGULAR = 0.75
TIER_ANY_ORDER = 0.5
TIER_ANY_ORDER_SINGULAR = 0.25

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_KEYWORD_HEADERS = {"search terms", "search term", "keyword", "keywords"}
_SV_HEADERS = {"sv", "search volume"}


# --------------------------------------------------------------------------- #
# Text matching
# --------------------------------------------------------------------------- #
def tokenize(text: Any) -> list[str]:
    """Lowercase, unescape HTML entities, drop U+FFFC, fold accents, split [a-z0-9]+."""
    if text is None:
        return []
    s = html.unescape(str(text)).replace("\ufffc", "").lower().replace("ß", "ss")
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return _TOKEN_RE.findall(s)


def singularize(word: str) -> str:
    """Strip a trailing 's' from words longer than 3 chars that do not end in 'ss'."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


class _Text:
    """Pre-tokenized text, so many keywords can be matched cheaply."""

    __slots__ = ("joined", "joined_s", "tokens", "tokens_s")

    def __init__(self, text: Any):
        toks = tokenize(text)
        sing = [singularize(w) for w in toks]
        self.joined = " " + " ".join(toks) + " "
        self.joined_s = " " + " ".join(sing) + " "
        self.tokens = set(toks)
        self.tokens_s = set(sing)

    def tier(self, kw_tokens: list[str], kw_tokens_s: list[str]) -> float:
        if not kw_tokens:
            return 0.0
        if " " + " ".join(kw_tokens) + " " in self.joined:
            return TIER_EXACT
        if " " + " ".join(kw_tokens_s) + " " in self.joined_s:
            return TIER_EXACT_SINGULAR
        if set(kw_tokens) <= self.tokens:
            return TIER_ANY_ORDER
        if set(kw_tokens_s) <= self.tokens_s:
            return TIER_ANY_ORDER_SINGULAR
        return 0.0


def match_tier(keyword: str, text: Any) -> float:
    """Match quality of one keyword in one text: 1.0, 0.75, 0.5, 0.25 or 0."""
    toks = tokenize(keyword)
    return _Text(text).tier(toks, [singularize(w) for w in toks])


# --------------------------------------------------------------------------- #
# Scoring
# --------------------------------------------------------------------------- #
def _join(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value if v is not None)
    return str(value)


def resolve_weights(weights: dict | None) -> dict:
    out = dict(DEFAULT_WEIGHTS)
    for key, value in (weights or {}).items():
        if key in out and value is not None:
            out[key] = float(value)
    return out


def score_listing(
    keywords: Iterable[tuple[str, float]],
    title: Any,
    bullets: Any,
    description: Any = "",
    item_highlights: Any = "",
    weights: dict | None = None,
    highlights_field: str = "title",
) -> dict:
    """Score one listing against [(keyword, sv), ...].

    Returns per-field scores (unweighted SV credit), the weighted total,
    max_possible (= weight_title x sum SV), pct_of_max and keywords_credited.
    """
    w = resolve_weights(weights)
    if highlights_field not in HIGHLIGHT_FIELDS:
        raise ValueError(f"highlights_field must be one of {HIGHLIGHT_FIELDS}, got {highlights_field!r}")
    texts = {"title": _join(title), "bullets": _join(bullets), "description": _join(description)}
    highlights = _join(item_highlights).strip()
    if highlights and highlights_field != "none":
        texts[highlights_field] = (texts[highlights_field] + " " + highlights).strip()
    parsed = {f: _Text(texts[f]) for f in FIELDS}

    field_scores = {f: 0.0 for f in FIELDS}
    sv_total = 0.0
    credited = scored = 0
    for keyword, sv in keywords:
        sv = float(sv or 0)
        toks = tokenize(keyword)
        if not toks or sv <= 0:
            continue
        sv_total += sv
        scored += 1
        toks_s = [singularize(t) for t in toks]
        best = 0.0
        any_credit = False
        for f in FIELDS:
            tier = parsed[f].tier(toks, toks_s)
            gain = max(0.0, tier - best)
            if gain > 0:
                field_scores[f] += sv * gain
                any_credit = True
            best = max(best, tier)
        credited += any_credit

    total = sum(w[f] * field_scores[f] for f in FIELDS)
    max_possible = w["title"] * sv_total
    return {
        "title": field_scores["title"],
        "bullets": field_scores["bullets"],
        "description": field_scores["description"],
        "total": total,
        "max_possible": max_possible,
        "pct_of_max": round(100.0 * total / max_possible, 2) if max_possible else 0.0,
        "keywords_credited": credited,
        "keywords_scored": scored,
        "weights": w,
        "highlights_field": highlights_field,
    }


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #
def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _to_number(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def keywords_from_rows(rows: list[list[Any]]) -> list[tuple[str, float]]:
    """[(keyword, sv)] from MKL CSV rows. Headers are found by name; like the
    builder's own MKL readers, missing names fall back to columns 1 (keyword)
    and 2 (SV). Every row is scored, as DataDive scores every MKL row."""
    if not rows:
        return []
    header = [_norm(h) for h in rows[0]]
    kw_i = next((i for i, h in enumerate(header) if h in _KEYWORD_HEADERS), 1)
    sv_i = next((i for i, h in enumerate(header) if h in _SV_HEADERS), 2)
    return _keep_scorable(
        (row[kw_i], _to_number(row[sv_i]) if sv_i < len(row) else 0.0)
        for row in rows[1:] if kw_i < len(row)
    )


def _keep_scorable(pairs: Iterable[tuple[Any, float]]) -> list[tuple[str, float]]:
    """Drop rows whose keyword has no tokens; keep every other row, variants included."""
    return [(str(kw).strip(), sv) for kw, sv in pairs if tokenize(kw)]


def load_keywords(path: str) -> list[tuple[str, float]]:
    """Core MKL CSV (builder format) or DataDive get_niche_keywords JSON."""
    if path.lower().endswith(".json"):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("keywords", []) if isinstance(data, dict) else data
        return _keep_scorable(
            (it.get("keyword") or it.get("searchTerm") or "",
             _to_number(it.get("searchVolume", it.get("sv", 0))))
            for it in items if isinstance(it, dict)
        )
    with open(path, newline="", encoding="utf-8-sig") as f:
        return keywords_from_rows(list(csv.reader(f)))


def listings_from_data(data: Any) -> list[dict]:
    """Listing-reference / capture JSON -> [{asin, title, bullets, description, item_highlights}]."""
    if isinstance(data, dict):
        items = data.get("listings") or ([data] if data.get("asin") else [])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    out = []
    for it in items:
        if not isinstance(it, dict) or not it.get("asin"):
            continue
        bullets = it.get("bullets") or it.get("bullet_points") or []
        if isinstance(bullets, str):
            bullets = [b for b in bullets.splitlines() if b.strip()]
        out.append({
            "asin": str(it["asin"]).strip(),
            "title": it.get("title") or "",
            "bullets": list(bullets),
            "description": it.get("description") or "",
            "item_highlights": it.get("item_highlights") or it.get("itemHighlights") or "",
        })
    return out


def _copy_line(value: Any) -> str:
    """First non-empty line of a New Listing cell; '(' placeholders count as empty."""
    for line in str(value or "").splitlines():
        if line.strip():
            line = line.strip()
            return "" if line.startswith("(") else line
    return ""


def draft_from_seo_rows(rows: list[dict], key: str = "new") -> dict:
    """Title / Item Highlights / Bullet 1-5 / Description copy from seo_content rows."""
    draft = {"title": "", "item_highlights": "", "bullets": [], "description": ""}
    for row in rows or []:
        section = _norm(row.get("section"))
        line = _copy_line(row.get(key))
        if section.startswith("title"):
            draft["title"] = draft["title"] or line
        elif section.startswith("item highlight"):
            draft["item_highlights"] = draft["item_highlights"] or line
        elif section.startswith("bullet"):
            if line:
                draft["bullets"].append(line)
        elif section.startswith("description"):
            draft["description"] = draft["description"] or line
    return draft


def has_copy(listing: dict) -> bool:
    return any(_join(listing.get(k)).strip() for k in ("title", "bullets", "description", "item_highlights"))


def score_entry(keywords, listing: dict, weights=None, highlights_field="title") -> dict:
    return score_listing(
        keywords, listing.get("title"), listing.get("bullets"), listing.get("description", ""),
        listing.get("item_highlights", ""), weights=weights, highlights_field=highlights_field,
    )


def datadive_scores(data: dict) -> dict[str, dict]:
    """{asin: {title, bullets, description, total}} from a get_ranking_juice JSON."""
    out = {}
    for comp in (data or {}).get("competitors") or []:
        listing = comp.get("listing") or {}
        out[str(comp.get("asin", "")).strip()] = {
            "title": (listing.get("title") or {}).get("rankingJuice") or 0,
            "bullets": (listing.get("bullets") or {}).get("rankingJuice") or 0,
            "description": (listing.get("description") or {}).get("rankingJuice") or 0,
            "total": listing.get("rankingJuice") or 0,
        }
    return out


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _ratio(ours: float, theirs: float) -> float | None:
    return round(ours / theirs, 3) if theirs else None


def run(args: argparse.Namespace) -> dict:
    keywords = load_keywords(args.keywords)
    weights = json.loads(args.weights) if args.weights else None
    rows = []
    if args.listing:
        with open(args.listing, encoding="utf-8") as f:
            for item in listings_from_data(json.load(f)):
                rows.append({"name": item["asin"], **score_entry(keywords, item, weights, args.highlights_field)})
    if args.seo_content:
        with open(args.seo_content, encoding="utf-8") as f:
            seo = json.load(f)
        draft = draft_from_seo_rows(seo.get("rows") or [])
        rows.append({"name": "Draft", **score_entry(keywords, draft, weights, args.highlights_field)})
    out: dict[str, Any] = {"keywords": len(keywords), "rows": rows}
    if args.compare_datadive:
        with open(args.compare_datadive, encoding="utf-8") as f:
            dd = datadive_scores(json.load(f))
        ours = {r["name"]: r for r in rows}
        comparison = []
        for asin, d in dd.items():
            o = ours.get(asin)
            if not o:
                comparison.append({"asin": asin, "missing": True, "datadive_total": d["total"]})
                continue
            comparison.append({
                "asin": asin,
                "datadive": d,
                "ours": {f: round(o[f]) for f in ("title", "bullets", "description", "total")},
                "ratio_total": _ratio(o["total"], d["total"]),
                "ratio_title": _ratio(o["title"], d["title"]),
            })
        present = [c for c in comparison if not c.get("missing")]
        order_dd = [c["asin"] for c in sorted(present, key=lambda c: -c["datadive"]["total"])]
        order_ours = [c["asin"] for c in sorted(present, key=lambda c: -c["ours"]["total"])]
        out["datadive_comparison"] = {
            "rows": comparison,
            "median_ratio_total": median([c["ratio_total"] for c in present if c["ratio_total"]]),
            "median_ratio_title": median([c["ratio_title"] for c in present if c["ratio_title"]]),
            "order_datadive": order_dd,
            "order_ours": order_ours,
        }
    return out


def _fmt(value: float) -> str:
    return f"{value:,.0f}"


def print_table(out: dict) -> None:
    print(f"Keywords scored against: {out['keywords']}")
    header = f"{'Listing':<14} {'Title':>12} {'Bullets':>12} {'Descr.':>12} {'Total':>14} {'% of max':>9}"
    print(header)
    print("-" * len(header))
    for r in sorted(out["rows"], key=lambda r: -r["total"]):
        print(f"{r['name']:<14} {_fmt(r['title']):>12} {_fmt(r['bullets']):>12} "
              f"{_fmt(r['description']):>12} {_fmt(r['total']):>14} {r['pct_of_max']:>8.2f}%")
    cmp_ = out.get("datadive_comparison")
    if not cmp_:
        return
    print("\nOurs vs DataDive")
    header = (f"{'ASIN':<14} {'DD title':>11} {'ours':>11} {'ratio':>6} {'DD bullets':>11} {'ours':>9} "
              f"{'DD descr.':>10} {'ours':>9} {'DD total':>12} {'ours':>12} {'ratio':>6}")
    print(header)
    print("-" * len(header))
    for c in cmp_["rows"]:
        if c.get("missing"):
            print(f"{c['asin']:<14} not in --listing (DataDive total {_fmt(c['datadive_total'])})")
            continue
        d, o = c["datadive"], c["ours"]
        print(f"{c['asin']:<14} {_fmt(d['title']):>11} {_fmt(o['title']):>11} {c['ratio_title'] or 0:>6.3f} "
              f"{_fmt(d['bullets']):>11} {_fmt(o['bullets']):>9} {_fmt(d['description']):>10} "
              f"{_fmt(o['description']):>9} {_fmt(d['total']):>12} {_fmt(o['total']):>12} {c['ratio_total'] or 0:>6.3f}")
    print(f"median ratio: title {cmp_['median_ratio_title']} | total {cmp_['median_ratio_total']}")
    print(f"order DataDive: {' > '.join(cmp_['order_datadive'])}")
    print(f"order ours    : {' > '.join(cmp_['order_ours'])}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Calculate a keyword ranking score (Ranking Juice equivalent).")
    p.add_argument("--keywords", required=True, help="Core MKL CSV or DataDive get_niche_keywords JSON")
    p.add_argument("--listing", help="listing-reference or capture JSON ({listings:[{asin,title,bullets,description}]})")
    p.add_argument("--seo-content", help="seo_content JSON; its New Listing copy is scored as 'Draft'")
    p.add_argument("--compare-datadive", help="DataDive get_ranking_juice JSON to compare per ASIN")
    p.add_argument("--weights", help='JSON weights, e.g. \'{"title":3,"bullets":2,"description":1}\'')
    p.add_argument("--highlights-field", default="title", choices=HIGHLIGHT_FIELDS,
                   help="field that Item Highlights are scored with (default: title)")
    p.add_argument("--json", action="store_true", help="print JSON instead of a table")
    args = p.parse_args(argv)
    if not args.listing and not args.seo_content:
        p.error("give --listing and/or --seo-content")
    try:
        out = run(args)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print_table(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
