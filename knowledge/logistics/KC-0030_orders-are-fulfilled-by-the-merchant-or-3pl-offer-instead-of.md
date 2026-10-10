---
id: KC-0030
title: "Orders are fulfilled by the merchant or 3PL offer instead of FBA even though FBA stock exists"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Product detail page featured offer by delivery location; Seller Central > Manage Orders"
surface_verified: false
symptom_keywords: ["orders going to FBM instead of FBA", "3PL fulfilling orders not FBA", "why FBM offer wins over FBA", "featured offer depends on zip code", "FBA and FBM on same ASIN"]
error_text: []
asked_as: ["An ASIN with both an FBA offer and a merchant-fulfilled offer (shipped by a 3PL) received orders that went to the 3PL instead of FBA."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0030"
---

## Question

An ASIN with both an FBA offer and a merchant-fulfilled offer (shipped by a 3PL) received orders that went to the 3PL instead of FBA. The brand asked why.

## Answer

When an ASIN carries both an FBA and a merchant-fulfilled offer, Amazon can feature either one depending on the buyer's location and the delivery promise. If FBA inventory is in transfer or thin in a region, the merchant offer can win there. Check the detail page with ZIP codes set in different regions and look at the FBA transfer quantities before treating it as an error.

## Cause

The featured offer is chosen per customer location, and delivery speed weighs in. For buyers whose ZIP code has no nearby FBA stock (for example while Amazon is transferring inventory between fulfillment centers), the merchant-fulfilled offer can promise faster delivery and wins. The thread's explanation is from operator experience, checked against one ZIP code.

## Fix

1. Open the detail page with a delivery ZIP code set in several regions and note which offer is featured and its delivery promise.
2. In Inventory, check whether FBA units are in transfer between fulfillment centers rather than available.
3. If FBA should win, wait for transfers to finish or raise FBA stock depth; if the 3PL offer should not sell, adjust its quantity or handling time.

## Verify

After transfers finish, detail-page checks across ZIP codes show the FBA offer featured and new orders show Fulfilled by Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The multiple-offers SOP explains setup, not why orders route to the merchant offer by buyer location while FBA stock is in transfer.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`).
