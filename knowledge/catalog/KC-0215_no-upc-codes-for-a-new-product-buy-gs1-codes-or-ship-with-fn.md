---
id: KC-0215
title: "No UPC codes for a new product: buy GS1 codes or ship with FNSKU labels"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Add a Product / Send to Amazon barcode preference"
surface_verified: false
symptom_keywords: ["do I need UPC codes", "how to get UPC for Amazon", "FNSKU instead of UPC", "no barcode for FBA"]
error_text: []
asked_as: ["The client had no UPC codes and asked whether UPCs are only needed for removing copycats, how to create them and whether Amazon issues them."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md", "MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md", "MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0215"
---

## Question

The client had no UPC codes and asked whether UPCs are only needed for removing copycats, how to create them and whether Amazon issues them.

## Answer

Amazon does not issue UPC codes; if you need them, buy GS1 codes registered to the brand. An Amazon-only brand can skip buying UPCs by requesting a GTIN exemption when it lists the product and labelling each unit with Amazon's FNSKU barcode. Either way, every FBA unit needs a scannable barcode before it ships.

## Cause

Amazon does not issue UPCs; product codes are bought from the issuing body. FBA units need a scannable barcode, which can be the manufacturer UPC or Amazon's own FNSKU label.

## Fix

1. Decide whether the brand will sell outside Amazon or wants manufacturer-barcode tracking; if so, buy GS1 product codes registered to the brand (Amazon has taken down listings whose barcode is not GS1-registered to the brand owner).
2. If not, request a GTIN exemption when creating the listing (Catalog > Add products > I'm adding a product not sold on Amazon > I don't have a product ID). The exemption needs the brand name permanently on the product or packaging, real photos of product and packaging, and no GS1 barcode on the product.
3. Set the barcode preference to Amazon barcodes, print FNSKU labels from Send to Amazon and apply one to each unit before shipping.

## Verify

The listing is created without a product ID error and the inbound shipment passes with labeled units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Gives the buy-GS1-UPC versus GTIN-exemption-plus-FNSKU decision for a brand with no barcodes, which local sources cover only in separate SOPs.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`, `AdLabs Help/articles/003-rpc-bidding-formula-acos-goals.md`).
