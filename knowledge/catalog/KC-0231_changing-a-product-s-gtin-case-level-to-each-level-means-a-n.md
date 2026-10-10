---
id: KC-0231
title: "Changing a product's GTIN (case-level to each-level) means a new listing, not an edit, and the agency restarted the supplement verification"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Add a product; GS1 GTIN portal"
surface_verified: false
symptom_keywords: ["change GTIN on existing listing", "case level GTIN vs each level GTIN", "new barcode same product new ASIN", "product ID cannot be edited", "new GTIN supplement verification again"]
error_text: []
asked_as: ["The client found its pack formats had been given case-level GTINs in GS1, reassigned each-level GTINs, and expected to keep the same listings and supplement verification, changing only images and desc"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: call
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0231"
---

## Question

The client found its pack formats had been given case-level GTINs in GS1, reassigned each-level GTINs, and expected to keep the same listings and supplement verification, changing only images and description at the format transition.

## Answer

Assign each-level GTINs to the sellable unit before listing, because Amazon does not let you change a listing's product ID afterwards unless the listing was created with a GTIN exemption. A new GTIN means a new product listing. For supplements the agency also restarted the testing-body verification for the new product; confirm that with the testing body.

## Cause

A listing's product ID cannot be edited once the listing exists (unless it was created with a GTIN exemption), so a new GTIN requires a new product listing. The agency said the supplement verification also has to start again for the new products; the reason was discussed on a call and not stated in the thread.

## Fix

1. Assign each-level GTINs to the sellable unit in GS1 before creating listings.
2. If the GTIN of an already-listed product changes, create a new product with the new GTIN; do not try to edit the product ID (listings created with a GTIN exemption are the exception).
3. For supplements, plan to restart the testing-body verification for the new product; the agency said so, but the reason was given on a call and is not in the thread, so confirm with the testing body.

## Verify

The new product shows the each-level GTIN as its product ID.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The local page says product IDs cannot be edited, but nothing links a case-level to each-level GTIN change to a new listing, a restarted supplement verification and carton labels without a case GTIN.
- Existing coverage: partial (`Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`, `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
