---
id: KC-0025
title: "Can one package carry both the FNSKU and the UPC? No: keep one scannable barcode and print the UPC alone when the offer uses the manufacturer barcode"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Product packaging; offer barcode type (manufacturer barcode or Amazon barcode)"
surface_verified: false
symptom_keywords: ["FNSKU and UPC on same box", "two barcodes on packaging", "same packaging for Shopify and Amazon", "print UPC only FBA", "small box barcode"]
error_text: []
asked_as: ["The client wanted one packaging for its own web store and Amazon and asked whether it could print both the FNSKU and the UPC on a small box."]
synonyms: []
resolution_status: resolved
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
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0025"
---

## Question

The client wanted one packaging for its own web store and Amazon and asked whether it could print both the FNSKU and the UPC on a small box.

## Answer

Put only one scannable barcode on a unit. If the FBA offer uses the manufacturer barcode, print the UPC alone and use the same packaging for every channel. If the offer needs the Amazon barcode, the FNSKU takes the place of the UPC rather than sitting beside it.

## Cause

Amazon does not accept two scannable barcodes on the same unit. When the FBA offer uses the manufacturer barcode, the UPC alone identifies the unit in the fulfillment center.

## Fix

1. Check the offer's barcode type and its manufacturer-barcode eligibility.
2. If the offer uses the manufacturer barcode, print only the UPC on the packaging; it then works for both channels.
3. If the offer needs the Amazon barcode, print the FNSKU instead, not next to the UPC.
4. Make sure the printed code is the right UPC or FNSKU for that offer.

## Verify

Two agency members gave the same answer; no shipment outcome is in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The barcode SOPs list eligible manufacturer barcodes but do not state the one-scannable-barcode rule for shared multichannel packaging.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`).
