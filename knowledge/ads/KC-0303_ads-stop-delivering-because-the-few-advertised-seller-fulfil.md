---
id: KC-0303
title: "Ads stop delivering because the few advertised seller-fulfilled ASINs show out of stock although the external warehouse has stock"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-troubleshooting, amazon-fba-inventory-planning]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Inventory > Manage All Inventory (seller-fulfilled quantity); Ads console"
surface_verified: false
symptom_keywords: ["ads stopped delivering out of stock", "FBM listing showing out of stock", "sponsored products not serving OOS ASIN", "gateway ASIN out of stock ads paused", "merchant fulfilled quantity zero ads stop"]
error_text: []
asked_as: ["Ads stopped delivering over a weekend because the advertised products showed as out of stock; the account advertised only two or three entry-level ASINs, so those going out of stock stopped most ad de"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/192-create-a-sponsored-products-campaign-GKLSYGFS2YD33FER.md", "Advertising Help After Login/articles/181-create-a-display-campaign-GHG5D7G37KZSD3VQ.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0303"
---

## Question

Ads stopped delivering over a weekend because the advertised products showed as out of stock; the account advertised only two or three entry-level ASINs, so those going out of stock stopped most ad delivery.

## Answer

When ads suddenly stop on seller-fulfilled products, check the listing quantity before touching bids, because sponsored ads do not serve out-of-stock ASINs. Compare it with the stock actually held at the warehouse and correct the quantity. If the ad program relies on only a few gateway ASINs, keep their quantity synced and add a backup ASIN so one stockout does not stop all delivery.

## Cause

Sponsored ads do not serve products that are out of stock or inactive; the first-party campaign pages state that such ASINs do not appear for advertising. The listings showed out of stock while the external warehouse reported enough units, and the agency lead then adjusted the listing quantity. The thread does not say why the quantity reached zero, and it does not name the fulfillment channel. Concentrating spend on two or three gateway ASINs made the whole ad program depend on those listings.

## Fix

1. Confirm in the Ads console that the advertised ASINs are flagged out of stock or ineligible, and check the listing status in Manage All Inventory.
2. Ask the account owner for the current on-hand stock at the external warehouse.
3. Update the listing quantity on the affected SKUs to match available stock (an inventory change; follow the approval gate).
4. Check that the listings return to active and that the ads resume delivery.
5. Optional, not from the thread: set up a routine quantity sync or alert, and consider a backup ASIN for campaigns that depend on one gateway product.

## Verify

The listings show in stock, the advertised products no longer show as ineligible in the Ads console, and impressions resume within the next hours.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/192-create-a-sponsored-products-campaign-GKLSYGFS2YD33FER.md`
- First-party: `Advertising Help After Login/articles/181-create-a-display-campaign-GHG5D7G37KZSD3VQ.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Sources cover out-of-stock ad ineligibility in general; the card adds the seller-fulfilled quantity drift as the cause and the gateway-ASIN concentration risk.
- Existing coverage: full (`Advertising Help After Login/articles/236-out-of-stock-products-in-stores-GZEH3FV3JSJGR8ZE.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md`, `MAG SOPs/README.md`).
