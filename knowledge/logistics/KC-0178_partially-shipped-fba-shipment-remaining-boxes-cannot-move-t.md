---
id: KC-0178
title: "Partially shipped FBA shipment: remaining boxes cannot move to another ship-from location and a new shipment does not replace the old one"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > shipment detail (Amazon-partnered carrier pickup)"
surface_verified: false
symptom_keywords: ["shipment still waiting for remaining boxes", "partial FBA shipment only some boxes sent", "change ship-from location after shipping", "partnered carrier pickup not scheduled", "reschedule pickup for remaining boxes"]
error_text: []
asked_as: ["The seller received an Amazon email about an inbound shipment where only part of the boxes had been handed over."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md", "MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-05
review_by: 2027-10
provenance: "ledger:KC-0178"
---

## Question

The seller received an Amazon email about an inbound shipment where only part of the boxes had been handed over. The warehouse could not send the rest, a second shipment was created from another location, and the seller asked when the pickup for the remaining boxes was scheduled.

## Answer

Treat each FBA shipment as fixed to the ship-from address it was confirmed with. When a warehouse can send only part of a shipment, the remaining boxes still have to leave from that original address, and a new shipment created elsewhere runs alongside the old one rather than replacing it. Once part of a partnered-carrier shipment has been picked up, it can no longer be cancelled for a refund, so schedule the pickup for the rest and confirm with the warehouse that it happened.

## Cause

A confirmed shipment keeps the ship-from address it was created with, and once part of it has been picked up it cannot be cancelled or refunded. Amazon keeps waiting for the missing boxes on the original shipment. A separate shipment created from a different location is an independent shipment and does not close or replace the original one. Why the pickup for one shipment was not scheduled was not established in the thread.

## Fix

1. Open the original shipment in Send to Amazon and compare boxes shipped with boxes planned; note which boxes are still open.
2. Do not expect a new shipment from another location to close the original one; track both shipments separately.
3. Ship the remaining boxes from the original ship-from location, because the ship-from address of a confirmed shipment cannot be changed. If they will not ship from there, remove the unshipped units from the original shipment instead of leaving Amazon waiting for them (operator approval).
4. If the partnered-carrier pickup for the remaining boxes is not scheduled, reschedule it in the shipment. If that fails, contact Seller Support and confirm with the warehouse that the boxes are ready.
5. After pickup, confirm with the warehouse and the carrier tracking that the boxes left, then reconcile receipts once the fulfillment center checks them in.

## Verify

Each open shipment shows every planned box with carrier tracking, and the fulfillment center receipt matches the units sent.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The cited SOPs cover cancelling and the void window but not that a partially shipped shipment keeps its ship-from address and is not replaced by a new shipment from another location.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`).
