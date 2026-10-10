---
id: KC-0221
title: "GS1 license is ready for a new Amazon launch: how many barcodes to create and what product data to collect"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: true
surface: "GS1 member portal; Seller Central listing creation"
surface_verified: false
symptom_keywords: ["GS1 license next steps", "how many barcodes per SKU", "does GS1 product name matter for Amazon", "product data needed to create listings", "GTIN for new listings"]
error_text: []
asked_as: ["The client received its GS1 license and asked what the next steps were, which product information the agency needed, and whether every data point (materials, weight, box size) was strictly necessary."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md", "Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md"]
related_sops: ["MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md"]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0221"
---

## Question

The client received its GS1 license and asked what the next steps were, which product information the agency needed, and whether every data point (materials, weight, box size) was strictly necessary.

## Answer

After a brand buys a GS1 license, create one barcode per sellable SKU, child variations included. The product name inside GS1 is for internal filtering, but the brand on the GS1 record should match the Amazon brand exactly. Collect size, selling points, materials, internal SKU and packaged weight and dimensions for the listings; measured package data sets the FBA size tier and fees, so replace estimates before the first shipment.

## Cause

Not a fault; a setup question. Each sellable SKU needs its own GTIN that the brand owns, and listing creation needs basic product data.

## Fix

1. Create one GS1 barcode per sellable SKU, including every variation child; parent SKUs need none.
2. Name the products in GS1 however is convenient for filtering, but enter the brand name on each GS1 record exactly as it will appear in the Amazon Brand field (the thread says GS1 naming does not affect Amazon; no capture confirms it, and a separate card records a rejection over a brand mismatch).
3. Either the client creates the barcodes or gives the agency a secondary user login to create them.
4. Collect basic product data for each SKU: size, key selling points, working title, all materials, internal SKU, and packaged dimensions and weight.
5. Estimates of packaged weight and dimensions are acceptable for the first draft; replace them with measured values before listing and before the first FBA shipment, because they set the size tier and the fulfilment and storage fees.

## Verify

Each SKU in the listing file has a unique GS1-registered GTIN, and a GS1 ownership lookup returns the brand.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- First-party: `Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md`
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the post-license checklist (one barcode per SKU, GS1 naming is internal only, the product data to collect) that the GTIN rules and listing SOP do not spell out.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `Amazon Seller Help/articles/134-listings-apis-GD76M4FUWL4NEU32.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
