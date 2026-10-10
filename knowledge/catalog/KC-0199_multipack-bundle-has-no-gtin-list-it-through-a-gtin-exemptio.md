---
id: KC-0199
title: "Multipack bundle has no GTIN: list it through a GTIN exemption instead of waiting for barcodes"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Catalog > Add Products > GTIN exemption application"
surface_verified: false
symptom_keywords: ["no GTIN for bundle", "multipack without barcode", "GTIN exemption for 3 pack", "list bundle without UPC"]
error_text: []
asked_as: ["The listing file for new three-pack bundles was ready, but the bundles had no GTINs."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0199"
---

## Question

The listing file for new three-pack bundles was ready, but the bundles had no GTINs. The agency lead asked whether a GTIN exemption could be used instead.

## Answer

When a new multipack or bundle has no GS1 barcode, apply for a GTIN exemption instead of holding the launch for barcodes. The application needs real photos of the product and packaging, and the brand name must match the packaging. The MAG SOP expects a decision within 48 hours, and it can come sooner. Once the exemption is approved, upload the listing without a product ID. A listing created with a GTIN exemption also keeps its product ID editable later.

## Cause

The new bundle SKUs had no GS1 barcode of their own, so they could not be listed with a product ID. A GTIN exemption for the brand and category removes that requirement.

## Fix

1. ["1. Confirm the bundle has no GS1-approved barcode on its packaging; if it has one, list with it instead.", "2. Apply for a GTIN exemption for the product category and product type, with two to nine real-world photos showing all sides of the product and packaging; the brand name entered must match the branding on the product or packaging (the MAG SOP notes a 'This product does not have a brand name' checkbox for unbranded items and bundles, so check which option fits before applying).", "3. Wait for the decision by email or in the case log; the MAG SOP expects it within 48 hours, and in the source case it came back the same day.", "4. Upload the prepared listing file without a product ID, using the exemption.", "5. Check that the bundle listings are live."]

## Verify

The exemption shows as approved and the bundle SKUs appear as active listings without a product ID.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Shows a GTIN exemption used for a new multipack bundle with no barcode, approved within a day, as an alternative to waiting for GS1 codes.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
