---
id: KC-0212
title: "Relaunching products under a new brand name: old UPC codes cannot be reused, new ones are needed"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["reuse old UPC new brand", "new brand need new UPC", "UPC tied to brand name", "GTIN for rebrand"]
error_text: []
asked_as: ["The products are being launched under a new brand."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md", "Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0212"
---

## Question

The products are being launched under a new brand. Can the UPC codes from earlier batches be reused for the new shipments, or are new codes needed?

## Answer

When a product relaunches under a new brand name, list it with new GTINs the brand owns or is authorised to use instead of reusing the old brand's codes, even for sold-out batches, because the ASIN's brand is fixed at creation and an old code can match the old brand's catalog record. Keep one mapping of size, pack count and UPC so later bundles and size changes stay separate.

## Cause

An ASIN's brand name is set when the ASIN is created, and sellers may only use GTINs they own or are authorised to use (bought from GS1 or authorised by the GTIN prefix owner). Codes already used for the old brand's products point to catalog records under the old brand. The thread states the rule as agency practice; the GS1 rule that a brand change needs a new GTIN is not in a local capture.

## Fix

1. Confirm the brand name the listings are created under.
2. Have the brand obtain new GS1 UPCs, or codes authorised by the prefix owner, for every SKU and bundle under that brand.
3. Create the listings and SKUs with the new codes and keep a mapping of size, pack count and UPC.

## Verify

Each listing's product ID is a code the brand owns or is authorised to use, and the ASIN shows the new brand name.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- First-party: `Amazon Seller Help/articles/223-register-products-to-your-brand-G6DU75NSM86VXKZC.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the rule that a rebrand needs new UPCs tied to the new brand name, even for sold-out batches.
- Existing coverage: full (`MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`).
