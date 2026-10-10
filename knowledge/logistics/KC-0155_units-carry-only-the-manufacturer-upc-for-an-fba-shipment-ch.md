---
id: KC-0155
title: "Units carry only the manufacturer UPC for an FBA shipment: check manufacturer-barcode eligibility for every SKU before creating the shipment"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["ship with UPC instead of FNSKU", "switch to manufacturer barcode", "boxes have UPC barcode FBA", "barcode preference before shipment"]
error_text: []
asked_as: ["A replenishment shipment is approved and the warehouse will label the boxes with UPC barcodes, not Amazon barcodes."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md"]
supersedes: []
contradicts: []
observed: 2024-07
review_by: 2027-10
provenance: "ledger:KC-0155"
---

## Question

A replenishment shipment is approved and the warehouse will label the boxes with UPC barcodes, not Amazon barcodes. Is anything needed on the Amazon side before creating the shipment?

## Answer

Before sending units that carry only the manufacturer UPC, confirm every SKU in the shipment is set to manufacturer barcode and is eligible. From 31.03.2026 this is open only to brand owners with the Brand Representative role in Brand Registry, and a SKU with Amazon-barcoded stock already in fulfillment centers cannot switch, so it needs a new SKU or FNSKU labels. Otherwise label the units with FNSKUs, or expect unplanned labelling fees and receiving delays.

## Cause

The SKUs were still set to Amazon barcodes in Seller Central. Units carrying only a manufacturer barcode are tracked under that barcode only when the SKU's barcode preference is manufacturer barcode and the SKU is eligible. A SKU with Amazon-barcoded inventory already in fulfillment centers cannot switch; it needs a new SKU set to manufacturer barcode, or the units need FNSKU labels. For inventory shipped on or after 31.03.2026, only brand owners with the Brand Representative role in Brand Registry can use manufacturer barcodes; resellers must apply Amazon barcodes.

## Fix

1. Confirm whether the units carry only the manufacturer barcode (UPC/EAN) or Amazon FNSKU labels.
2. Confirm the seller holds the Brand Representative role in Brand Registry for the brand; without it, label every unit with its FNSKU.
3. For each SKU, check eligibility under Manufacturer barcode: Convert eligible offers. A SKU with Amazon-barcoded stock already in fulfillment centers cannot switch and needs a new SKU set to manufacturer barcode, or FNSKU labels on the units.
4. Only then create the shipment in Send to Amazon (needs operator approval).

## Verify

Every SKU in the Send to Amazon shipment shows manufacturer barcode as its barcode type, or the units of any SKU that could not switch carry FNSKU labels.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the pre-shipment check that every SKU must be switched to manufacturer barcode before boxes ship with UPC-only labels.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
