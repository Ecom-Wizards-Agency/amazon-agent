---
id: KC-0180
title: "FBA offer out of stock and an FBM backup offer takes over: set handling time to what the fulfillment partner can actually meet"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Settings > Shipping Settings (shipping template, handling time)"
surface_verified: false
symptom_keywords: ["FBA out of stock switch to FBM", "FBM handling time too short", "FBM backup offer shipping template", "fulfillment partner fulfilling FBM orders handling time", "merchant fulfilled fallback during stockout"]
error_text: []
asked_as: ["The FBA offer for a product went out of stock and orders moved to a merchant-fulfilled backup offer shipped by the brand's fulfillment partner."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md", "MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md"]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0180"
---

## Question

The FBA offer for a product went out of stock and orders moved to a merchant-fulfilled backup offer shipped by the brand's fulfillment partner. The account manager asked whether handling time and transit time had been adjusted, warning that numbers set too short cause problems later.

## Answer

When an FBA stockout pushes orders to an FBM backup offer, check that offer's handling time against the fulfiller's real processing time and daily cutoff, not the fastest possible promise. Ask the fulfillment partner for its maximum processing time and cutoff, then set the handling time with a buffer. In the source case the team chose two days for a partner that ships same day before a morning cutoff. A longer promise lowers late-shipment risk but can make the offer less competitive, so check the Featured Offer after the change; the thread did not record that outcome.

## Cause

A merchant-fulfilled offer promises delivery from its handling time plus transit time. If the handling time is shorter than the fulfillment partner's real processing time (for example a same-day cutoff in the warehouse's time zone), orders ship late and the late shipment metric suffers; the thread did not record a late-shipment incident, only the risk.

## Fix

1. When an FBA stockout moves sales to the FBM backup offer, check the handling time and shipping template assigned to that offer.
2. Ask the fulfillment partner for its maximum order processing time and its daily order cutoff (time and time zone).
3. Set the handling time to cover that processing time with a buffer; the team chose two days for a fulfillment partner that ships same day before a morning cutoff.
4. Confirm the backup offer still wins the Featured Offer after the change.
5. If volume spikes are expected, also review Order Handling Capacity so extra orders get an extra day automatically.

## Verify

The FBM offer shows the new handling time in its shipping template, orders after the change are confirmed shipped before the ship-by date, and late shipment rate stays under the threshold.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Also in: `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties the FBM backup offer's handling time during an FBA stockout to the fulfillment partner's stated processing time and cutoff plus a buffer day; the SOPs cover late shipment and capacity but not this stockout fallback check.
- Existing coverage: full (`knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`).
