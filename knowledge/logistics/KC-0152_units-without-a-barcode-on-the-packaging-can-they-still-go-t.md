---
id: KC-0152
title: "Units without a barcode on the packaging: can they still go to FBA, and what does Amazon need on each unit?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon (prep and labeling); Seller Central Help packaging and prep requirements"
surface_verified: false
symptom_keywords: ["ship units without barcode to FBA", "does FBA need UPC or FNSKU on each unit", "chargeback for missing barcode", "unplanned prep fee missing label", "rework packaging for Amazon"]
error_text: []
asked_as: ["The client operations contact asked whether a few units whose packaging carried no barcode could be shipped to FBA as they were, whether a chargeback would follow, and what full list of Amazon packagi"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md", "Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md]
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0152"
---

## Question

The client operations contact asked whether a few units whose packaging carried no barcode could be shipped to FBA as they were, whether a chargeback would follow, and what full list of Amazon packaging rework (labels, poly bags, tamper seals) applied to their SKUs.

## Answer

Every unit you send to FBA needs a scannable barcode Amazon accepts: an FNSKU label, or the manufacturer UPC when the SKU is set to manufacturer barcodes and is eligible for them. Units that need a label and arrive without one cost unplanned prep fees and delay receiving. Keep unbarcoded legacy stock at your own warehouse and fulfil it yourself, and check the category prep rules before assuming a barcode is all Amazon needs.

## Cause

Units shipped to FBA need a scannable barcode Amazon can use: either an Amazon FNSKU label, or the manufacturer barcode (UPC) when the SKU is set to use manufacturer barcodes and is eligible for them. Units that need a label but arrive without one are charged an unplanned prep fee and can delay receipt by up to 48 hours. The thread also states a cut-off date for shipping unbarcoded units; no local first-party capture backs it, so it is left out.

## Fix

1. Check that each unit carries a scannable barcode, and check the SKU's barcode setting: a printed UPC only covers the unit label when the SKU uses manufacturer barcodes and is eligible (eligibility rules change; see the manufacturer-barcode SOP); otherwise apply FNSKU labels.
2. For a shipment already packed with a few unbarcoded units, choose between labeling them before shipping and accepting unplanned prep fees and receiving delays; the thread did not establish which option was finally used.
3. For new production, print the UPC on the packaging and switch the SKU to manufacturer barcodes if eligible, or plan FNSKU labeling.
4. Keep unbarcoded legacy units at your own warehouse and sell them through seller fulfillment instead of sending them to FBA.
5. Check the category's packaging and prep requirements (poly bag, tamper seal and similar) before assuming a barcode is the only requirement.

## Verify

At receiving, the shipment shows no unplanned prep charge and no labeling or unscannable-barcode defect on the Inbound Performance dashboard.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No captured source states that shipping unbarcoded units ends at a fixed date or that a printed UPC alone satisfies the unit-label need; the barcode SOPs cover printing labels, not this ship-as-is decision.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`).
