---
id: KC-0311
title: "Ads get few clicks and little spend because the FBM offer is deactivated and FBA stock is mostly out"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit]
marketplaces: [US]
marketplace_inferred: false
surface: "Amazon Ads Console > Sponsored Products delivery; Seller Central inventory"
surface_verified: false
symptom_keywords: ["ads not spending low spend", "sponsored products no impressions out of stock", "ad spend dropped FBA out of stock", "fbm deactivated ads stopped", "low CTR bad reviews ads"]
error_text: []
asked_as: ["The client asked why ad spend stayed low."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md", "Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0311"
---

## Question

The client asked why ad spend stayed low. One answer blamed a very low star rating cutting click-through; a second answer found the FBM offer deactivated and FBA mostly out of stock.

## Answer

When ad spend and clicks stay low, check stock and Featured Offer status for the advertised ASINs before blaming ratings or bids. A product without a buyable offer cannot win ad placements, which looks like a click-through problem from the dashboard. Check rating effects on click-through only once stock is healthy.

## Cause

Most advertised products had no buyable offer: the FBM offer was deactivated and FBA inventory was mostly out of stock. Amazon's ads help says a Sponsored Products ad shows when the product is the Featured Offer and advises keeping advertised products in stock. A very low star rating can also lower click-through, but the thread names stock as the cause. The restock outcome is not shown.

## Fix

1. Check inventory and offer status for every advertised ASIN: FBA available units and whether the FBM offer is active.
2. Check whether each advertised ASIN holds the Featured Offer.
3. Restore stock or reactivate the FBM offer (an operator-approved change) before changing bids or budgets.
4. Only once stock and Featured Offer are healthy, look at rating and click-through as secondary causes.

## Verify

After stock or the FBM offer is restored, confirm that impressions, clicks and spend recover in the Ads Console. The thread does not show how long recovery takes.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md`
- First-party: `Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Stock and Featured Offer eligibility rank ahead of rating effects when diagnosing low ad spend; KC-0009 covers delivery loss with healthy stock, so it does not apply here.
- Existing coverage: partial (`knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md`, `Amazon Ads Help/articles/knowledge-hub/010-python-authorization-amazon-ads-api.md`, `Amazon Ads Help/articles/guides/010-sponsored-display-contextual-targeting-api.md`, `Amazon Ads Help/articles/knowledge-hub/007-amazon-connect-tealium-ads-api.md`, `MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md`).
