---
id: KC-0234
title: "Final SKU not known before listing creation: a placeholder SKU stays permanent, the UPC is what ties the product"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central Add a Product / flat file, Seller SKU and Product ID fields"
surface_verified: false
symptom_keywords: ["can I change SKU later", "placeholder SKU new listing", "edit seller SKU after creation", "SKU not final UPC first"]
error_text: []
asked_as: ["A client launching a new product in a few weeks asked whether they can register the UPC now and change the SKU later without causing problems."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md"]
related_sops: ["MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md", "MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0234"
---

## Question

A client launching a new product in a few weeks asked whether they can register the UPC now and change the SKU later without causing problems.

## Answer

Choose the Seller SKU once: it cannot be changed after the listing is created, and changing it later means deleting and relisting the offer. The UPC matters more, because it ties the offer to the catalog and Amazon does not let you edit the product ID of an existing listing either. If the final internal SKU is not known, get the UPC right first, choose a placeholder SKU you can live with, and keep a mapping to the internal SKU.

## Cause

The Seller SKU is the seller's own identifier for the offer, while the UPC (product ID) is what Amazon matches to the catalog. The account manager advised creating the listing with a placeholder SKU. The MAG listing-creation SOP adds that a Seller SKU cannot be changed once the listing exists. Amazon's detail page rules add that the product ID of an existing listing cannot be edited unless it was created with a GTIN exemption, so both values are fixed at creation.

## Fix

1. Secure the correct, unique UPC for the new product first; that is the identifier that matters for the catalog.
2. If the internal SKU is not final, pick a SKU name now that you are willing to keep, because the Seller SKU cannot be edited after the listing is created.
3. If the business later needs a different SKU, plan a delete-and-relist of the offer with the new SKU instead of an edit, with operator approval.
4. Keep a mapping of the Amazon SKU to the internal SKU in the client's own records.

## Verify

Open the listing in Manage All Inventory and confirm the SKU and the product ID shown are the intended ones before inbound shipments or ads reference the SKU.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Also in: `MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The listing-creation SOP notes SKUs cannot change, but nothing addresses choosing a placeholder SKU before launch while securing the UPC first.
- Existing coverage: full (`MAG SOPs/amazon-advertising/advertising-sop-how-to-find-skus-that-are-not-being-advertised.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`).
