---
id: KC-0181
title: "Can the FBA ship-from address change after the first shipments: yes, it is set per shipment"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Ship from"
surface_verified: false
symptom_keywords: ["change ship from address FBA", "ship from different warehouse later", "start FBA from overseas warehouse then switch", "temporary 3PL ship from address", "ship from another address Send to Amazon"]
error_text: []
asked_as: ["A new seller planned to send the first FBA stock from a warehouse abroad and, a few months later, from a warehouse in the destination country, and asked whether it was acceptable to give the first war"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0181"
---

## Question

A new seller planned to send the first FBA stock from a warehouse abroad and, a few months later, from a warehouse in the destination country, and asked whether it was acceptable to give the first warehouse as the ship-from address for now.

## Answer

You can start FBA shipments from one warehouse and switch to another later. Send to Amazon asks for the ship-from address on each shipment, and Ship from another address adds a new one. The address cannot be changed once a shipment is confirmed, so enter the address the cartons actually leave from before confirming each shipment.

## Cause

Not a fault: the ship-from address is chosen on each Send to Amazon workflow, so a later change does not affect earlier shipments.

## Fix

1. Enter the current warehouse as the Ship from address when creating the shipment.
2. When stock moves to the new warehouse, choose Ship from another address in Send to Amazon and add the new address.
3. Check the ship-from address before confirming the shipment; it cannot be changed after confirmation.
4. Shipping from another country brings import and customs requirements that this answer does not cover.

## Verify

Each shipment shows the warehouse it actually leaves from as its ship-from address.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms that starting FBA from one warehouse and switching ship-from address later is fine because the address is set per shipment.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
