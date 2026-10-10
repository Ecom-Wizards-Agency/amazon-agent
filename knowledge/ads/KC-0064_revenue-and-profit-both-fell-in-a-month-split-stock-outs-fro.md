---
id: KC-0064
title: "Revenue and profit both fell in a month: split stock-outs from bid pushes and use search-query conversion versus market to place budget"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-audit, amazon-reporting, amazon-ppc-weekly-management]
marketplaces: [DE]
marketplace_inferred: false
surface: "Business Reports; Search Query Performance; Amazon Ads campaign manager"
surface_verified: false
symptom_keywords: ["revenue and profit down month", "profit leak analysis ads", "where to put ad budget sqp conversion", "conversion below market keyword", "stock out caused revenue drop"]
error_text: []
asked_as: ["The brand owner reported a month with revenue down and profit down even more while the agency was pushing a key product, and asked for a detailed analysis of the profit leaks and a strategy to grow sa"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0064"
---

## Question

The brand owner reported a month with revenue down and profit down even more while the agency was pushing a key product, and asked for a detailed analysis of the profit leaks and a strategy to grow sales without destroying profitability.

## Answer

When revenue and profit drop together, split the causes before acting: stock-outs explain lost revenue, bid pushes explain lost margin. Compare your conversion rate with the market rate per search term in Search Query Performance; put budget where you convert at or above market, and treat below-market terms as an offer problem, not a PPC problem.

## Cause

Two separate causes: the revenue decline came almost entirely from stock-outs on one product family, while the profit decline came from raised bids on the main keywords to win impression share. On the biggest keywords the product converted at about half the market rate, so holding top positions there with ads alone could not be profitable.

## Fix

1. Split the revenue change by product and check days out of stock per SKU; quantify revenue lost to stock-outs.
2. Separate the profit change from the revenue change: check whether bids were raised on head terms during the period.
3. In Search Query Performance, compare the product's conversion rate with the market conversion rate per main search term.
4. Where conversion is well below market, treat it as an offer problem (price point, pack size, images) and cut bids; ads alone cannot hold those positions profitably.
5. Move budget to terms where conversion is at or above market.
6. Adjust bids accordingly and watch TACOS over the following days.

## Verify

TACOS falls toward target in the following weeks while sales on at-or-above-market terms hold.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the split of a revenue-and-profit drop into stock-outs versus bid pushes and the rule to fund only terms where conversion is at or above market.
- Existing coverage: full (`AdLabs Help/articles/004-bid-optimization-guide.md`, `MAG SOPs/README.md`).
