#!/usr/bin/env python3
"""Internal call-claim verification for Amazon audits.

The output is evidence control, not client copy. A narrative may surface only the
contradictions and recommendation-changing conclusions selected by the operator.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from collections import defaultdict

VERDICTS = {
    "confirmed": "Confirmed",
    "not_supported": "Not supported",
    "mixed": "Mixed or confounded",
    "not_verifiable": "Not verifiable from available data",
}


def _rate(num, den):
    return (float(num) / float(den)) if den else None


def _sum(rows, key):
    return sum(float(row.get(key) or 0) for row in rows)


def _funnel_rates(rows):
    asin_clicks = _sum(rows, "clicks")
    asin_carts = _sum(rows, "cart_adds")
    asin_purchases = _sum(rows, "purchases")
    market_clicks = _sum(rows, "market_clicks")
    market_carts = _sum(rows, "market_cart_adds")
    market_purchases = _sum(rows, "market_purchases")
    asin_click_to_cart = _rate(asin_carts, asin_clicks)
    market_click_to_cart = _rate(market_carts, market_clicks)
    asin_cart_to_purchase = _rate(asin_purchases, asin_carts)
    market_cart_to_purchase = _rate(market_purchases, market_carts)
    return {
        "queries": len(rows),
        "asin_click_to_cart": asin_click_to_cart,
        "market_click_to_cart": market_click_to_cart,
        "asin_cart_to_purchase": asin_cart_to_purchase,
        "market_cart_to_purchase": market_cart_to_purchase,
        "click_to_cart_market_index": _rate(asin_click_to_cart, market_click_to_cart),
        "cart_to_purchase_market_index": _rate(asin_cart_to_purchase, market_cart_to_purchase),
        "asin_average_purchases": asin_purchases,
    }


def evaluate_cart_claim(rows, *, min_impressions=100, min_clicks=5,
                        min_weeks=2, material_gap=0.10,
                        suppression_confounded=False,
                        search_catalog=None):
    """Compare the ASIN funnel with the market on the same queries.

    Rows are per-query averages across the weeks in which each query appeared.
    Summing those averages within the segment preserves the audit's SQP basis.
    """
    eligible = [
        row for row in rows
        if float(row.get("impressions") or 0) >= min_impressions
        and float(row.get("clicks") or 0) >= min_clicks
        and int(row.get("weeks") or 0) >= min_weeks
        and float(row.get("market_clicks") or 0) > 0
        and float(row.get("market_cart_adds") or 0) > 0
    ]
    if not eligible:
        if suppression_confounded:
            return {
                "verdict": VERDICTS["mixed"],
                "reason": "Suppression and missing query coverage prevent a clean market-indexed funnel verdict.",
                "eligible_queries": 0,
                "suppression_confounded": True,
                "search_catalog_performance": search_catalog,
            }
        return {
            "verdict": VERDICTS["not_verifiable"],
            "reason": "No query passed the minimum impression, click, week, and market-denominator gates.",
            "eligible_queries": 0,
        }

    eligible.sort(key=lambda row: (-float(row.get("purchases") or 0),
                                   -float(row.get("clicks") or 0),
                                   str(row.get("query") or "").lower()))
    overall = _funnel_rates(eligible)
    by_segment = defaultdict(list)
    for row in eligible:
        by_segment[row.get("segment") or "Unclassified"].append(row)

    result = dict(overall)
    result.update({
        "eligible_queries": len(eligible),
        "segments": {segment: _funnel_rates(segment_rows)
                     for segment, segment_rows in sorted(by_segment.items())},
        "commercial_query_order": [row.get("query") for row in eligible],
        "material_gap": material_gap,
        "suppression_confounded": bool(suppression_confounded),
        "search_catalog_performance": search_catalog,
    })

    indexes = [x for x in (overall["click_to_cart_market_index"],
                           overall["cart_to_purchase_market_index"]) if x is not None]
    if not indexes:
        result.update(verdict=VERDICTS["not_verifiable"],
                      reason="The eligible queries did not contain usable ASIN and market funnel denominators.")
    elif suppression_confounded:
        result.update(verdict=VERDICTS["mixed"],
                      reason="The selected window includes a suppression event, so the funnel cannot be cleanly attributed.")
    elif min(indexes) <= 1.0 - material_gap:
        result.update(verdict=VERDICTS["confirmed"],
                      reason="A commercially relevant ASIN funnel step materially trails the market on the same queries.")
    elif all(x >= 1.0 for x in indexes):
        result.update(verdict=VERDICTS["not_supported"],
                      reason="The ASIN matches or beats the market at both measured funnel steps.")
    else:
        result.update(verdict=VERDICTS["mixed"],
                      reason="The ASIN is near market or the two funnel steps point in different directions.")
    return result


def parse_search_catalog_performance(path):
    """Read the product-level SCP funnel using tolerant Amazon header aliases."""
    if not path or not Path(path).exists():
        return None
    with open(path, encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return None

    def pick(row, *names):
        normalized = {str(k).strip().lower().replace("–", "-"): v for k, v in row.items()}
        for name in names:
            value = normalized.get(name.lower())
            if value not in (None, ""):
                try:
                    return float(str(value).replace(",", "").replace("%", ""))
                except ValueError:
                    continue
        return 0.0

    totals = dict(impressions=0.0, clicks=0.0, cart_adds=0.0, purchases=0.0)
    for row in rows:
        totals["impressions"] += pick(row, "impressions", "impression count", "impressions: impressions")
        totals["clicks"] += pick(row, "clicks", "click count", "clicks: clicks")
        totals["cart_adds"] += pick(row, "cart adds", "cart add count", "adds to cart", "cart adds: cart adds")
        totals["purchases"] += pick(row, "purchases", "purchase count", "purchases: purchases")
    totals.update(
        click_through_rate=_rate(totals["clicks"], totals["impressions"]),
        click_to_cart_rate=_rate(totals["cart_adds"], totals["clicks"]),
        cart_to_purchase_rate=_rate(totals["purchases"], totals["cart_adds"]),
    )
    return totals


def build_matrix(claims, cart_result=None):
    matrix = []
    for claim in claims:
        row = {
            "id": claim["id"],
            "claim": claim["claim"],
            "verdict": claim.get("verdict", VERDICTS["not_verifiable"]),
            "evidence": claim.get("evidence", []),
            "client_surface": bool(claim.get("client_surface", False)),
        }
        if row["id"] == "cart_abandonment" and cart_result:
            row["verdict"] = cart_result["verdict"]
            row["evidence"] = [cart_result]
        matrix.append(row)
    return matrix


def run(claims_path, cart_path, out_path, search_catalog_path=None, **kwargs):
    claims = json.loads(Path(claims_path).read_text())
    cart = None
    if cart_path and Path(cart_path).exists():
        rows = json.loads(Path(cart_path).read_text())
        cart = evaluate_cart_claim(
            rows,
            search_catalog=parse_search_catalog_performance(search_catalog_path),
            **kwargs,
        )
    payload = {"verdict_labels": list(VERDICTS.values()), "claims": build_matrix(claims, cart)}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True)
    ap.add_argument("--cart-rows")
    ap.add_argument("--search-catalog")
    ap.add_argument("--out", required=True)
    ap.add_argument("--suppression-confounded", action="store_true")
    ap.add_argument("--material-gap", type=float, default=0.10)
    args = ap.parse_args()
    print(run(args.claims, args.cart_rows, args.out, args.search_catalog,
              suppression_confounded=args.suppression_confounded,
              material_gap=args.material_gap))
