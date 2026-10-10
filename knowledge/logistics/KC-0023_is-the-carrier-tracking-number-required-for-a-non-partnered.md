---
id: KC-0023
title: "Is the carrier tracking number required for a non-partnered inbound shipment"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Tracking details"
surface_verified: false
symptom_keywords: ["upload tracking number FBA shipment", "is tracking needed for inbound", "non-partnered carrier tracking ID", "air freight tracking Send to Amazon"]
error_text: []
asked_as: ["A brand asked whether the tracking number for an air shipment to the Amazon warehouse had to be uploaded, after its forwarder said it was not needed."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0023"
---

## Question

A brand asked whether the tracking number for an air shipment to the Amazon warehouse had to be uploaded, after its forwarder said it was not needed.

## Answer

Add carrier tracking to non-partnered inbound shipments even when the forwarder says it is optional. Amazon uses the tracking ID to plan receiving and to mark the shipment delivered, and accurate tracking speeds up processing.

## Cause

Not a fault; the question is whether tracking details are mandatory for shipments that do not use an Amazon-partnered carrier.

## Fix

1. Get the carrier tracking number from the forwarder.
2. Enter it in the Tracking details step of the shipment in Send to Amazon.

## Verify

The shipment shows the tracking ID in Send to Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Answers directly that tracking for non-partnered inbound shipments is optional in practice but should be entered because Amazon uses it to plan receiving and mark delivery.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`).
