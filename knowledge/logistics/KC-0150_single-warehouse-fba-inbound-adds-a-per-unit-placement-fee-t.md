---
id: KC-0150
title: "Single-warehouse FBA inbound adds a per-unit placement fee that Amazon-optimized splits avoid"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Step 2 Confirm shipping (inbound placement option)"
surface_verified: true
symptom_keywords: ["inbound placement fee", "minimal shipment splits cost", "one warehouse vs optimized splits", "container to one Amazon warehouse fee", "Amazon-optimized splits free"]
error_text: []
asked_as: ["The client planned to send one consolidated sea container to a single warehouse near the arrival port and asked whether to submit it to Amazon and brief the freight forwarder."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md", "Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0150"
---

## Question

The client planned to send one consolidated sea container to a single warehouse near the arrival port and asked whether to submit it to Amazon and brief the freight forwarder.

## Answer

Before sending a full container to one Amazon warehouse, price the placement options in Send to Amazon with real case packs. A single-destination drop carries a per-unit inbound placement fee that can outweigh the freight saving, while Amazon-optimized splits showed no placement fee in the checked case. Compare total cost (placement fee plus delivery to each destination) and re-check the fee screen for the exact mix before confirming.

## Cause

Choosing a single destination or minimal splits in Send to Amazon adds the FBA inbound placement service fee per unit. In the live check with the real case packs, the Amazon-optimized splits option showed no placement fee for that shipment. Local captures name the fee and the split options but do not state that optimized splits are always fee-free.

## Fix

1. Build the shipment in Send to Amazon as a draft with the real case-pack data before quoting freight.
2. At Step 2 Confirm shipping, compare the placement options and their total estimated cost (placement fee plus estimated shipping).
3. Pick Amazon-optimized splits when the forwarder's extra cost to deliver to several destinations is lower than the placement fee it avoids; otherwise compare the single-destination total.
4. Brief the forwarder with box count, volume, weight and the destination list from the draft for a quote.
5. Confirm the shipment only after operator approval, after re-checking that the fee screen still shows the expected placement fee for the final mix.

## Verify

The confirmed shipment shows the Amazon-optimized placement option with no placement fee line, and the forwarder quote covers every destination.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Sources name the placement fee and optimized splits, but none tells a team to price placement options with real case packs before routing a full container to one warehouse.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/README.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
