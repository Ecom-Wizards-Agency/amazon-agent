---
id: KC-0169
title: "Product has no UPC printed on the label: what is needed to list it and to ship it to FBA"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Add a Product; Send to Amazon labeling"
surface_verified: false
symptom_keywords: ["UPC not printed on packaging", "is UPC label compulsory for FBA", "need UPC to create listing", "print UPC sticker on box", "FNSKU or UPC for FBA"]
error_text: []
asked_as: ["The client was asked for UPCs to list a new product, but the packaging has no printed UPC yet, and asked whether that is a problem and whether a UPC label is compulsory when shipping to FBA."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md", "Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", "MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md", "MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md"]
supersedes: []
contradicts: [knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md]
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0169"
---

## Question

The client was asked for UPCs to list a new product, but the packaging has no printed UPC yet, and asked whether that is a problem and whether a UPC label is compulsory when shipping to FBA.

## Answer

A UPC is needed as data to create the listing, not as a print on the packaging. Before inventory goes to FBA, every unit needs a scannable barcode: the manufacturer barcode where eligible, an FNSKU label or Transparency. Print and apply stickers yourself, or confirm in Send to Amazon that the paid FBA Label service is still offered in your marketplace before you rely on it. Check the barcode preference before labeling, because sellers without the Brand Representative role may need Amazon barcodes even when a manufacturer barcode exists.

## Cause

Listing creation needs a product ID (UPC/GTIN or an exemption) as data; it does not need the code printed on the pack. FBA receiving needs a scannable barcode on every unit, which can be a manufacturer barcode where eligible, an Amazon FNSKU label or a Transparency code.

## Fix

1. Get the UPC (or a GTIN exemption) for listing creation; the code does not need to be printed on the packaging yet.
2. Before shipping to FBA, make sure every unit carries a scannable barcode: the manufacturer barcode if the SKU is eligible for manufacturer barcodes, otherwise an FNSKU label.
3. If you cannot label the units yourself, check in Send to Amazon whether the FBA Label service (per-item fee) is offered for the SKU and marketplace. The help capture of 12.05.2026 lists it, but KC-0008 records an unverified agency statement that US prep and labeling services ended on 01.01.2026.
4. Check the SKU's barcode preference in Send to Amazon so the label type matches what is on the units.

## Verify

The listing is created with the product ID, and the Send to Amazon labeling step shows the barcode type that matches the labels on the units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Separates the UPC needed as listing data from the scannable barcode needed on units for FBA, with the label options when the pack has no printed UPC.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
