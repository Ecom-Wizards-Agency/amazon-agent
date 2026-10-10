---
id: KC-0220
title: "New listing with own UPCs keeps failing and the brand name may not exactly match the registered brand"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Add a Product; GS1 US Data Hub > Product"
surface_verified: false
symptom_keywords: ["brand name does not match UPC", "GS1 brand name capitalization", "listing creation rejected brand mismatch", "company name vs brand name GS1", "where to find brand name in GS1"]
error_text: []
asked_as: ["Listing creation with the brand's own UPCs kept failing, and the team asked what exact brand name is tied to the UPCs in GS1."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md", "Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md"]
related_sops: ["MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md"]
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0220"
---

## Question

Listing creation with the brand's own UPCs kept failing, and the team asked what exact brand name is tied to the UPCs in GS1. The client first answered with the company name.

## Answer

When a listing with your own UPCs keeps failing, check the brand name character for character, capitalization included. Amazon requires the listing brand to match the Brand Registry brand name exactly, and the GS1 product record shows the brand tied to the UPCs; the GS1 company name is the owning entity, not the brand. If the failure persists, capture the exact error text before trying anything else.

## Cause

Suspected, not confirmed: the brand name entered on the listing differed in capitalization from the registered brand. Amazon's product registration page says the brand name is case-sensitive and must exactly match the brand name in Brand Registry, and that the product ID must be a GS1-registered UPC. The thread read the brand name from GS1 Data Hub; no local first-party page says Amazon matches the listing brand against the GS1 brand record. The GS1 company name is the owning entity, not the brand name.

## Fix

1. Sign in to GS1 US Data Hub, open Product, click any product or barcode and read the Brand Name field (not the company name).
2. Compare it with the brand name in Brand Registry and on the listing, character for character, including capitalization and spacing.
3. Enter the exact registered brand name on the listing; the ASIN's brand name can only be set when the ASIN is created.
4. Resubmit the listing (operator approval) and capture the exact error text if it fails again.

## Verify

The listing submission is accepted without a brand or GTIN mismatch.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- First-party: `Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md`
- Also in: `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party pages require GS1-owned GTINs but none says the listing brand must match the GS1 Data Hub brand name exactly, or where to read it.
- Existing coverage: partial (`MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`, `Amazon Seller Help/articles/236-create-a-brand-name-GTTTDEQTT9GFW9X2.md`, `Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md`, `MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md`, `Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md`).
