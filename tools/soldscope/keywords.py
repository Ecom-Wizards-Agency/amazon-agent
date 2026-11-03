#!/usr/bin/env python3
"""SoldScope keyword research pages -> keyword-workbook builder CSVs and research.json.

Inputs are saved MCP responses, never live calls:
  --pages        keyword_research_get_multi_results pages (one multi-ASIN search)
  --asin-pages   kr_get_results pages, one single-ASIN search per ASIN, merged here
                 (marketplaces outside the 8 that support multi-ASIN research)
  --live-info    optional product_live_info_get responses (fills competitor gaps)

Outputs in --out-dir:
  roots.csv            "", Normalized Root, Frequency, Broad Search Volume, <0-1 score>
  core.csv             "", Search Terms, SV, Relev., Sugg. bid & range, <ASIN cols, anchor first>
  expanded.csv         same shape, the 1% pool
  competitors.csv      asin, brand, seller country, variations, rating, review count, price,
                       30d sales, 30d revenue, fulfillment, category
  research.json        provider, run identity, statistics, pool keywords, competitors, benchmark
  keywords-receipt.json  reconciliation, thresholds, relevancy choice, input sha256 list

Relevancy is written on a 0-1 scale. SoldScope's native multi-ASIN `relevancy` is 0-100
and rank-weighted; it is divided by 100. The computed relevancy is the share of compared
ASINs ranking organically in the top N (default 50), which is how DataDive's Relev.
behaved. `--relevancy auto` keeps native only while it tracks the computed share.

Exit 2 when the pages do not reconcile (rows read != meta.total, or
unique + dropped + merged != rows read) or the marketplace does not match. On a failure
only keywords-receipt.json is written. See tools/soldscope/README.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RANK_CAP = 101          # ranks above 100 and "beyond the scrape" fold to 101
P1_RANK_MAX = 48        # DataDive's kwRankedOnP1 matched organic rank <= 48 on saved niches
MULTI_MARKETS = {"US", "CA", "MX", "UK", "DE", "ES", "FR", "IT"}
FULFILLMENT = {1: "AMZ", 2: "FBA", 3: "FBM"}   # 1 observed as an Amazon.com buy box
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
STOP = {"a", "an", "the", "of", "for", "to", "and", "with", "in", "on", "by", "from", "or",
        "de", "para", "con", "el", "la", "del", "y", "w", "&", "+",
        "und", "mit", "fur", "für", "der", "die", "das", "et", "le", "les", "des", "pour", "per", "di"}
OUTPUT_FILES = ("roots.csv", "core.csv", "expanded.csv", "competitors.csv", "research.json")
MKL_HEADER = ["", "Search Terms", "SV", "Relev.", "Sugg. bid & range"]
COMP_HEADER = ["asin", "brand", "seller country", "variations", "rating", "review count",
               "price", "30d sales", "30d revenue", "fulfillment", "category"]


class AdapterError(Exception):
    """Input that cannot produce trustworthy output. Exit code 2."""


# ----------------------------------------------------------------------------- helpers

def load_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AdapterError(f"cannot read {path}: {exc}") from exc


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_PREFIX_PLUS = re.compile(r"(?:(?<=\s)|^)\+(?=\w)")
_INFIX_PLUS = re.compile(r"(?<=\w\w)\+(?=\w\w)")


def clean_keyword(raw) -> tuple[str | None, str]:
    """Return (cleaned keyword, "") or (None, reason) for junk rows.

    Decodes HTML entities, removes U+FFFC and zero-width characters, strips edge quotes,
    turns URL-style '+' joins ("giant+widget+seeds", "brand +widget +spray") into spaces while
    keeping a free-standing '+' ("cleaner + polish") and a trailing one ("aloe cure+"),
    folds case and whitespace, and drops product-title fragments that contain '|'."""
    k = html.unescape(str(raw or ""))
    k = k.replace("￼", " ").replace("​", "").replace("﻿", "")
    k = _INFIX_PLUS.sub(" ", k)
    k = _PREFIX_PLUS.sub("", k)
    k = re.sub(r"\s+", " ", k).strip().strip("'\"").strip()
    k = re.sub(r"\s+", " ", k).lower()
    if not k:
        return None, "empty after cleaning"
    if "|" in k:
        return None, "product-title fragment ('|')"
    return k, ""


def rank_value(v) -> int | None:
    """Positive rank as an int, else None (0, null, missing and junk mean not ranked)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
        return None
    return int(v)


def cap_rank(v) -> int | None:
    r = rank_value(v)
    if r is None:
        return None
    return RANK_CAP if r > 100 else r


def singular(word: str, vocab: set[str]) -> str:
    """Conservative plural folding: only when the singular also occurs in the vocabulary."""
    if len(word) > 3 and word.endswith("ies") and word[:-3] + "y" in vocab:
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")) and word[:-1] in vocab:
        return word[:-1]
    return word


def pearson(xs, ys) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sxy / (sx * sy) if sx and sy else float("nan")


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _median(vals):
    vals = [v for v in vals if _num(v) is not None]
    return statistics.median(vals) if vals else None


def _page_data(page) -> dict:
    if not isinstance(page, dict):
        raise AdapterError("page is not a JSON object")
    data = page.get("data", page)
    return data if isinstance(data, dict) else {"keywords": data}


def _page_keywords(page) -> list:
    data = _page_data(page)
    kws = data.get("keywords")
    if kws is None and isinstance(page.get("data"), list):
        kws = page["data"]
    if not isinstance(kws, list):
        raise AdapterError("page has no keywords list")
    return kws


def _page_meta(page) -> dict:
    meta = page.get("meta") if isinstance(page, dict) else None
    if not isinstance(meta, dict) or "total" not in meta:
        raise AdapterError("page has no meta.total; save the full MCP response")
    return meta


# ----------------------------------------------------------------------------- reading

def read_pages(paths: list[Path], label: str) -> dict:
    """Read one search's pages. Returns rows, meta_total, details, summary, marketplaces."""
    rows: list[dict] = []
    totals = set()
    seen_pages: dict[int, Path] = {}
    details: dict[str, dict] = {}
    detail_order: list[str] = []
    summary: dict[str, dict] = {}
    markets: set[str] = set()
    seen_kw: dict[str, Path] = {}
    for p in paths:
        page = load_json(p)
        meta = _page_meta(page)
        totals.add(int(meta["total"]))
        cur = meta.get("current_page")
        if cur is not None:
            if cur in seen_pages:
                raise AdapterError(f"{label}: page {cur} given twice ({seen_pages[cur]} and {p})")
            seen_pages[cur] = p
        data = _page_data(page)
        for d in data.get("productDetails") or []:
            a = str(d.get("asin") or "").upper()
            if a and a not in details:
                details[a] = d
                detail_order.append(a)
            if d.get("marketplace"):
                markets.add(str(d["marketplace"]).upper())
        for a, s in (data.get("productsSummary") or {}).items():
            if a != "median" and isinstance(s, dict):
                summary.setdefault(str(a).upper(), s)
        for r in _page_keywords(page):
            if isinstance(r, dict):
                k = r.get("keyword")
                if isinstance(k, str):
                    # One search never repeats a raw keyword (0 repeats in 23,837 saved
                    # rows). A repeat means pages overlapped and another row was lost.
                    if k in seen_kw:
                        raise AdapterError(f"{label}: keyword {k!r} appears twice ({seen_kw[k]} and {p}); "
                                           "unstable paging, re-fetch the search")
                    seen_kw[k] = p
                rows.append(r)
                if r.get("marketplace"):
                    markets.add(str(r["marketplace"]).upper())
    if len(totals) > 1:
        raise AdapterError(f"{label}: pages disagree on meta.total {sorted(totals)}; mixed searches?")
    return dict(rows=rows, meta_total=totals.pop() if totals else 0, details=details,
                detail_order=detail_order, summary=summary, markets=markets,
                pages=sorted(seen_pages))


def read_live_info(paths: list[Path]) -> dict[str, dict]:
    live: dict[str, dict] = {}
    for p in paths:
        d = load_json(p)
        results = d.get("results") if isinstance(d, dict) else None
        if isinstance(d, dict) and isinstance(d.get("data"), dict) and results is None:
            results = d["data"].get("results")
        for asin, res in (results or {}).items():
            if isinstance(res, dict) and res.get("status") == "completed" and isinstance(res.get("data"), dict):
                live[str(asin).upper()] = res["data"]
    return live


def parse_asin_pages(specs: list[str]) -> list[tuple[str, list[Path]]]:
    out = []
    for spec in specs:
        if "=" not in spec:
            raise AdapterError(f"--asin-pages wants ASIN=PAGE.json[,PAGE.json], got {spec!r}")
        asin, files = spec.split("=", 1)
        asin = asin.strip().upper()
        if not ASIN_RE.match(asin):
            raise AdapterError(f"--asin-pages: {asin!r} is not an ASIN")
        out.append((asin, [Path(f) for f in files.split(",") if f.strip()]))
    return out


def _positions(r: dict) -> dict:
    pos = r.get("asinsPositions")
    return pos if isinstance(pos, dict) else {}


def _single_asin_ranks(r: dict, asin: str) -> tuple[int | None, int | None]:
    """Organic and sponsored rank of the analyzed ASIN in a kr_get_results row.

    The single-ASIN shape is not captured yet. Read asinsPositions[asin] when present,
    else the top-level organicRank/sponsoredRank, else mainOrganicRank/mainSponsoredRank."""
    p = _positions(r).get(asin)
    if isinstance(p, dict):
        return rank_value(p.get("organicRank")), rank_value(p.get("sponsoredRank"))
    org = r.get("organicRank", r.get("mainOrganicRank"))
    spo = r.get("sponsoredRank", r.get("mainSponsoredRank"))
    return rank_value(org), rank_value(spo)


# ----------------------------------------------------------------------------- core logic

def make_record(kw: str, r: dict) -> dict:
    return {"keyword": kw, "raw_keyword": r.get("keyword"), "sv": _num(r.get("searchVolume")),
            "native_raw": _num(r.get("relevancy")),
            "cpc": _num(r.get("cpc")), "cpcMin": _num(r.get("cpcMin")), "cpcMax": _num(r.get("cpcMax")),
            "ranks": {}, "sponsored": {}}


def dedupe(rows: list[dict], fill_ranks) -> tuple[dict[str, dict], list, list]:
    """Clean and dedupe rows. Keeps the higher-SV duplicate (the scratch adapter's rule)."""
    by_kw: dict[str, dict] = {}
    dropped, merged = [], []
    for r in rows:
        kw, why = clean_keyword(r.get("keyword"))
        if kw is None:
            dropped.append({"keyword": r.get("keyword"), "reason": why})
            continue
        rec = make_record(kw, r)
        fill_ranks(rec, r)
        prev = by_kw.get(kw)
        if prev is None:
            by_kw[kw] = rec
            continue
        keep, lose = (rec, prev) if (rec["sv"] or 0) > (prev["sv"] or 0) else (prev, rec)
        by_kw[kw] = keep
        merged.append({"kept": keep["raw_keyword"], "merged": lose["raw_keyword"], "as": kw})
    return by_kw, dropped, merged


def resolve_asins(args, details_order: list[str], rows: list[dict]) -> list[str]:
    if args.asins:
        asins = [a.strip().upper() for a in args.asins.split(",") if a.strip()]
    elif details_order:
        asins = list(details_order)
    else:
        asins = []
        for r in rows:
            for a in _positions(r):
                a = str(a).upper()
                if a not in asins:
                    asins.append(a)
    if args.anchor:
        anchor = args.anchor.strip().upper()
        if not args.asins and asins and anchor not in asins:
            raise AdapterError(f"--anchor {anchor} is not in the pages' productDetails/asinsPositions {asins}")
        asins = [anchor] + [a for a in asins if a != anchor]
    bad = [a for a in asins if not ASIN_RE.match(a)]
    if bad:
        raise AdapterError(f"not ASINs: {bad}")
    if not asins:
        raise AdapterError("no ASINs: pass --asins or save pages with productDetails")
    if len(set(asins)) != len(asins):
        raise AdapterError(f"duplicate ASINs in {asins}")
    return asins


def bid_text(r: dict) -> str:
    if not r["cpc"]:
        return ""
    lo, hi = r["cpcMin"], r["cpcMax"]
    return f"{r['cpc']:.2f} ({lo:.2f}-{hi:.2f})" if lo is not None and hi is not None else f"{r['cpc']:.2f}"


def build_roots(core: list[dict], ngram_max: int, ngram_min_freq: int) -> list[tuple[str, int, int]]:
    """n-gram roots (1..ngram_max words) over the Core set, with Broad SV summed."""
    vocab = {w for r in core for w in r["keyword"].split()}
    freq: Counter = Counter()
    broad_sv: defaultdict = defaultdict(int)
    for r in core:
        toks = [singular(w, vocab) for w in r["keyword"].split()]
        grams = set()
        for n in range(1, ngram_max + 1):
            for i in range(len(toks) - n + 1):
                grams.add(" ".join(toks[i:i + n]))
        for g in grams:
            freq[g] += 1
            broad_sv[g] += r["sv"] or 0
    roots = [(g, freq[g], broad_sv[g]) for g in freq
             if g.split()[0] not in STOP and g.split()[-1] not in STOP
             and (len(g.split()) == 1 or freq[g] >= ngram_min_freq)]
    roots.sort(key=lambda t: (-t[2], -t[1], t[0]))
    return roots


def competitor_rows(asins, anchor, details, summary, live, core) -> tuple[list[dict], list[str]]:
    """Competitor rows. advertisedKws and kwRankedOnP1Percent count the Core list, the
    equivalent of the visible DataDive MKL those audit columns were measured on."""
    rows, missing = [], []
    n_core = len(core)
    for asin in asins:
        s = summary.get(asin) or {}
        d = details.get(asin) or {}
        x = live.get(asin) or {}
        if not (s or d or x):
            missing.append(asin)
        lp = (x.get("price") or {}).get("priceCents") if isinstance(x.get("price"), dict) else None
        cat = s.get("category")
        if isinstance(cat, dict):
            cat = cat.get("name")
        elif isinstance(cat, list):
            cat = (cat[0] or {}).get("name") if cat and isinstance(cat[0], dict) else None
        crumbs = x.get("breadcrumbs") or []
        bb = x.get("buyBoxInfo") or {}
        live_ff = ("AMZ" if str(bb.get("sellerName") or "").startswith("Amazon") else "FBA/FBM") if bb else None
        ff = s.get("fulfillmentType")
        price = _num(s.get("price"))
        if price is None and _num(lp) is not None:
            price = lp / 100
        sales = _num(s.get("sales"))
        if sales is None:
            sales = _num((x.get("sales") or {}).get("sales")) if isinstance(x.get("sales"), dict) else None
        revenue = _num(s.get("revenue"))
        if revenue is None and price is not None and sales is not None:
            revenue = round(price * sales, 2)
        reviews = _num(s.get("reviewCount"))
        if reviews is None:
            reviews = _num(x.get("ratingsCount"))
        variations = _num(s.get("variationsCount"))
        if variations is None:
            variations = _num((x.get("variationsInfo") or {}).get("totalVariationsCount"))
        rows.append({
            "asin": asin,
            "brand": s.get("brand") or d.get("brand") or (x.get("productDetails") or {}).get("brand")
            or (x.get("brandInfo") or {}).get("name") or "",
            "title": d.get("title") or x.get("title") or "",
            "price": price,
            "rating": _num(s.get("rating")) if _num(s.get("rating")) is not None else _num(x.get("rating")),
            "reviewCount": reviews,
            "reviews": reviews,
            "revenue": revenue,
            "sales": sales,
            "sellerCountry": "",
            "category": cat or (crumbs[0].get("name") if crumbs and isinstance(crumbs[0], dict) else "") or "",
            "variations": variations,
            "fulfillment": FULFILLMENT.get(ff, str(ff)) if ff is not None else (live_ff or ""),
            "advertisedKws": sum(1 for r in core if r["sponsored"].get(asin) is not None),
            "kwRankedOnP1Percent": round(sum(1 for r in core if (r["ranks"].get(asin) or RANK_CAP) <= P1_RANK_MAX)
                                         / n_core, 4) if n_core else 0.0,
            "isAnchor": asin == anchor,
        })
    return rows, missing


def _fmt(v, fmt=None):
    if v is None or v == "":
        return ""
    return format(v, fmt) if fmt else v


def write_csv(path: Path, header: list, rows: list[list]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(header)
        w.writerows(rows)


# ----------------------------------------------------------------------------- main

def run(args) -> dict:
    out_dir = Path(args.out_dir)
    inputs: list[dict] = []
    receipt: dict = {"ok": False, "provider": "soldscope", "errors": []}

    if bool(args.pages) == bool(args.asin_pages):
        raise AdapterError("pass exactly one of --pages (multi-ASIN) or --asin-pages (single-ASIN merge)")

    details: dict[str, dict] = {}
    summary: dict[str, dict] = {}
    markets: set[str] = set()
    merged_across = 0
    per_asin_counts = {}
    if args.pages:
        source = "keyword_research_search_multi_asin"
        paths = [Path(p) for p in args.pages]
        inputs += [{"role": "multi_results_page", "path": str(p), "sha256": sha256(p)} for p in paths]
        got = read_pages(paths, "pages")
        rows, meta_total = got["rows"], got["meta_total"]
        details, summary, markets = got["details"], got["summary"], got["markets"]
        asins = resolve_asins(args, got["detail_order"], rows)

        def fill(rec, r):
            pos = _positions(r)
            for a in asins:
                p = pos.get(a) or {}
                rec["ranks"][a] = rank_value(p.get("organicRank"))
                rec["sponsored"][a] = rank_value(p.get("sponsoredRank"))

        by_kw, dropped, merged = dedupe(rows, fill)
        raw_rows = len(rows)
        page_numbers = got["pages"]
    else:
        source = "kr_asin_search"
        specs = parse_asin_pages(args.asin_pages)
        spec_asins = [a for a, _ in specs]
        if len(set(spec_asins)) != len(spec_asins):
            raise AdapterError(f"--asin-pages names an ASIN twice: {spec_asins}")
        if args.asins:
            listed = [a.strip().upper() for a in args.asins.split(",") if a.strip()]
            if set(listed) != set(spec_asins):
                raise AdapterError(f"--asins {listed} does not match --asin-pages ASINs {spec_asins}")
            order = listed
        else:
            order = spec_asins
        if args.anchor:
            anchor_u = args.anchor.strip().upper()
            if anchor_u not in spec_asins:
                raise AdapterError(f"--anchor {anchor_u} has no --asin-pages entry")
            order = [anchor_u] + [a for a in order if a != anchor_u]
        asins = order
        by_kw, dropped, merged = {}, [], []
        raw_rows = meta_total = 0
        page_numbers = {}
        for asin, paths in specs:
            inputs += [{"role": f"kr_get_results_page:{asin}", "path": str(p), "sha256": sha256(p)} for p in paths]
            got = read_pages(paths, asin)
            if got["meta_total"] != len(got["rows"]):
                raise AdapterError(f"{asin}: read {len(got['rows'])} rows but meta.total is {got['meta_total']}")
            raw_rows += len(got["rows"])
            meta_total += got["meta_total"]
            page_numbers[asin] = got["pages"]
            markets |= got["markets"]
            for a, d in got["details"].items():
                details.setdefault(a, d)
            for a, s in got["summary"].items():
                summary.setdefault(a, s)

            def fill(rec, r, asin=asin):
                org, spo = _single_asin_ranks(r, asin)
                rec["ranks"][asin], rec["sponsored"][asin] = org, spo

            one, d_, m_ = dedupe(got["rows"], fill)
            dropped += [dict(x, asin=asin) for x in d_]
            merged += [dict(x, asin=asin) for x in m_]
            per_asin_counts[asin] = {"raw_rows": len(got["rows"]), "unique": len(one),
                                     "dropped": len(d_), "merged": len(m_)}
            for kw, rec in one.items():
                cur = by_kw.get(kw)
                if cur is None:
                    rec["native_raw"] = None   # single-ASIN scores do not describe the set
                    by_kw[kw] = rec
                    continue
                merged_across += 1
                cur["ranks"].update(rec["ranks"])
                cur["sponsored"].update(rec["sponsored"])
                if (rec["sv"] or 0) > (cur["sv"] or 0):
                    cur["sv"] = rec["sv"]
                for k in ("cpc", "cpcMin", "cpcMax"):
                    if cur[k] is None:
                        cur[k] = rec[k]
        for rec in by_kw.values():
            for a in asins:
                rec["ranks"].setdefault(a, None)
                rec["sponsored"].setdefault(a, None)

    anchor = args.anchor.strip().upper() if args.anchor else None
    marketplace = args.marketplace.upper() if args.marketplace else None
    if marketplace and markets and markets != {marketplace}:
        raise AdapterError(f"--marketplace {marketplace} but the pages are {sorted(markets)}")
    if not marketplace and len(markets) == 1:
        marketplace = next(iter(markets))
    warnings = []
    if source.endswith("multi_asin") and marketplace and marketplace not in MULTI_MARKETS:
        warnings.append(f"marketplace {marketplace} is outside the 8 multi-ASIN markets")
    if source.endswith("multi_asin") and details:
        extra = [a for a in asins if a not in details]
        if extra:
            warnings.append(f"ASINs not in the pages' productDetails: {extra}")

    recs = list(by_kw.values())
    unique = len(recs)
    merged_total = len(merged) + merged_across
    reconcile = {
        "raw_rows": raw_rows, "meta_total": meta_total, "unique": unique,
        "dropped": len(dropped), "merged": merged_total,
        "rows_equal_total": raw_rows == meta_total,
        "accounted": unique + len(dropped) + merged_total == raw_rows,
    }
    if source == "kr_asin_search":
        reconcile["merged_within_asin"] = len(merged)
        reconcile["joined_across_asins"] = merged_across
        reconcile["per_asin"] = per_asin_counts
    receipt.update(reconcile)
    receipt["inputs"] = inputs
    if not reconcile["rows_equal_total"]:
        raise AdapterError(f"read {raw_rows} rows but meta.total is {meta_total}; a page is missing or repeated",
                           receipt)
    if not reconcile["accounted"]:
        raise AdapterError(f"unique {unique} + dropped {len(dropped)} + merged {merged_total} != {raw_rows}",
                           receipt)

    # ---- relevancy ----------------------------------------------------------
    n_asins = len(asins)
    for r in recs:
        top = sum(1 for v in r["ranks"].values() if v is not None and v <= args.top_n)
        r["top_hits"] = top
        r["computed"] = top / n_asins
        r["native"] = (r["native_raw"] / 100.0) if r["native_raw"] is not None else None
    recs_sv = [r for r in recs if r["sv"]]
    has_native = any(r["native"] for r in recs_sv)
    agreement = None
    if has_native:
        scored = [r for r in recs_sv if r["computed"] > 0 or (r["native"] or 0) > 0]
        rp_ = pearson([r["computed"] for r in scored], [r["native"] or 0 for r in scored])
        core_c = {r["keyword"] for r in recs_sv if r["computed"] >= args.core_min}
        core_n = {r["keyword"] for r in recs_sv if (r["native"] or 0) >= args.core_min}
        union = core_c | core_n
        jac = len(core_c & core_n) / len(union) if union else 1.0
        agreement = {"pearson_r_on_nonzero_rows": None if math.isnan(rp_) else round(rp_, 4),
                     "nonzero_rows": len(scored), "core_membership_jaccard": round(jac, 4),
                     "core_computed": len(core_c), "core_native": len(core_n),
                     "pool_computed": sum(1 for r in recs_sv if r["computed"] >= args.pool_min),
                     "pool_native": sum(1 for r in recs_sv if (r["native"] or 0) >= args.pool_min)}
    choice = args.relevancy
    if choice == "native" and not has_native:
        raise AdapterError("--relevancy native but the pages carry no native relevancy "
                           "(single-ASIN merge or all zero)", receipt)
    if choice == "auto":
        ok = (agreement and agreement["pearson_r_on_nonzero_rows"] is not None
              and agreement["core_membership_jaccard"] >= 0.9 and agreement["pearson_r_on_nonzero_rows"] >= 0.9)
        choice = "native" if ok else "computed"
    for r in recs:
        r["rel"] = (r["native"] or 0.0) if choice == "native" else r["computed"]

    # ---- pool / core --------------------------------------------------------
    allow = {w.strip().lower() for w in (args.allow_one_word or "").split(",") if w.strip()}

    def in_pool(r):
        return r["rel"] >= args.pool_min and r["top_hits"] >= args.pool_min_top_asins

    def in_core(r):
        one_word_ok = len(r["keyword"].split()) > 1 or r["keyword"] in allow
        return in_pool(r) and r["rel"] >= args.core_min and one_word_ok

    order = lambda r: (-r["rel"], -(r["sv"] or 0), r["keyword"])  # noqa: E731
    pool = sorted((r for r in recs_sv if in_pool(r)), key=order)
    core = [r for r in pool if in_core(r)]
    core_set = {r["keyword"] for r in core}
    one_word_removed = sorted((r for r in pool if r["rel"] >= args.core_min and r["keyword"] not in core_set),
                              key=lambda r: -(r["sv"] or 0))
    pool_removed = [r for r in recs_sv if r["rel"] >= args.pool_min and not in_pool(r)]

    roots = build_roots(core, args.ngram_max, args.ngram_min_freq)
    live_paths = [Path(p) for p in args.live_info or []]
    inputs += [{"role": "live_info", "path": str(p), "sha256": sha256(p)} for p in live_paths]
    live = read_live_info(live_paths)
    comps, comps_missing = competitor_rows(asins, anchor, details, summary, live, core)
    with_data = [c for c in comps if c["asin"] not in comps_missing]
    benchmark = {"price": _median(c["price"] for c in with_data),
                 "reviewCount": _median(c["reviewCount"] for c in with_data),
                 "rating": _median(c["rating"] for c in with_data),
                 "basis": f"median of {len(with_data)} compared ASINs"}

    # ---- write --------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)

    def mkl_rows(rs):
        return [["", r["keyword"], r["sv"], round(r["rel"], 4), bid_text(r),
                 *[_fmt(cap_rank(r["ranks"][a])) for a in asins]] for r in rs]

    write_csv(out_dir / "core.csv", MKL_HEADER + asins, mkl_rows(core))
    write_csv(out_dir / "expanded.csv", MKL_HEADER + asins, mkl_rows(pool))
    top_sv = roots[0][2] if roots else 0
    write_csv(out_dir / "roots.csv", ["", "Normalized Root", "Frequency", "Broad Search Volume", ""],
              [["", g, fr, sv, (sv / top_sv) if top_sv else 0] for g, fr, sv in roots])
    write_csv(out_dir / "competitors.csv", COMP_HEADER, [[
        c["asin"], c["brand"], c["sellerCountry"], _fmt(c["variations"]), _fmt(c["rating"]),
        _fmt(c["reviewCount"]), _fmt(c["price"], ".2f"), _fmt(c["sales"]), _fmt(c["revenue"], ".2f"),
        c["fulfillment"], c["category"]] for c in comps])

    search_id = None
    if args.search_id:
        ids = [int(s) if s.strip().isdigit() else s.strip() for s in str(args.search_id).split(",") if s.strip()]
        search_id = ids[0] if len(ids) == 1 and source.endswith("multi_asin") else ids
    research = {
        "provider": "soldscope", "source": source, "search_id": search_id,
        "marketplace": marketplace, "asins": asins, "anchor": anchor,
        "date_from": args.date_from, "date_to": args.date_to,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "statistics": {"numKeywords": len(pool), "rawRows": raw_rows, "uniqueRows": unique,
                       "poolRows": len(pool), "coreRows": len(core)},
        "keywords": [{"keyword": r["keyword"], "searchVolume": int(r["sv"]) if r["sv"] is not None else None,
                      "relevancy": round(r["rel"], 4),
                      "asinRanks": {a: cap_rank(r["ranks"][a]) for a in asins},
                      "sponsoredAsinRanks": {a: cap_rank(r["sponsored"][a]) for a in asins},
                      "origin": "core" if r["keyword"] in core_set else "pool"} for r in pool],
        "competitors": comps,
        "benchmark": benchmark,
    }
    (out_dir / "research.json").write_text(json.dumps(research, indent=1, ensure_ascii=False), encoding="utf-8")

    receipt.update({
        "ok": True, "source": source, "search_id": search_id, "marketplace": marketplace,
        "asins": asins, "anchor": anchor, "pages": page_numbers,
        "no_search_volume": unique - len(recs_sv), "with_search_volume": len(recs_sv),
        "core_rows": len(core), "core_sv": sum(r["sv"] for r in core),
        "pool_rows": len(pool), "pool_sv": sum(r["sv"] for r in pool),
        "core_subset_of_pool": True, "roots_rows": len(roots),
        "competitor_rows": len(comps), "competitors_missing_data": comps_missing,
        "relevancy": {"requested": args.relevancy, "choice": choice,
                      "definition": ("SoldScope native relevancy / 100 (rank-weighted, 0-1)" if choice == "native"
                                     else f"share of the {n_asins} compared ASINs ranking organically "
                                          f"in the top {args.top_n}"),
                      "agreement": agreement},
        "thresholds": {"core_min": args.core_min, "pool_min": args.pool_min, "top_n": args.top_n,
                       "pool_min_top_asins": args.pool_min_top_asins, "ngram_max": args.ngram_max,
                       "ngram_min_freq": args.ngram_min_freq, "p1_rank_max": P1_RANK_MAX,
                       "rank_cap": RANK_CAP, "allow_one_word": sorted(allow)},
        "noise_filters": {
            "pool_rule": f"relevancy >= {args.pool_min} and >= {args.pool_min_top_asins} compared ASIN(s) "
                         f"at organic rank <= {args.top_n}",
            "core_rule": f"in pool, relevancy >= {args.core_min}, more than one word unless allow-listed",
            "pool_rows_removed": len(pool_removed), "pool_sv_removed": sum(r["sv"] for r in pool_removed),
            "core_one_word_removed": [[r["keyword"], r["sv"]] for r in one_word_removed]},
        "warnings": warnings,
        "outputs": list(OUTPUT_FILES),
        "dropped_keywords": dropped,
        "merged_keywords": merged,
    })
    return receipt


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pages", nargs="+", help="keyword_research_get_multi_results page files")
    ap.add_argument("--asin-pages", nargs="+", metavar="ASIN=PAGE.json[,PAGE.json]",
                    help="single-ASIN kr_get_results pages per ASIN, merged here")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--anchor", help="own ASIN, written first; omit for prelaunch runs")
    ap.add_argument("--asins", help="comma-separated ASIN order (default: the pages' productDetails order)")
    ap.add_argument("--marketplace", help="expected marketplace; a mismatch with the pages fails")
    ap.add_argument("--search-id", help="search_id, or comma-separated ids in --asin-pages mode")
    ap.add_argument("--date-from")
    ap.add_argument("--date-to")
    ap.add_argument("--live-info", nargs="+", help="product_live_info_get responses (fill competitor gaps)")
    ap.add_argument("--relevancy", choices=["auto", "native", "computed"], default="auto")
    ap.add_argument("--core-min", type=float, default=0.30)
    ap.add_argument("--pool-min", type=float, default=0.01)
    ap.add_argument("--top-n", type=int, default=50)
    ap.add_argument("--pool-min-top-asins", type=int, default=1)
    ap.add_argument("--allow-one-word", default="", help="comma-separated one-word keywords to keep in Core")
    ap.add_argument("--ngram-max", type=int, default=3)
    ap.add_argument("--ngram-min-freq", type=int, default=3)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out_dir)
    try:
        receipt = run(args)
    except AdapterError as exc:
        receipt = exc.args[1] if len(exc.args) > 1 and isinstance(exc.args[1], dict) else \
            {"ok": False, "provider": "soldscope", "errors": []}
        receipt["ok"] = False
        receipt.setdefault("errors", []).append(str(exc.args[0]))
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "keywords-receipt.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False),
                                                       encoding="utf-8")
        stale = [f for f in OUTPUT_FILES if (out_dir / f).exists()]
        print(f"FAIL: {exc.args[0]}", file=sys.stderr)
        if stale:
            print(f"warning: {out_dir} still holds older outputs {stale}; do not use them", file=sys.stderr)
        return 2
    (out_dir / "keywords-receipt.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False),
                                                   encoding="utf-8")
    brief = {k: receipt[k] for k in ("raw_rows", "meta_total", "unique", "dropped", "merged", "core_rows",
                                     "pool_rows", "roots_rows", "competitor_rows", "marketplace")}
    brief["relevancy"] = receipt["relevancy"]["choice"]
    print(json.dumps(brief))
    for w in receipt["warnings"]:
        print(f"warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
