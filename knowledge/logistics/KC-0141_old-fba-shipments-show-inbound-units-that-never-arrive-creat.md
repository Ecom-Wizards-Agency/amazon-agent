---
id: KC-0141
title: "Old FBA shipments show inbound units that never arrive: created but never shipped"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > Shipments; Manage Inventory inbound column"
surface_verified: true
symptom_keywords: ["inbound units never arrived", "stale FBA shipment", "shipment created but not sent", "inbound inflates stock report", "cancel unsent FBA shipment"]
error_text: []
asked_as: ["An operator taking over logistics found older FBA shipments still counting as inbound with nothing received, and asked the supplier and the client's warehouse teams whether they had ever been sent."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md", "MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0141"
---

## Question

An operator taking over logistics found older FBA shipments still counting as inbound with nothing received, and asked the supplier and the client's warehouse teams whether they had ever been sent. The client also asked why Amazon counted units in stock that had not arrived.

## Answer

Inbound means units in transit, not units received, and Amazon reserves space for them. When an old shipment shows no receipts, confirm with every possible shipper that nothing was sent under those shipment IDs, then cancel it so reports and capacity reflect real stock.

## Cause

The shipments were created in Send to Amazon but never handed to a carrier. Until a shipment is received or cancelled, its units count as inbound, meaning stock expected in transit rather than stock received, which overstates total units in reports. The capacity-limits SOP says FBA capacity limits consider shipments on the way to fulfillment centers. That stale shipments also use up capacity was the operator's explanation; no first-party page captured here confirms it for shipments that were never sent.

## Fix

1. List the open shipments with no receipts and no carrier tracking.
2. Ask every party that could have shipped (supplier, overseas forwarder, domestic warehouse) to confirm in writing whether anything was sent under those shipment IDs, matching the ship-from address and creation date.
3. Do not rely on label PDFs or tracking screenshots alone; match each tracking number to the exact shipment ID.
4. Once every party confirms nothing was sent, cancel the shipments in the shipment workflow (an Amazon write that needs operator approval). Cancel only stale shipments, because frequent create-and-cancel cycles may be flagged.
5. Recheck inbound quantity and capacity after cancellation.

## Verify

Cancelled shipments move to Canceled status in the shipping queue, and inbound quantity in Manage Inventory and inventory reports drops by those units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that unsent shipments keep counting as inbound and reserving space, and requires written confirmation from every possible shipper before cancelling.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
