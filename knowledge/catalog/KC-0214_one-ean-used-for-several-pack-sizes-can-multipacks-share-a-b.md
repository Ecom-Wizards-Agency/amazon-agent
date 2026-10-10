---
id: KC-0214
title: "One EAN used for several pack sizes: can multipacks share a barcode, or is a bundle the compliant route?"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [DE]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["same EAN multiple pack sizes", "one barcode for several pack sizes", "ship two packs as one multipack", "virtual bundle same ASIN"]
error_text: []
asked_as: ["The client saw one EAN return several pack-size listings in Add a Product and wanted to copy it, shipping several smaller packs as one larger pack to avoid stocking extra pack sizes."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md", "MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md"]
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0214"
---

## Question

The client saw one EAN return several pack-size listings in Add a Product and wanted to copy it, shipping several smaller packs as one larger pack to avoid stocking extra pack sizes.

## Answer

Give every pack size its own GTIN and ASIN; sharing one barcode across variants is not compliant and risks the wrong item being picked. Virtual bundles need at least two different ASINs, so use them for mixed sets, not same-item multipacks, and check that they are available in the marketplace first.

## Cause

Each distinct product, including each pack size, needs its own GTIN; one barcode for several variants means fulfillment scans the same barcode and can ship the wrong item. Virtual bundles need at least two unique ASINs, so they cannot turn several units of one ASIN into a multipack.

## Fix

1. Open the listing said to share the barcode and check which pack size it actually resolves to.
2. Do not reuse one EAN for several pack sizes.
3. For a set of distinct ASINs (for example two colours), create a virtual bundle once virtual bundles are available in that marketplace (operator approval required).
4. For a true multipack of one item, create a separate multipack ASIN with its own GTIN or a GTIN exemption.

## Verify

Each pack size has its own GTIN and ASIN, or the bundle shows under Virtual Bundles with two or more unique ASINs.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Rules out one EAN across pack sizes and explains why virtual bundles cannot replace same-item multipacks.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md`).
