---
id: KC-0170
title: "Inbound transportation charge appears after sending FBA stock with partnered carrier labels"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [DE]
marketplace_inferred: true
surface: "Send to Amazon > shipping step; payments transaction view"
surface_verified: false
symptom_keywords: ["inbound transportation fee", "why did Amazon charge shipping to FBA", "partnered carrier charge", "UPS inbound charge"]
error_text: []
asked_as: ["The client asked why Amazon charged an inbound transportation fee."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0170"
---

## Question

The client asked why Amazon charged an inbound transportation fee.

## Answer

An inbound transportation charge is the cost of the Amazon-partnered carrier labels bought in Send to Amazon, not a penalty. Confirm it against the estimate you accepted in the shipping step. You can book your own carrier instead, but it is usually no cheaper and adds manual tracking work.

## Cause

The inbound shipment was sent with a carrier booked through Amazon (UPS in this case), and Amazon charges the shipping cost to the seller account as an inbound transportation charge. The thread does not name the program; the mechanism matches the Amazon Partnered Carrier program, which offers discounted inbound rates that the seller pays.

## Fix

1. Open the shipment in Send to Amazon and confirm the carrier was booked through Amazon (partnered carrier).
2. Compare the charge in the payments transaction view with the shipping cost shown in the shipping step for that shipment.
3. To avoid the charge, book your own carrier outside Seller Central and enter tracking manually; the agency found this not really cheaper and slightly more work.
4. Do not confuse this charge with the inbound placement service fee, which is separate.

## Verify

The inbound transportation charge equals the partnered-carrier estimate accepted for that shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties an unexpected inbound transportation charge on the payments side to partnered-carrier labels bought in Send to Amazon.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
