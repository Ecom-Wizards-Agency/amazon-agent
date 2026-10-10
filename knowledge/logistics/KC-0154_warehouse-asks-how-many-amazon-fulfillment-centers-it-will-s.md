---
id: KC-0154
title: "Warehouse asks how many Amazon fulfillment centers it will ship to before the FBA shipment exists"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["how many Amazon warehouses will we ship to", "ship from address before shipment", "UPS partnered carrier prepaid labels", "third-party warehouse to FBA domestic transfer"]
error_text: []
asked_as: ["The brand's US warehouse wants to know how many Amazon warehouses it will ship to so it can prepare, and the brand wants the fastest carrier for a domestic transfer to FBA."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0154"
---

## Question

The brand's US warehouse wants to know how many Amazon warehouses it will ship to so it can prepare, and the brand wants the fastest carrier for a domestic transfer to FBA.

## Answer

Get the confirmed ship-from address before anything else, because Amazon only shows how many fulfillment centers a shipment goes to after Send to Amazon creates it from that address, and the count also depends on the placement option chosen there (Amazon-optimized splits or fewer destinations for a placement fee). For a domestic small-parcel transfer, the Amazon-partnered carrier is the simplest option: labels are bought in the workflow and the warehouse hands the boxes to the carrier.

## Cause

Amazon assigns destination fulfillment centers only when the shipment is created in Send to Amazon, and that workflow needs the confirmed ship-from address first. Until the warehouse address is confirmed, no destination count exists.

## Fix

1. Confirm the exact ship-from warehouse address with the brand; if it has several locations, get the one that will ship.
2. Add or select that address as Ship from in Send to Amazon (it cannot be changed after the shipment is confirmed).
3. Build the shipment; Amazon then shows the placement and the number of destination fulfillment centers.
4. For a domestic small-parcel transfer, choose the Amazon-partnered carrier (UPS in the US) and buy the labels in the workflow.
5. Send the prepaid box labels to the warehouse; it applies one per box and hands the boxes to the carrier. Confirming the shipment needs operator approval.

## Verify

The shipment shows the correct ship-from address, the destination fulfillment centers, and partnered-carrier labels for every box.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains why the destination fulfillment center count cannot be given to a warehouse before the shipment is created from a confirmed ship-from address.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`).
