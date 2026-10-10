---
id: KC-0293
title: "Sponsored Products campaign shows Delivering but gets no impressions because a minimum advertised price above the selling price hides the price"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-troubleshooting, amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Amazon Ads campaign builder; Seller Central Manage Inventory offer edit"
surface_verified: false
symptom_keywords: ["campaign delivering no impressions", "price cannot be found ads", "see price in cart", "minimum advertised price hides price", "ads not serving hidden price"]
error_text: [Delivering, "Price cannot be found", "See price in cart", "Delivered and Sold by Amazon"]
asked_as: ["A new Sponsored Products campaign showed status Delivering but had no impressions or spend, and the price did not display on the product; the team first suspected the wrong advertising profile."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0293"
---

## Question

A new Sponsored Products campaign showed status Delivering but had no impressions or spend, and the price did not display on the product; the team first suspected the wrong advertising profile.

## Answer

"Delivering" means only that a campaign is enabled; if it gets no impressions, check that the advertised product shows a price. A minimum advertised price above the selling price hides the price ("See price in cart"), and the ads side then reports "Price cannot be found" and does not serve. Fix the MAP before rebuilding campaigns under another ads profile, because the price problem follows the offer, not the profile.

## Cause

The SKU had a minimum advertised price (MAP) set higher than its selling price, so Amazon hid the price ("See price in cart") and the Ads side showed "Price cannot be found" for the product, and the campaign got no impressions or spend. "Delivering" only means the campaign configuration is enabled, not that the ad enters auctions. The team first suspected the wrong ads profile, but once the MAP was removed the price showed in both ads profiles, so the profile was not the cause.

## Fix

1. Open the campaign and confirm whether impressions and spend are zero despite status Delivering.
2. Check the advertised product in the campaign builder: does it show a price and in-stock status, or "Price cannot be found"?
3. Open the detail page: "See price in cart" means the price is hidden.
4. In Seller Central, open Manage Inventory and edit the offer; compare the Minimum Advertised Price with the selling price.
5. Remove the MAP, or lower it to the selling price or below, or raise the selling price to at least the MAP (needs operator approval).
6. Recheck the detail page and the ads product view for a visible price before relaunching or moving campaigns.

## Verify

The detail page shows the price, the ads builder shows the price and in-stock status, and the campaign starts getting impressions.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links the MAP hidden-price cause to the Ads symptom of a Delivering campaign with no impressions and "Price cannot be found", which the hidden-price SOP does not mention.
- Existing coverage: full (`MAG SOPs/catalog/merchandising-sop-amazon-list-price-mrsp.md`).
