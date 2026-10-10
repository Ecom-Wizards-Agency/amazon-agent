---
id: KC-0290
title: "Before pausing ads on out-of-stock FBA products, check whether an FBM offer still makes them buyable"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management, amazon-fba-inventory-planning]
marketplaces: [DE, IT]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory (FBA and FBM offers per ASIN); Amazon Ads Console > product ads"
surface_verified: false
symptom_keywords: ["pause ads on out of stock products", "ads spending on OOS ASINs", "FBA out of stock but FBM offer active", "re-enable ads after restock", "ads stop serving when FBA runs out"]
error_text: []
asked_as: ["A large share of ad spend was going to products with many out-of-stock days, so the team paused campaigns and product ads for ASINs that looked unable to ship."]
synonyms: []
resolution_status: resolved
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
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0290"
---

## Question

A large share of ad spend was going to products with many out-of-stock days, so the team paused campaigns and product ads for ASINs that looked unable to ship. Later the same day a per-SKU check showed several of those ASINs still selling through active FBM offers, and part of the pause had to be reversed.

## Answer

Pausing ads for products that cannot ship saves money, but check every ASIN for an active FBM offer and for who holds the featured offer before pausing, because FBA stock alone does not tell you whether the product is buyable or whether its ads can serve. Pause only ASINs with no buyable offer, tag the pauses so they are easy to revert, and re-enable per product once stock cover is healthy. Where both an FBA and an FBM SKU exist, advertise both so ads keep serving through a stockout.

## Cause

The out-of-stock list was built from FBA stock data only. Several ASINs still had active seller-fulfilled offers, some holding the featured offer, so they were buyable and their ads could still convert; pausing them removed live sales. Other ASINs were truly unbuyable because both offers were closed or the listing was inactive with FBA units stranded.

## Fix

1. Build the candidate pause list from FBA stock and days of cover.
2. For each ASIN, check in Seller Central whether an FBM or Seller Fulfilled Prime offer is active and who holds the featured offer.
3. Pause campaigns and product ads only for ASINs with no buyable offer; keep ads live where an FBM offer sells (operator approval before any pause).
4. Tag or note every pause so it can be filtered and reverted; re-enable per product once its days of cover is healthy again rather than all at once.
5. Flag closed or inactive listings that still hold FBA units to the catalog team for relisting.
6. Where both an FBA and an FBM SKU exist for the ASIN, advertise both so ads keep serving through the FBM offer if FBA stock runs out.

## Verify

Paused campaigns for truly unbuyable ASINs spend nothing, while ASINs with active FBM offers keep impressions and orders; the reverted ads resume serving.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md`
- First-party: `Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source tells operators to check for an active FBM offer before pausing ads on FBA out-of-stock ASINs, or to advertise both SKUs so ads survive a stockout.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `Advertising Help After Login/articles/236-out-of-stock-products-in-stores-GZEH3FV3JSJGR8ZE.md`, `knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md`).
