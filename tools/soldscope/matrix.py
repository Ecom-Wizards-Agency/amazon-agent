#!/usr/bin/env python3
"""research.json (from keywords.py) -> one self-contained, sortable competitor x keyword page.

  python3 tools/soldscope/matrix.py --research DIR/research.json --out-dir DIR
    [--roots DIR/roots.csv] [--title "Widget Keyword Matrix"] [--views roots,outliers]
    [--min-relev-pct 30] [--outlier-min-sv 2000] [--max-bytes 250000]

Writes DIR/matrix.html and DIR/matrix-receipt.json. Every header metric is computed here
over the full row set before any trimming; the page only sorts, filters and renders.
The data travels as one gzip+base64 JSON payload in place of the template's single
data token and is rendered with textContent, so no text from the data is parsed as HTML.
When the page exceeds --max-bytes the lowest-SV rows are dropped from the largest view
first, the page says so in a banner and the receipt lists every dropped name.
Exit 2 on malformed input or a research.json written before thresholds were recorded.
"""
from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import html as html_lib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from keywords import P1_RANK_MAX, RANK_CAP  # noqa: E402

TEMPLATE = HERE / "matrix_template.html"
TOKEN = "__DATA__"
TITLE_TAG = "<title>Keyword Matrix</title>"
VIEWS = ("matrix", "outliers", "roots")
DOMAINS = {"US": "amazon.com", "CA": "amazon.ca", "MX": "amazon.com.mx", "BR": "amazon.com.br",
           "UK": "amazon.co.uk", "GB": "amazon.co.uk", "DE": "amazon.de", "FR": "amazon.fr",
           "IT": "amazon.it", "ES": "amazon.es", "NL": "amazon.nl", "SE": "amazon.se",
           "PL": "amazon.pl", "BE": "amazon.com.be", "TR": "amazon.com.tr", "IE": "amazon.ie",
           "JP": "amazon.co.jp", "AU": "amazon.com.au", "IN": "amazon.in", "SG": "amazon.sg",
           "AE": "amazon.ae", "SA": "amazon.sa", "EG": "amazon.eg"}
CURRENCY = {"US": "$", "CA": "$", "MX": "$", "AU": "$", "SG": "$", "BR": "R$", "UK": "£", "GB": "£",
            "DE": "€", "FR": "€", "IT": "€", "ES": "€", "NL": "€", "BE": "€", "IE": "€",
            "JP": "¥", "IN": "₹", "SE": "kr ", "PL": "zł ", "TR": "₺", "AE": "AED ", "SA": "SAR ", "EG": "EGP "}
# (min share, key, label): Strength from unrounded Share of Voice; the same buckets strip
# the KWs on P1 % and SV on P1 % cells.
STRENGTH = ((0.8, "vs", "Very Strong"), (0.6, "s", "Strong"), (0.4, "w", "Weak"), (0.2, "vw", "Very Weak"))
RANK_BANDS = ((5, "k1", "Heavy competition"), (21, "k2", "Strong competition"),
              (40, "k3", "Some competition"), (None, "k4", "Little or no competition"))
FOOTER = "Not shown: Seller's Country and TOS ads (no SoldScope source)"
OUTLIER_NOTE = "Outliers come from the keyword pool (at least one compared ASIN in the top {n})"
MEDIAN_TIP = "Median of the compared ASINs with a value"
RANGE_TIP = ("The range runs between the two figures, lower first. The 2nd to 4th highest (2nd to last "
             "with fewer than 4) leave out the leader so one outlier does not set the range.")


class MatrixError(Exception):
    """Input that cannot produce a trustworthy page. Exit code 2."""


# ----------------------------------------------------------------------------- helpers

def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _int_rank(v):
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, int) or v < 1 or v > RANK_CAP:
        raise MatrixError(f"rank {v!r} is not an int 1-{RANK_CAP}")
    return v


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def strength(share):
    for lo, key, label in STRENGTH:
        if share is not None and share >= lo:
            return key, label
    return None, None


def rank_band(r):
    for hi, key, label in RANK_BANDS:
        if hi is None or (r is not None and r <= hi):
            return key, label
    return None, None


def launch_score(sv, h, n):
    """DataDive's round(SV / relevancy * 0.003), half-up, in integers; null below 40%."""
    if not sv or sv <= 0 or h <= 0 or 10 * h < 4 * n:
        return None
    return (6 * sv * n + 1000 * h) // (2000 * h)


def fmt_int(v):
    # Half up, like the page's Math.round; Python's round() would turn a median of 4.5 into 4.
    return "" if v is None else f"{math.floor(v + 0.5):,}"


def fmt_pct(v):
    return "" if v is None else f"{v * 100:.0f}%"


def fmt_money(v, cur, dec=2):
    return "" if v is None else f"{cur}{v:,.{dec}f}"


def fmt_age(days, approx=False):
    if days is None:
        return ""
    months = int(days // 30.44)
    y, m = divmod(months, 12)
    text = f"{y}y {m}m" if y else f"{m}m"
    return text + (" approx." if approx else "")


def median(vals):
    vals = [v for v in vals if _num(v) is not None]
    return statistics.median(vals) if vals else None


def top_range(vals):
    """(median, avg of the 2nd-4th highest) over non-null values; None when < 2 values."""
    vals = sorted((v for v in vals if _num(v) is not None), reverse=True)
    if not vals:
        return None, None
    rest = vals[1:4]
    return statistics.median(vals), (sum(rest) / len(rest) if rest else None)


# ----------------------------------------------------------------------------- reading

def load_research(path: Path) -> dict:
    try:
        r = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise MatrixError(f"cannot read {path}: {exc}") from exc
    if not isinstance(r, dict):
        raise MatrixError(f"{path} is not a JSON object")
    th = r.get("thresholds")
    if not isinstance(th, dict) or not all(isinstance(th.get(k), int) and not isinstance(th.get(k), bool)
                                           for k in ("topN", "p1RankMax")):
        raise MatrixError(f"{path} has no thresholds (written by an older keywords.py); "
                          "re-run tools/soldscope/keywords.py on the saved pages; it is free")
    asins = r.get("asins")
    if not isinstance(asins, list) or not asins or not all(isinstance(a, str) for a in asins) \
            or len(set(asins)) != len(asins):
        raise MatrixError(f"{path}: asins must be a non-empty list of unique ASINs")
    if not isinstance(r.get("keywords"), list) or not isinstance(r.get("competitors"), list):
        raise MatrixError(f"{path}: keywords and competitors must be lists")
    return r


def read_roots(path: Path) -> list[list]:
    try:
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
    except OSError as exc:
        raise MatrixError(f"cannot read {path}: {exc}") from exc
    if not rows or rows[0][1:4] != ["Normalized Root", "Frequency", "Broad Search Volume"]:
        raise MatrixError(f"{path} is not a keywords.py roots.csv")
    out = []
    for i, row in enumerate(rows[1:], 2):
        try:
            out.append([row[1], int(row[2]), int(row[3]), round(float(row[4]), 4)])
        except (IndexError, ValueError) as exc:
            raise MatrixError(f"{path} line {i}: {exc}") from exc
    out.sort(key=lambda t: (-t[2], -t[1], t[0]))
    return out


def keyword_rows(research: dict, order: list[str]) -> list[dict]:
    rows, seen = [], set()
    top_n = research["thresholds"]["topN"]
    for k in research["keywords"]:
        if not isinstance(k, dict) or not isinstance(k.get("keyword"), str):
            raise MatrixError("keywords[] entry without a keyword string")
        kw = k["keyword"]
        if kw in seen:
            raise MatrixError(f"keyword {kw!r} appears twice in research.json")
        seen.add(kw)
        ar, sr = k.get("asinRanks") or {}, k.get("sponsoredAsinRanks") or {}
        if not isinstance(ar, dict) or not isinstance(sr, dict):
            raise MatrixError(f"{kw!r}: asinRanks/sponsoredAsinRanks must be objects")
        try:
            ranks = [_int_rank(ar.get(a)) for a in order]
            spon = [_int_rank(sr.get(a)) for a in order]
        except MatrixError as exc:
            raise MatrixError(f"{kw!r}: {exc}") from None
        sv = _num(k.get("searchVolume"))
        cpc = _num(k.get("cpc")) or None   # 0 means SoldScope has no bid, like keywords.py's CSV
        rows.append({"kw": kw, "sv": int(sv) if sv is not None else None, "ranks": ranks, "spon": spon,
                     "h": sum(1 for x in ranks if x is not None and x <= top_n),
                     "cpc": cpc, "lo": _num(k.get("cpcMin")) if cpc else None,
                     "hi": _num(k.get("cpcMax")) if cpc else None, "stored_rel": k.get("relevancy")})
    return rows


def competitor_order(research: dict) -> list[dict]:
    comps = {c.get("asin"): c for c in research["competitors"] if isinstance(c, dict)}
    out = [dict(comps.get(a) or {}, asin=a) for a in research["asins"]]
    anchor = research.get("anchor")

    def key(c):
        s = _num(c.get("sales"))
        return (0 if c["asin"] == anchor else 1, s is None, -(s or 0), c["asin"])
    return sorted(out, key=key)


# ----------------------------------------------------------------------------- metrics

def cell(t="", s=None, tip=None, **kw):
    c = {"t": t}
    if s:
        c["s"] = s
    if tip:
        c["tip"] = tip
    c.update({k: v for k, v in kw.items() if v is not None})
    return c


def build(research: dict, roots: list | None, args) -> dict:
    th = research["thresholds"]
    top_n, p1 = th["topN"], th["p1RankMax"]
    pct = args.min_relev_pct
    mkt = (research.get("marketplace") or "").upper()
    cur = CURRENCY.get(mkt, "")
    domain = DOMAINS.get(mkt, "amazon.com")
    comps = competitor_order(research)
    order = [c["asin"] for c in comps]
    n = len(order)
    rows = keyword_rows(research, order)

    matrix = [r for r in rows if 100 * r["h"] >= pct * n and (r["sv"] or 0) > 0]
    outliers = [r for r in rows if (r["sv"] or 0) >= args.outlier_min_sv and 100 * r["h"] <= pct * n]
    in_matrix = {r["kw"] for r in matrix}
    for r in rows:
        r["ls"] = launch_score(r["sv"], r["h"], n)
    by_sv = lambda r: (-(r["sv"] or 0), r["kw"])  # noqa: E731
    matrix.sort(key=by_sv)
    outliers.sort(key=by_sv)
    total_sv = sum(r["sv"] for r in matrix)
    m = len(matrix)

    # ---- per-competitor metrics (full matrix set, before trimming) ----------
    for i, c in enumerate(comps):
        p1_rows = [r for r in matrix if r["ranks"][i] is not None and r["ranks"][i] <= p1]
        c["p1Kws"] = len(p1_rows)
        c["p1Pct"] = len(p1_rows) / m if m else 0.0
        c["p1Sv"] = sum(r["sv"] for r in p1_rows)
        c["sov"] = c["p1Sv"] / total_sv if total_sv else 0.0
        c["strength"] = strength(c["sov"])[1]
        c["advKws"] = sum(1 for r in matrix if r["spon"][i] is not None)
        c["advPct"] = c["advKws"] / m if m else 0.0
        o_rows = [r for r in outliers if r["ranks"][i] is not None and r["ranks"][i] <= top_n]
        c["outlierSv"] = sum(r["sv"] for r in o_rows)
        c["outlierKws"] = len(o_rows)

    def strip(v):
        return strength(v)[0]

    header = []

    def row(label, cells, med, tip=None):
        header.append({"label": label, "tip": tip, "cells": cells, "median": med})

    def num_row(label, field, f, small=None, tip=None):
        cells = [cell(f(_num(c.get(field))), small(c) if small else None) for c in comps]
        row(label, cells, cell(f(median(c.get(field) for c in comps)), tip=MEDIAN_TIP), tip)

    brands = [c.get("brand") or "" for c in comps]
    row("Brand", [cell(c.get("brand") or "", tip=c.get("title") or None,
                       tag="Your product" if c["asin"] == research.get("anchor") else None) for c in comps],
        cell(f"{len({b for b in brands if b})} brands"))
    row("ASIN", [cell(c["asin"], href=f"https://www.{domain}/dp/{c['asin']}") for c in comps],
        cell(f"{n} ASINs"))
    counts = Counter(c["strength"] for c in comps)
    chips = [[f"{counts[label]} {label}", key] for _, key, label in reversed(STRENGTH)]
    if counts[None]:
        chips.append([f"{counts[None]} none", ""])
    row("Strength", [cell(c["strength"] or "", badge=strip(c["sov"]),
                          tip=f"Share of Voice {c['sov'] * 100:.1f}%") for c in comps],
        cell("", chips=chips), "From Share of Voice (SV on P1 / total SV): 80% Very Strong, 60% Strong, "
                               "40% Weak, 20% Very Weak")
    num_row("Variations", "variations", fmt_int)
    row("30d Outlier SV", [cell(fmt_int(c["outlierSv"]), f"{c['outlierKws']} kws") for c in comps],
        cell(fmt_int(median(c["outlierSv"] for c in comps)), tip=MEDIAN_TIP),
        f"Search volume of outlier terms (SV >= {args.outlier_min_sv:,}, relevancy <= {pct}%) "
        f"where the ASIN ranks in the top {top_n}")
    # SoldScope reports a listing without reviews as rating 0; show it blank, as DataDive does.
    def rating(c):
        r = _num(c.get("rating"))
        return None if r is None or (r == 0 and not _num(c.get("reviewCount"))) else r
    med_rating = median(rating(c) for c in comps)
    row("Rating", [cell("" if rating(c) is None else f"{rating(c):.1f}",
                        fmt_int(_num(c.get("reviewCount")))) for c in comps],
        cell("" if med_rating is None else f"{med_rating:.1f}",
             fmt_int(median(c.get("reviewCount") for c in comps)), tip=MEDIAN_TIP), "Rating (review count)")
    row("Listing Age", [cell(fmt_age(_num(c.get("listingAgeDays")), bool(c.get("listingAgeApprox"))))
                        for c in comps],
        cell(fmt_age(median(c.get("listingAgeDays") for c in comps)), tip=MEDIAN_TIP))
    num_row("Price", "price", lambda v: fmt_money(v, cur))
    for label, field, f in (("30d Sales", "sales", fmt_int), ("30d Revenue", "revenue",
                                                               lambda v: fmt_money(v, cur, 0))):
        med, avg = top_range(c.get(field) for c in comps)
        if avg is None:
            text, tip = f(med), MEDIAN_TIP
        else:
            lo, hi = sorted((med, avg))
            text, tip = f"{f(lo)} - {f(hi)}", f"Median {f(med)}; average of the 2nd to 4th highest {f(avg)}. {RANGE_TIP}"
        row(label, [cell(f(_num(c.get(field)))) for c in comps], cell(text, tip=tip))
    ff = Counter(c.get("fulfillment") for c in comps if c.get("fulfillment"))
    row("Fulfillment", [cell(c.get("fulfillment") or "") for c in comps],
        cell(", ".join(k for k, _ in sorted(ff.items(), key=lambda t: (-t[1], t[0])))))
    row("KWs on P1", [cell(fmt_int(c["p1Kws"]), fmt_pct(c["p1Pct"]), strip=strip(c["p1Pct"])) for c in comps],
        cell(fmt_int(median(c["p1Kws"] for c in comps)), fmt_pct(median(c["p1Pct"] for c in comps)),
             tip=MEDIAN_TIP), f"Matrix terms where the ASIN ranks organically at {p1} or better")
    row("SV on P1", [cell(fmt_int(c["p1Sv"]), fmt_pct(c["sov"]), strip=strip(c["sov"])) for c in comps],
        cell(fmt_int(median(c["p1Sv"] for c in comps)), fmt_pct(median(c["sov"] for c in comps)),
             tip=MEDIAN_TIP), "Search volume of those terms; the % is the Share of Voice")
    row("Advertised KWs", [cell(fmt_int(c["advKws"]), fmt_pct(c["advPct"])) for c in comps],
        cell(fmt_int(median(c["advKws"] for c in comps)), fmt_pct(median(c["advPct"] for c in comps)),
             tip=MEDIAN_TIP), "Matrix terms with a sponsored rank for the ASIN")
    cats = Counter(c.get("category") for c in comps if c.get("category"))
    row("Category", [cell(c.get("category") or "") for c in comps],
        cell("\n".join(f"{v} {k}" for k, v in sorted(cats.items(), key=lambda t: (-t[1], t[0])))))

    dates = (research.get("statistics") or {}).get("rankDates") or {}
    note = f"{m:,} terms, relevancy >= {pct}%"
    if dates.get("organicMin") and dates.get("organicMax"):
        note += f", ranks scraped {dates['organicMin']} to {dates['organicMax']}"
    sid = research.get("search_id")
    meta = [mkt or "marketplace unknown",
            "search " + (", ".join(map(str, sid)) if isinstance(sid, list) else str(sid)) if sid else None,
            f"{research.get('date_from')} to {research.get('date_to')}"
            if research.get("date_from") or research.get("date_to") else None,
            f"generated from research.json created {research.get('created_at')}"
            if research.get("created_at") else None]

    def kw_row(r, badge=False):
        out = [r["kw"], r["sv"], r["h"], r["cpc"], r["lo"], r["hi"], r["ls"], r["ranks"], r["spon"]]
        if badge:
            out.append(1 if r["kw"] in in_matrix else 0)
        return out

    views = {"matrix": [kw_row(r) for r in matrix]}
    if "outliers" in args.views:
        views["outliers"] = [kw_row(r, True) for r in outliers]
    if "roots" in args.views:
        views["roots"] = roots
    return {
        "payload": {
            "v": 1, "title": args.title, "note": note, "meta": [x for x in meta if x],
            "n": n, "topN": top_n, "p1": p1, "minRelevPct": pct, "outlierMinSv": args.outlier_min_sv,
            "currency": cur, "anchor": research.get("anchor"),
            "comps": [{k: c.get(k) for k in ("asin", "brand", "p1Kws", "p1Pct", "p1Sv", "sov", "strength",
                                              "advKws", "advPct", "outlierSv", "outlierKws", "sales")}
                      for c in comps],
            "header": header, "footer": FOOTER, "outlierNote": OUTLIER_NOTE.format(n=top_n),
            "bands": [[key, label] for _, key, label in RANK_BANDS],
            "strengthBands": [[key, label] for _, key, label in STRENGTH],
        },
        "views": views,
        "outliers_in_matrix": sum(1 for r in outliers if r["kw"] in in_matrix),
        "relev_mismatch": sum(1 for r in rows if isinstance(r["stored_rel"], (int, float))
                              and round(r["h"] / n, 4) != r["stored_rel"]),
    }


# ----------------------------------------------------------------------------- encode

def limit_text(max_bytes):
    return "256 KiB" if max_bytes == 250000 else f"{max_bytes:,}-byte"


def encode(built: dict, keep: dict, max_bytes: int, template: str):
    payload = dict(built["payload"])
    payload["views"] = {}
    for v, rows in built["views"].items():
        k = keep[v]
        unit = "roots by broad search volume" if v == "roots" else "terms by search volume"
        payload["views"][v] = {
            "rows": rows[:k], "eligible": len(rows),
            "banner": None if k == len(rows) else
            f"Showing top {k:,} of {len(rows):,} {unit} to fit the {limit_text(max_bytes)} page limit"}
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, sort_keys=True).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(data, compresslevel=9, mtime=0)).decode("ascii")
    html = template.replace(TOKEN, b64)
    # Title last: the payload is base64 and cannot contain the tag, and a title holding the
    # data token is never touched by the token replacement.
    html = html.replace(TITLE_TAG, f"<title>{html_lib.escape(payload['title'])}</title>")
    return data, html.encode("utf-8")


def fit(built: dict, max_bytes: int, template: str):
    """Largest common per-view cap C (rows kept = min(len, C)) that fits: the largest view
    loses rows first, and each view keeps its highest-SV prefix."""
    lens = {v: len(r) for v, r in built["views"].items()}
    full = dict(lens)
    data, html = encode(built, full, max_bytes, template)
    if not max_bytes or len(html) <= max_bytes:
        return full, data, html
    lo, hi = 0, max(lens.values())        # lo fits (checked below), hi does not
    keep0 = {v: 0 for v in lens}
    d0, h0 = encode(built, keep0, max_bytes, template)
    if len(h0) > max_bytes:
        raise MatrixError(f"the page without any rows is {len(h0):,} bytes, over --max-bytes {max_bytes:,}")
    best = (keep0, d0, h0)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        keep = {v: min(n, mid) for v, n in lens.items()}
        d, h = encode(built, keep, max_bytes, template)
        if len(h) <= max_bytes:
            lo, best = mid, (keep, d, h)
        else:
            hi = mid
    return best


# ----------------------------------------------------------------------------- main

def run(args) -> dict:
    research_path = Path(args.research)
    out_dir = Path(args.out_dir)
    views = [v.strip() for v in (args.views or "").split(",") if v.strip()]
    bad = [v for v in views if v not in ("roots", "outliers")]
    if bad:
        raise MatrixError(f"--views takes roots and/or outliers, got {bad}")
    args.views = views
    if not 0 < args.min_relev_pct <= 100:
        raise MatrixError("--min-relev-pct must be 1-100")
    research = load_research(research_path)
    roots_path = Path(args.roots) if args.roots else research_path.parent / "roots.csv"
    roots = None
    inputs = [{"role": "research", "path": str(research_path), "sha256": sha256_bytes(research_path.read_bytes())}]
    if "roots" in views:
        if not roots_path.exists():
            raise MatrixError(f"--views roots needs {roots_path} (pass --roots)")
        roots = read_roots(roots_path)
        inputs.append({"role": "roots", "path": str(roots_path), "sha256": sha256_bytes(roots_path.read_bytes())})
    try:
        template = TEMPLATE.read_text(encoding="utf-8")
    except OSError as exc:
        raise MatrixError(f"cannot read {TEMPLATE}: {exc}") from exc
    if template.count(TOKEN) != 1:
        raise MatrixError(f"{TEMPLATE} must hold the data token exactly once")
    inputs.append({"role": "template", "path": str(TEMPLATE), "sha256": sha256_bytes(template.encode("utf-8"))})
    # Hosts read the page name from the static <title> tag (the first 8 KB of the file).
    if template.count(TITLE_TAG) != 1:
        raise MatrixError(f"{TEMPLATE} must hold {TITLE_TAG} exactly once")

    built = build(research, roots, args)
    keep, data, html = fit(built, args.max_bytes, template)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "matrix.html").write_bytes(html)
    per_view = {}
    for v, rows in built["views"].items():
        k = keep[v]
        per_view[v] = {"eligible": len(rows), "rendered": k, "dropped": len(rows) - k,
                       "dropped_keywords": [r[0] for r in rows[k:]]}
    th = research["thresholds"]
    return {
        "ok": all(p["rendered"] + p["dropped"] == p["eligible"] for p in per_view.values())
              and (not args.max_bytes or len(html) <= args.max_bytes),
        "inputs": inputs, "n": built["payload"]["n"], "asins": [c["asin"] for c in built["payload"]["comps"]],
        "thresholds": {"topN": th["topN"], "p1RankMax": th["p1RankMax"], "min_relev_pct": args.min_relev_pct,
                       "outlier_min_sv": args.outlier_min_sv, "outlier_max_relev_pct": args.min_relev_pct},
        "views": per_view, "outliers_in_matrix": built["outliers_in_matrix"],
        "stored_relevancy_differs": built["relev_mismatch"],
        "payload_sha256": sha256_bytes(data), "html_bytes": len(html), "max_bytes": args.max_bytes,
        "outputs": ["matrix.html", "matrix-receipt.json"],
    }


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--research", required=True, help="research.json from tools/soldscope/keywords.py")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--roots", help="roots.csv (default: next to research.json); needed for --views roots")
    ap.add_argument("--title", default="Keyword Matrix")
    ap.add_argument("--views", default="", help="extra views: roots,outliers (default: matrix only)")
    ap.add_argument("--min-relev-pct", type=int, default=30,
                    help="matrix relevancy floor and outlier relevancy ceiling, percent (default 30)")
    ap.add_argument("--outlier-min-sv", type=int, default=2000)
    ap.add_argument("--max-bytes", type=int, default=250000, help="page size cap; 0 disables it")
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out_dir)
    try:
        receipt = run(args)
    except MatrixError as exc:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "matrix-receipt.json").write_text(
            json.dumps({"ok": False, "errors": [str(exc)]}, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"FAIL: {exc}", file=sys.stderr)
        if (out_dir / "matrix.html").exists():
            print(f"warning: {out_dir / 'matrix.html'} is from an older run; do not use it", file=sys.stderr)
        return 2
    (out_dir / "matrix-receipt.json").write_text(json.dumps(receipt, indent=1, ensure_ascii=False),
                                                 encoding="utf-8")
    views = ", ".join(f"{v} {p['rendered']}/{p['eligible']}" for v, p in receipt["views"].items())
    dropped = sum(p["dropped"] for p in receipt["views"].values())
    print(f"{'ok' if receipt['ok'] else 'NOT OK'}: {views} rows, {receipt['html_bytes']:,} bytes, "
          f"dropped {dropped}, outliers in matrix {receipt['outliers_in_matrix']}")
    return 0 if receipt["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
