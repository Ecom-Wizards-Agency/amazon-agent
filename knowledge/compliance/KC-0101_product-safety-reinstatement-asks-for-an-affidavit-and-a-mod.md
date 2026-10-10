---
id: KC-0101
title: "Product safety reinstatement asks for an affidavit and a model number update when the test report does not match the listing"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-regulated-product-appeals, amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Edit (model number); Product Safety case"
surface_verified: false
symptom_keywords: ["product safety affidavit manufacturer relationship", "test report manufacturer does not match listing", "model number does not match test report", "ASIN reinstatement product safety", "safety test report model number mismatch"]
error_text: ["We noticed a discrepancy between the manufacturer name in your test report", "Please provide an affidavit that explains the relationship between these two companies.", "Your Amazon listing must show one of the model numbers that appears in your safety documentation.", "Our team will review your complete submission within two to three business days after we receive all required documentation."]
asked_as: ["After submitting safety documents for a suspended ASIN, the product safety team asked for an affidavit on the manufacturer relationship and a model number change before reinstating it."]
synonyms: []
resolution_status: resolved
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/203-safety-and-compliance-verification-for-private-brands-products-GZR95BWRLUAD37C5.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-product-document-upload.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0101"
---

## Question

After submitting safety documents for a suspended ASIN, the product safety team asked for an affidavit on the manufacturer relationship and a model number change before reinstating it.

## Answer

Before submitting safety documents, check that the manufacturer name and model number on the listing match the test report. If they differ, Amazon asks for a signed affidavit explaining the company relationship and a model number update to a tested model, so fix the listing on every SKU of the ASIN and reply in the same case with proof.

## Cause

Amazon links the listing to the tested product: the manufacturer on the test report differed from the manufacturer on the listing, and the listing's model number was a parent placeholder that did not appear in the test report.

## Fix

1. Draft an affidavit on letterhead of either company stating how the two companies are related, with signer name and title, signature, date, ASIN and product name, as a PDF.
2. Confirm with the brand which tested model number covers the sold product, including any component sold separately that the test covered.
3. In Inventory, select Edit on every affected SKU (FBA and FBM offers) and set the model number field to the tested model number.
4. Take a backend screenshot as proof; the detail page's Item Details can lag.
5. Reply in the same product safety case with the affidavit and the change confirmation (reply needs operator approval).

## Verify

The model number shows the tested value in the listing edit view; the detail page's Item Details can lag. The case returns a reinstatement and the product safety flag clears, as it did in the source.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/203-safety-and-compliance-verification-for-private-brands-products-GZR95BWRLUAD37C5.md`
- Also in: `MAG SOPs/catalog/catalog-sop-product-document-upload.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains the product safety team's affidavit and model-number requirements when the test report does not match the listing's manufacturer or model.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-children-s-product-safety-request-or-children-s-product-certificate-cpc.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`, `Amazon Seller Help/articles/203-safety-and-compliance-verification-for-private-brands-products-GZR95BWRLUAD37C5.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`).
