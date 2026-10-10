---
id: KC-0116
title: "Existing FBA SKU stuck on Amazon barcode cannot switch to manufacturer barcode, so every unit needs an FNSKU sticker"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Settings > Fulfillment by Amazon > Barcode preference; SKU-level barcode type; Send to Amazon"
surface_verified: false
symptom_keywords: ["switch SKU to manufacturer barcode", "barcode preference manufacturer", "units need FNSKU label", "new SKU same ASIN barcode", "who labels units seller"]
error_text: []
asked_as: ["A brand shipping to FBA from a third-party warehouse found that an existing SKU was set to use Amazon barcodes labelled by the seller, so units without a printed FNSKU would need individual stickers."]
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
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0116"
---

## Question

A brand shipping to FBA from a third-party warehouse found that an existing SKU was set to use Amazon barcodes labelled by the seller, so units without a printed FNSKU would need individual stickers. The packaging now carried a UPC, and the team wanted to ship without per-unit labelling.

## Answer

A SKU that holds Amazon-barcoded inventory or open shipments usually cannot switch to the manufacturer barcode. Create a new SKU on the same ASIN with the manufacturer barcode and ship the UPC-printed units under it. Units without a matching UPC still need an FNSKU sticker on every unit. Manufacturer-barcode eligibility changed for inventory shipped from 31.03.2026 (brand representatives versus resellers), so check the current rule before you plan labelling.

## Cause

The SKU had been created with the Amazon barcode and set for seller labelling, and the team could not convert it to the manufacturer barcode. The MAG SOP gives the likely reasons: barcode type cannot be switched for inventory already in fulfillment centers, and listings with open shipments may need a new SKU. The thread did not establish which restriction applied, or whether an SKU without such inventory could have converted through Convert eligible offers or the Send to Amazon link.

## Fix

1. ["1. Try converting first: Manufacturer barcode: Convert eligible offers, or the Save using manufacturer barcode link in Step 1 of Send to Amazon. If the link is missing, the product is likely ineligible.", "2. If the SKU cannot convert (Amazon-barcoded inventory in fulfillment centers, open shipments), check Settings > Fulfillment by Amazon > Barcode preference (needs the FBA settings permission), then create a new SKU on the same ASIN and choose Manufacturer barcode on the List as FBA page. Reviews and the detail page stay on the ASIN.", "3. Ship units whose packaging carries the matching UPC under the new SKU without FNSKU stickers.", "4. Units of the old packaging without a UPC still need an Amazon unit label (FNSKU) on every unit and ship under the old SKU.", "5. Confirm with the warehouse that its system has synced the new SKU before it raises the outbound order."]

## Verify

In the shipment workflow the new SKU shows the manufacturer barcode and no unit labelling requirement; the warehouse system lists the new SKU.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP covers converting eligible offers, but not that the account barcode preference only applies to SKUs created afterwards, nor the split between barcoded new packaging and unlabelled old packaging under two SKUs on one ASIN.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
