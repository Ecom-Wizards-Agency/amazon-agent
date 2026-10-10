---
id: KC-0163
title: "Switching FBA units from Amazon barcode labels to the manufacturer UPC: what changes on the box"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["switch from FNSKU to UPC", "ASIN barcode to manufacturer barcode", "do we still need box labels", "UPC instead of Amazon barcode", "unit label change FBA"]
error_text: []
asked_as: ["The supplier had been labelling each unit with the Amazon (ASIN-based) barcode and each carton with the Amazon box label, and asked whether it would now use the UPC barcode instead and whether the sys"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2024-06
review_by: 2027-10
provenance: "ledger:KC-0163"
---

## Question

The supplier had been labelling each unit with the Amazon (ASIN-based) barcode and each carton with the Amazon box label, and asked whether it would now use the UPC barcode instead and whether the system would recognise it.

## Answer

Switching a SKU to manufacturer barcodes changes the unit label: Amazon then identifies the unit by its UPC, so the Amazon barcode on each unit is no longer needed. Carton box ID labels are still required on every box. The switch applies to future shipments only and not to units already in fulfillment centers, and from 31.03.2026 only brand owners with the Brand Representative role may skip Amazon barcodes. Change the SKU setting first, then brief the prep team, so unit labels and the setting never disagree.

## Cause

The barcode type is a SKU setting in Seller Central. Once the SKU is switched to manufacturer barcode, Amazon identifies the unit by its UPC, so the unit sticker changes; carton (box ID) labels are a separate, shipment-level requirement and still apply.

## Fix

1. Switch the SKU's barcode preference to manufacturer barcode in Seller Central (operator approval required).
2. Replace the Amazon barcode on each unit with the UPC barcode.
3. Keep printing and applying the box ID labels for every carton from the shipment workflow.
4. Tell the prep team which SKUs have switched so unit labels match the setting.

## Verify

The next shipment receives without labeling defects and units are matched to the right SKU.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: States that carton box labels stay required after a SKU switches unit labels to the manufacturer barcode.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/catalog-sop-request-a-bin-check-to-amazon.md`).
