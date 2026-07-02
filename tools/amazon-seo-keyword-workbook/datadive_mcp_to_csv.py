#!/usr/bin/env python3
"""Generate builder-compatible DataDive CSVs from DataDive MCP JSON payloads.

Purpose: replace the finicky DataDive *UI browser downloads* for the inputs the
DataDive MCP can supply, so a run only needs ONE DataDive download.

MCP-covered (this script writes them):
  - roots_csv         <- get_niche_roots      (normalizedRoots table)
  - master_csv (Core) <- get_niche_keywords   (the visible/tracked set == the 30% view)
  - competitors_csv   <- get_niche_competitors (row-per-competitor shape)

NOT MCP-covered (still a UI download — do NOT try to synthesize):
  - expanded_mkl_csv (1% MKL) — the MCP returns only the ~visible/tracked set, not
    the 1% expansion tail (the extra rows up to the 500 cap). Download it.

Usage (Claude calls the MCP tools, saves each raw JSON response to a file, then):
  python datadive_mcp_to_csv.py --anchor B0XXXXXXXX \
    --roots-json roots.json --keywords-json keywords.json --competitors-json comps.json \
    --out-roots ~/Downloads/niche-<ID>-niche-analysis-roots.csv \
    --out-core  "~/Downloads/master list-niche-<ID>-keywords.csv" \
    --out-competitors ~/Downloads/niche-<ID>-competitors.csv

Column schemas are matched to what build_keyword_workbook.py CONSUMES (it detects
columns by header name, not position):
  roots:  "","Normalized Root","Frequency","Broad Search Volume",""(=ratio → Root Score)
  core:   "","Search Terms","SV","Relev.","Sugg. bid & range",<ASIN cols…>
          ("Sugg. bid & range" is intentionally blank — the builder never reads it;
           it only matters for PPC builds, which are out of scope for SEO runs.)
  comps:  asin,brand,seller country,variations,rating,review count,price,30d sales,
          30d revenue,fulfillment,category  (row-per-competitor; builder handles this
          shape via competitor_map's non-transposed branch — needs an 'asin' column).

Guardrail: the caller MUST cross-check that len(keywords) == get_niche_competitors
numVisibleKeywords before trusting the Core file (they matched 257==257 on a
validation run). If they diverge, fall back to the UI Core export.
"""
import argparse
import csv
import json
import os


def load(path: str) -> dict:
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: str, rows: list[list]) -> int:
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerows(rows)
    return len(rows) - 1  # data rows (excl. header)


def gen_roots(roots: dict) -> list[list]:
    items = sorted(
        roots.get("normalizedRoots", []),
        key=lambda x: -(x.get("broadSearchVolume") or 0),
    )
    out = [["", "Normalized Root", "Frequency", "Broad Search Volume", ""]]
    for it in items:
        out.append([
            "", it.get("root", ""), it.get("frequency", ""),
            it.get("broadSearchVolume", ""), it.get("broadSearchVolumeRatio", ""),
        ])
    return out


def _rel_sort_key(r: dict):
    v = r.get("relevancy")
    if isinstance(v, (int, float)):
        return (0, -v)
    return (1, 0)  # "Outlier"/missing sorts after numeric relevancy


def gen_core(kw: dict, asin_order: list[str]) -> list[list]:
    items = sorted(
        kw.get("keywords", []),
        key=lambda r: (_rel_sort_key(r), -(r.get("searchVolume") or 0)),
    )
    out = [["", "Search Terms", "SV", "Relev.", "Sugg. bid & range"] + list(asin_order)]
    for r in items:
        row = ["", r.get("keyword", ""), r.get("searchVolume", ""), r.get("relevancy", ""), ""]
        ranks = r.get("asinRanks", {}) or {}
        for a in asin_order:
            v = ranks.get(a)
            row.append("" if v is None else v)
        out.append(row)
    return out


def gen_comps(comp: dict) -> list[list]:
    out = [[
        "asin", "brand", "seller country", "variations", "rating", "review count",
        "price", "30d sales", "30d revenue", "fulfillment", "category",
    ]]
    for c in comp.get("competitors", []):
        out.append([
            c.get("asin", ""), c.get("brand", ""), c.get("sellerCountry", ""),
            c.get("numberOfVariations", ""), c.get("rating", ""), c.get("reviewCount", ""),
            c.get("price", ""), c.get("sales", ""), c.get("revenue", ""),
            c.get("fulfillment", ""), c.get("category", ""),
        ])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", required=True, help="Anchor ASIN (goes first in the Core ASIN columns).")
    ap.add_argument("--roots-json")
    ap.add_argument("--keywords-json")
    ap.add_argument("--competitors-json", required=True, help="Needed for the ASIN column order.")
    ap.add_argument("--out-roots")
    ap.add_argument("--out-core")
    ap.add_argument("--out-competitors")
    a = ap.parse_args()

    comp = load(a.competitors_json)
    asin_order = [c["asin"] for c in comp.get("competitors", []) if c.get("asin")]
    if a.anchor not in asin_order:
        asin_order = [a.anchor] + asin_order
    elif asin_order[0] != a.anchor:  # ensure anchor leads
        asin_order.remove(a.anchor)
        asin_order = [a.anchor] + asin_order

    if a.out_roots and a.roots_json:
        n = write_csv(a.out_roots, gen_roots(load(a.roots_json)))
        print(f"roots       -> {a.out_roots}  ({n} rows)")
    if a.out_core and a.keywords_json:
        n = write_csv(a.out_core, gen_core(load(a.keywords_json), asin_order))
        print(f"core 30%    -> {a.out_core}  ({n} rows, {len(asin_order)} ASIN cols)")
    if a.out_competitors:
        n = write_csv(a.out_competitors, gen_comps(comp))
        print(f"competitors -> {a.out_competitors}  ({n} rows)")


if __name__ == "__main__":
    main()
