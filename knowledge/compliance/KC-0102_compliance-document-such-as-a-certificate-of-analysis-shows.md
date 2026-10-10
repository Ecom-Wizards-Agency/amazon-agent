---
id: KC-0102
title: "Compliance document such as a Certificate of Analysis shows publicly on the detail page and reveals the factory"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-catalog, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Product detail page document section; compliance document upload"
surface_verified: false
symptom_keywords: ["certificate of analysis visible on listing", "compliance document showing on detail page", "remove uploaded document from listing", "customers can see factory name", "product documents section on listing"]
error_text: []
asked_as: ["The brand asked to replace the Certificate of Analysis on the listing, because it was in a foreign language and showed the factory name to competitors."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-product-document-upload.md"]
supersedes: []
contradicts: []
observed: 2025-05
review_by: 2027-10
provenance: "ledger:KC-0102"
---

## Question

The brand asked to replace the Certificate of Analysis on the listing, because it was in a foreign language and showed the factory name to competitors. The service provider first said the document was internal only; the brand then showed it was visible on the public detail page without logging in.

## Answer

Assume any document added to a listing as a product or compliance-media document can be published on the detail page. Before uploading, check it for supplier names, factory details or foreign-language text you do not want customers or competitors to see, and check the live page logged out after approval. Removal can take more than one attempt and an escalation.

## Cause

Documents added to a listing as product documents (the Compliance media attributes) are published on the detail page after approval, per the product document SOP. The certificate appeared in a document section customers can see without logging in, while the service provider believed it was internal only. The thread does not show which upload route was used.

## Fix

1. Open the listing logged out and check the document section near the bottom of the detail page.
2. Before removing or replacing it, confirm the document is not required compliance evidence for the category, and replace it only with an equivalent document; a different document type such as a study does not replace a certificate.
3. Replace or remove the published document through the listing's Compliance media attributes (listing edit needs operator approval).
4. Allow up to 24 business hours for the change to show.
5. If the document still shows, escalate through Seller Support; in the thread the first change did not work and removal needed escalation across several Amazon teams (route not shown).
6. Recheck the live page until the document is gone.

## Verify

View the detail page logged out and confirm the document section no longer shows the certificate.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-product-document-upload.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The document-upload SOP says approved documents publish on the detail page, but nothing warns that a compliance certificate can expose factory details publicly or how hard removal is.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-product-document-upload.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `Amazon Seller Help/articles/099-common-reasons-you-cannot-find-your-handmade-listings-GRCWJ4KHBNQ3SNTB.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`).
