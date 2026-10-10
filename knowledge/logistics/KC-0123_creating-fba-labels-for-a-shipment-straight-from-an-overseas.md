---
id: KC-0123
title: "Creating FBA labels for a shipment straight from an overseas factory: Send to Amazon needs ship-from contact name, phone and postal code, and the forwarder gets no fulfillment center phone number"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Ship from address; shipping mode Small Parcel Delivery"
surface_verified: false
symptom_keywords: ["ship from address missing phone", "FBA labels for freight forwarder", "ship directly from factory to Amazon", "fulfillment center phone number", "air and sea split FBA shipment"]
error_text: []
asked_as: ["A brand splitting a large reorder between air and sea freight asked the agency for FBA labels so its freight forwarder could ship directly from an overseas factory to Amazon."]
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
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0123"
---

## Question

A brand splitting a large reorder between air and sea freight asked the agency for FBA labels so its freight forwarder could ship directly from an overseas factory to Amazon. Label creation stalled on missing ship-from details, and the forwarder later asked for the receiving fulfillment center's phone number.

## Answer

When labels must go to a forwarder shipping straight from a factory, collect the full ship-from contact name, phone number and postal code before you open Send to Amazon, because the address is fixed once the shipment is confirmed. Split air and sea quantities into separate shipments. If the forwarder asks for the fulfillment center's phone number, tell them there is none to give. For Small Parcel Delivery the carrier delivers to the address on the box labels without an appointment. The thread did not cover pallet freight.

## Cause

Send to Amazon requires a complete ship-from address, including a full contact name, phone number and postal code, before it creates the shipment and labels; the factory address was supplied without them. The ship-from address cannot be changed after the shipment is confirmed. For Small Parcel Delivery there is no delivery appointment and no fulfillment center contact number to give the forwarder.

## Fix

1. Before creating the shipment, collect the exact ship-from address of the factory or consolidation warehouse plus a full contact name, phone number and postal code.
2. In Send to Amazon, enter it under Ship from another address and check it, because it cannot be changed once the shipment is confirmed (operator approval before confirming).
3. Create separate shipments for the air and sea portions so each gets its own labels.
4. With Small Parcel Delivery, print box labels per carton and send them with the shipment details to the forwarder.
5. If the forwarder asks for a fulfillment center phone number, explain that none is provided; the carrier delivers to the address on the labels.

## Verify

Send to Amazon accepts the ship-from address and produces box labels for each shipment; the forwarder confirms it has labels and destination addresses without needing a phone number.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP says the ship-from address is fixed after confirmation, but not that a full contact name, phone and postal code are required for a factory ship-from or that SPD has no fulfillment center phone for the forwarder.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
