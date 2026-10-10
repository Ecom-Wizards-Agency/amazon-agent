---
id: KC-0319
title: "New listing blocked pending a GS1 certificate: the UPCs' company prefix does not match the prefix certificate"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Add a Product / listing creation with UPC; Seller Support request for GS1 proof"
surface_verified: false
symptom_keywords: ["amazon asking for GS1 certificate", "UPC prefix does not match", "new child listing blocked UPC", "GS1 prefix certificate for listing", "wrong UPC barcode pasted"]
error_text: []
asked_as: ["While listing several new size variants, a few could not be created; when the team contacted Amazon, it asked for the GS1 certificate for those UPCs."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: case
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0319"
---

## Question

While listing several new size variants, a few could not be created; when the team contacted Amazon, it asked for the GS1 certificate for those UPCs. The client could only download a company prefix certificate, and one variant was approved while two others stayed blocked.

## Answer

When Amazon blocks a new listing and asks for a GS1 certificate, send the GS1 company prefix certificate and first check that every submitted UPC starts with that prefix. A mismatched prefix usually means a wrong code was entered, so correct the UPC in the source data before resubmitting. After approval, check for an existing detail page for that UPC before creating another one.

## Cause

Amazon blocks listing submissions whose GTINs the seller does not own or is not authorised to use, and it asked for GS1 proof for the blocked codes. Two of the supplied UPCs were wrong in the source sheet (one was another barcode value pasted in place of the UPC), so they did not start with the company prefix on the certificate and stayed blocked; the code whose prefix matched was approved.

## Fix

1. When a listing is blocked and Amazon asks for GS1 proof, download the GS1 company prefix certificate from the GS1 account; in the thread no per-product certificate could be found there.
2. Compare the prefix on the certificate with the start of every UPC submitted for the listings.
3. For any UPC that does not start with that prefix, check the source sheet: confirm it is the UPC and not another barcode value, and correct it.
4. Send the prefix certificate and the corrected UPCs back through the same Amazon contact that requested them (sending needs operator approval).
5. Create the listings once approved, and check whether a matching detail page already exists before creating a duplicate.

## Verify

Every UPC starts with the certificate's prefix and each listing is created. In the thread the matching code was approved first and the two corrected codes were listed later; the code approved first attached to an existing detail page with a different title.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties a GS1-certificate block to a UPC whose prefix does not match the company prefix certificate, usually a wrongly entered code.
- Existing coverage: full (`MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`, `Amazon Seller Help/articles/134-listings-apis-GD76M4FUWL4NEU32.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`).
