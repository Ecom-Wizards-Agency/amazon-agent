---
id: KC-0031
title: "Send to Amazon shipment lists an auto-generated SKU that the warehouse does not recognise"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon; Manage All Inventory"
surface_verified: false
symptom_keywords: ["auto generated SKU in FBA shipment", "warehouse SKU mismatch on shipment", "wrong merchant SKU on shipment", "recreate FBA shipment with correct SKU", "cancel shipment to avoid charges"]
error_text: []
asked_as: ["After a shipment was created, the client operations lead saw that one product carried an Amazon-generated merchant SKU instead of the agreed SKU naming convention used in the warehouse system."]
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
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0031"
---

## Question

After a shipment was created, the client operations lead saw that one product carried an Amazon-generated merchant SKU instead of the agreed SKU naming convention used in the warehouse system.

## Answer

Check that the merchant SKUs in a new shipment match your warehouse SKU list before you release shipment details, because a listing created without your SKU gets an auto-generated one. If they differ, create the correct SKU, rebuild the shipment, and cancel the old one only after the warehouse confirms it will not ship it. Packing details cannot be changed after confirmation, so a rebuild is the clean fix.

## Cause

The product came from a listing created without the agreed seller SKU, so Amazon assigned a random merchant SKU to the barcode; the shipment was built on that SKU.

## Fix

1. Before sending shipment details to the warehouse, compare every merchant SKU in the shipment with the warehouse SKU list, matched by barcode.
2. If a SKU does not match, create an offer with the agreed SKU (for example with a fulfillment-channel suffix) on the same ASIN.
3. Recreate the shipment in Send to Amazon using the correct SKU and send the new shipment details to the warehouse.
4. Have the warehouse confirm it dropped the old request, then cancel the old shipment in Send to Amazon so it does not incur charges (operator approval).

## Verify

The new shipment shows the agreed SKUs, the old shipment status is cancelled, and the warehouse confirms it is shipping against the new shipment ID.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a pre-release check that shipment merchant SKUs match the warehouse SKU list, since listings created without a seller SKU get an auto-generated one, and the cancel-after-warehouse-confirms order of the rebuild.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
