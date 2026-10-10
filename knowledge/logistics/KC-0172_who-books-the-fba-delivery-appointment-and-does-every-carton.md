---
id: KC-0172
title: "Who books the FBA delivery appointment, and does every carton need its own box label?"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon; Amazon Carrier Central"
surface_verified: false
symptom_keywords: ["who schedules FBA delivery appointment", "non-partnered carrier appointment", "Carrier Central appointment", "FBA box label per carton", "one label per box"]
error_text: []
asked_as: ["The client's operations lead asked who books the delivery appointment for an FBA inbound shipment and whether every carton needs its own FBA box label."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0172"
---

## Question

The client's operations lead asked who books the delivery appointment for an FBA inbound shipment and whether every carton needs its own FBA box label.

## Answer

Who books the FBA delivery appointment depends on the carrier. With an Amazon-partnered carrier, you schedule the pickup in Send to Amazon and the carrier handles delivery. With a non-partnered carrier, pass the shipment ID to your 3PL or forwarder so the carrier requests the appointment in Carrier Central, and keep the delivery window in Send to Amazon accurate. Every carton needs its own FBA box label, and Send to Amazon issues one label per box from the packing information you enter.

## Cause

Appointment ownership depends on the carrier. With an Amazon-partnered carrier, the carrier handles delivery to the fulfilment centre and the seller schedules the carrier pickup in the Send to Amazon workflow. With a non-partnered carrier, the seller passes the shipment ID to the 3PL or freight forwarder, the carrier requests the delivery appointment in Amazon Carrier Central, and the seller keeps the estimated delivery window in Send to Amazon accurate. Box labels are generated per carton from the box count and units per box entered in Send to Amazon.

## Fix

1. Amazon-partnered carrier: schedule the carrier pickup in Send to Amazon; the carrier handles the delivery to the fulfilment centre. 2. Non-partnered carrier: give the shipment ID to the 3PL or freight forwarder; the carrier logs in to Amazon Carrier Central and requests the delivery appointment. Enter an accurate estimated delivery window and tracking in Send to Amazon. 3. In Send to Amazon, enter units per box and number of boxes, print the box labels and apply one unique FBA box label to each carton.

## Verify

Shipment shows a scheduled delivery window or appointment, and the number of printed box labels equals the number of cartons.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds who books the delivery appointment for each carrier type in one place; sources cover Carrier Central and box labels separately.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`).
