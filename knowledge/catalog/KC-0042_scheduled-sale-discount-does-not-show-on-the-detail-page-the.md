---
id: KC-0042
title: "Scheduled sale discount does not show on the detail page; the listing's minimum price sits above the deal price, or Amazon wants a deeper discount"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory (Your Minimum Price column); Advertising > Deals / Price discounts"
surface_verified: false
symptom_keywords: ["deal price not showing", "discount not live on listing", "sale price shows full price", "minimum price blocks deal", "Amazon suggests lower deal price"]
error_text: []
asked_as: ["During a seasonal sale several ASINs still showed the full price on the storefront instead of the planned discounted price."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: email
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md", "Amazon Seller Help/articles/072-amazon-deals-G202043110.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0042"
---

## Question

During a seasonal sale several ASINs still showed the full price on the storefront instead of the planned discounted price.

## Answer

When a planned sale price does not appear, first confirm the discount exists for that ASIN, then check the offer's minimum price: a minimum above the deal price suppresses the offer. Keep minimum price below sale price and sale price below regular price. If Amazon only accepts the deal at a deeper discount, the brand owner decides whether to go that low.

## Cause

Two causes in one sweep. Some ASINs had no discount set up at all. For one ASIN the minimum price set on the offer was higher than the new deal price, so the offer was suppressed until the minimum was lowered; for another, Amazon would accept the deal only at a lower price than planned (its suggested deal price).

## Fix

1. Compare the planned discount sheet against the live detail pages and list every ASIN still at full price.
2. Check that a discount or deal actually exists for each listed ASIN; create the missing ones.
3. Show the 'Your Minimum Price' column in Manage All Inventory and lower the minimum price below the deal or sale price so that minimum price < sale price < regular price.
4. If Amazon asks for a lower deal price than planned, take the price decision to the brand owner before accepting (operator approval required for any price change).
5. Recheck the detail page after the update and watch for the listing to come back.

## Verify

The detail page shows the discounted price with the strike-through, and the offer is active in Manage All Inventory.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- First-party: `Amazon Seller Help/articles/072-amazon-deals-G202043110.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the sale-sweep check order (discount exists, then minimum price, then Amazon's deeper-discount request) to the hidden-price SOP, which covers the minimum-price rule alone.
- Existing coverage: full (`MAG SOPs/catalog/merchandising-sop-amazon-list-price-mrsp.md`, `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`).
