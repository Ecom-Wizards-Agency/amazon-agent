---
id: KC-0079
title: "FBM late dispatch rate jumps to double digits from a handful of late orders: small order volume inflates the rate"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-logistics]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Shipping Performance (Late Dispatch Rate)"
surface_verified: false
symptom_keywords: ["late dispatch rate increased", "late shipment rate spike low volume", "few late orders high late dispatch rate", "FBM late dispatch fulfillment partner", "LDR above 4%"]
error_text: []
asked_as: ["An agency analyst flagged that the FBM late dispatch rate had risen far above the 4% target, caused by only a few late-dispatched orders on a small order volume."]
synonyms: []
resolution_status: partial
fix_source: client
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md", "MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0079"
---

## Question

An agency analyst flagged that the FBM late dispatch rate had risen far above the 4% target, caused by only a few late-dispatched orders on a small order volume.

## Answer

On low FBM volume, a few late confirmations can push the late dispatch rate far above the 4% target. Check the late orders behind the rate, fix the cause with the fulfiller, and lengthen handling time if they cannot keep pace. Then monitor the rate as the late orders age out of the window.

## Cause

Late dispatch rate is late-confirmed orders divided by all seller-fulfilled orders in the window; with few FBM orders, a handful of late confirmations from the fulfillment partner produces a very high percentage.

## Fix

1. Open Account Health > Shipping Performance and read the late orders behind the rate.
2. Identify why they were confirmed late, for example a fulfillment partner delay or a late shipping confirmation.
3. Raise it with the fulfillment partner so orders are shipped and confirmed by the expected dispatch date.
4. If the partner cannot keep pace, lengthen the handling time or set Order Handling Capacity.
5. Monitor the rate as the late orders roll out of the window; in the source case it fell a few points within days.

## Verify

Late dispatch rate falls back below 4% for the 10- and 30-day windows as late orders age out.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Also in: `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that on low FBM volume a few late confirmations inflate late dispatch rate far above target, and to fix it with the fulfiller and wait for orders to age out.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `AdLabs Help/articles/002-placement-bidding-adjustments.md`).
