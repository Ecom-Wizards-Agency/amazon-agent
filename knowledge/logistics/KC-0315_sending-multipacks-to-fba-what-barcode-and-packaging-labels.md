---
id: KC-0315
title: "Sending multipacks to FBA: what barcode and packaging labels does each multipack need?"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon; listing barcode type (manufacturer barcode or Amazon barcode)"
surface_verified: false
symptom_keywords: ["multipack FBA barcode", "FNSKU for bundle", "do not separate label", "packaging requirements apparel FBA", "multipack needs different UPC", "manufacturer barcode vs FNSKU"]
error_text: []
asked_as: ["A brand preparing its first FBA shipment of apparel multipacks from an overseas supplier asked what packaging rules apply, whether its usual bag works, and where to get a barcode for multipacks that h"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: [knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0315"
---

## Question

A brand preparing its first FBA shipment of apparel multipacks from an overseas supplier asked what packaging rules apply, whether its usual bag works, and where to get a barcode for multipacks that had none.

## Answer

Treat each multipack as its own FBA product: it needs its own listing and its own scannable barcode, different from the single item inside. When the pack has no UPC, create the FBA child and label it with the Amazon barcode (FNSKU). Pack the items in one bag with brand, manufacturer details and a Do Not Separate label, and hide any other scannable code on the bag.

## Cause

FBA identifies each sellable unit by one scannable barcode. A multipack is its own sellable unit and needs its own listing and its own barcode, different from the single item inside it. A multipack with no UPC of its own needs an FBA child listing that uses an Amazon barcode (FNSKU). What goes wrong at receiving when a pack carries the single's barcode is not established in the thread or in a local capture.

## Fix

1. Create an FBA child listing for each multipack in the variation family and set its barcode type: manufacturer barcode where the pack has its own UPC, Amazon barcode (FNSKU) otherwise.
2. Print FNSKU labels for multipacks without their own UPC. Keep manufacturer barcodes for singles that have them, after setting those listings to use the manufacturer barcode.
3. Pack all items of one multipack in one bag that shows one scannable barcode, the brand name and the manufacturer or importer details. The agency called a Do Not Separate or Sold as Set label helpful; the thread does not cite an Amazon rule that requires it.
4. Cover or turn away any other scannable code on the bag, such as a marketing QR code, so it cannot be scanned in place of the product barcode.
5. Check that garment labels carry the local legal details (agency reading of US clothing rules, not an Amazon page: fiber content, country of origin, manufacturer or RN number, care instructions, size).
6. Collect package dimensions and weight for each multipack listing, then create the Send to Amazon shipment with the ship-from address and shipping mode.

## Verify

Each multipack listing shows its own FNSKU or UPC, the labels match the listing, and the shipment plan accepts every ASIN.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Combines the multipack-specific rule (own barcode distinct from the single, FBA child with FNSKU when no UPC, one bag with Do Not Separate, hide other scannable codes) that the barcode SOPs do not state together.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`).
