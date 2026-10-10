---
id: KC-0186
title: "Units at the 3PL have no barcode before an FBA shipment: print the UPC labels and attach them to each unit"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["units have no barcode", "3PL no UPC on units", "print UPC labels for FBA", "manufacturer barcode missing", "label units before shipment"]
error_text: []
asked_as: ["Box labels for a multi-destination FBA shipment were ready, but the 3PL reported the units carried no barcode or UPC at all."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0186"
---

## Question

Box labels for a multi-destination FBA shipment were ready, but the 3PL reported the units carried no barcode or UPC at all.

## Answer

When a shipment relies on manufacturer barcodes, confirm with the 3PL that every unit already carries a scannable barcode before you hand over box labels. If the units are bare, send the barcode file and have the 3PL label each unit, then scan a sample before shipping. Unlabeled units cause receiving problems and labeling defects at the fulfillment center.

## Cause

The shipment was planned with manufacturer barcodes, which requires every unit to already carry a scannable barcode for its listing; the agency had stated this when it sent the box labels. The units at the 3PL carried none, so they could not go out as planned.

## Fix

1. Confirm which barcode the listing uses (manufacturer UPC or Amazon FNSKU) before the 3PL ships; sellers without a Brand Representative role must use Amazon barcode stickers even when a manufacturer barcode exists.
2. Send the 3PL the barcode artwork file for the exact product.
3. The 3PL prints the barcode labels and attaches one to every unit, on the bottom of the packaging.
4. Spot-check that a printed barcode scans and matches the listing before the boxes go out.
5. Apply the box labels and hand the boxes to the carrier.

## Verify

A sample unit scans to the correct product identifier before shipping, and the shipment is received without labeling defects.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Existing pages cover barcode preference and inbound defects, not the pre-shipment check that a 3PL has actually barcoded every unit.
- Existing coverage: full (`knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
