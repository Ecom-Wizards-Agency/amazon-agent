---
id: KC-0175
title: "Can we put our own packing-list label on FBA cartons when Amazon also requires a box label?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Print box labels"
surface_verified: true
symptom_keywords: ["own label on FBA boxes", "packing list sticker on carton", "do I need to label each box FBA", "box label plus packing list"]
error_text: []
asked_as: ["The client wanted to put its own packing-list label on every carton of an FBA shipment and asked whether that is allowed, since it had done so before."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0175"
---

## Question

The client wanted to put its own packing-list label on every carton of an FBA shipment and asked whether that is allowed, since it had done so before.

## Answer

Your own packing-list label on FBA cartons is fine as long as each carton also carries the box label Amazon generates in Send to Amazon. The Amazon label is the one the fulfillment center scans, so place it where it stays visible and do not cover it with your own sticker.

## Cause

Send to Amazon issues one box label per carton at the Print box labels step; that is the label Amazon relies on at receiving. The thread treats a seller's own packing-list label as extra information that does not replace it. No local source states a rule on additional seller labels.

## Fix

1. Keep the seller's own packing-list label on each carton if import paperwork or internal tracking needs it.
2. In Send to Amazon, at the Print box labels step, print the box labels Amazon generates, one per carton.
3. Attach the Amazon box label to each carton where it stays visible and scannable, and do not cover it with the seller's own label.

## Verify

Every carton carries its own Amazon box label in addition to any seller label, and the carton count matches the labels printed.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Also in: `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms that a seller's own packing-list label may sit on a carton alongside the required Amazon box label, which the Send to Amazon SOP does not address.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`).
