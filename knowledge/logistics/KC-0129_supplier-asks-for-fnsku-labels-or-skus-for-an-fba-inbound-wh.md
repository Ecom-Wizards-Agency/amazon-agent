---
id: KC-0129
title: "Supplier asks for FNSKU labels or SKUs for an FBA inbound when the products use manufacturer barcodes"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon (box labels); barcode type setting per SKU"
surface_verified: false
symptom_keywords: ["supplier asks for FNSKU labels", "manufacturer barcode no FNSKU needed", "UPC barcode FBA inbound", "what labels does supplier print", "even units per carton FBA"]
error_text: []
asked_as: ["A supplier preparing an FBA inbound asked which labels to put on the boxes, asked for the seller SKUs, and asked for FNSKU labels like last time."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0129"
---

## Question

A supplier preparing an FBA inbound asked which labels to put on the boxes, asked for the seller SKUs, and asked for FNSKU labels like last time. The packing data also had uneven unit counts per carton.

## Answer

When SKUs use manufacturer barcode tracking, the supplier prints the product's UPC (GS1) barcode on each unit and sticks the Send to Amazon box label on each carton; FNSKU labels are unnecessary and only add work. Confirm the barcode setting first. Ask for the same unit count in every carton, adjusting order quantities if needed, so each replenishment uses the same master carton.

## Cause

The SKUs were set to manufacturer barcode (UPC) tracking, so Amazon scans the product's own GS1 barcode and individual FNSKU labels are not needed. The supplier only needs the Send to Amazon box labels for the cartons and the product UPC barcode on each unit. An earlier shipment had used FNSKU labels, which caused the confusion. Uneven unit counts per carton made each shipment's box setup different.

## Fix

1. Check that each SKU in the shipment is set to manufacturer barcode tracking and is eligible before telling the supplier FNSKU labels are not needed; for inventory shipped on or after 31.03.2026 only sellers with the Brand Representative role in Brand Registry may skip Amazon barcodes.
2. Ask the supplier to pack the same number of units in every carton; if quantities do not divide evenly, adjust the order quantity per SKU so all cartons are full.
3. Build the shipment in Send to Amazon with the even carton configuration and the chosen transport mode.
4. Send the supplier the Send to Amazon box labels to stick on each carton.
5. If the supplier needs unit barcodes, send the UPC (GS1) barcode image per product, not FNSKU labels.

## Verify

Cartons arrive with one box label each, units carry the manufacturer UPC barcode, and no 'Labeling required' inbound defect appears.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains what a supplier must label when SKUs use manufacturer barcodes (UPC per unit, box labels per carton, no FNSKU) and why even carton counts help; the matched SOPs cover barcode setup, not the supplier handoff.
- Existing coverage: partial (`knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`).
