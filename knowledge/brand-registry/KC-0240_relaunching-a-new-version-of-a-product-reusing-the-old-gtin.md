---
id: KC-0240
title: "Relaunching a new version of a product: reusing the old GTIN ties it to the old ASIN, so get a new GTIN before enrolling it in Transparency"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central listing creation; Transparency portal (product enrollment, code requests)"
surface_verified: false
symptom_keywords: ["same UPC for new product version", "relaunch product new GTIN", "transparency enrollment needs GTIN", "new version links to old ASIN", "request transparency codes for new product"]
error_text: []
asked_as: ["While setting up Transparency codes for a relaunched product, the agency asked the client for a GTIN; the client asked whether to reuse the existing one or issue a new one."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md", "Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-03
review_by: 2027-10
provenance: "ledger:KC-0240"
---

## Question

While setting up Transparency codes for a relaunched product, the agency asked the client for a GTIN; the client asked whether to reuse the existing one or issue a new one.

## Answer

Give a new version of a product its own GTIN and ASIN; reusing the old GTIN attaches it to the old listing, and Amazon does not let you change the product ID on an existing listing. Enroll the new GTIN in Transparency, request codes in the Transparency portal and label units before they ship. Amazon's Transparency page says enrolled products cannot be sold without a valid code whether fulfilled by Amazon or by the seller, so do not launch either channel before the codes are in place.

## Cause

A product ID cannot be changed on an existing listing and a new version of a product must get its own detail page, so submitting the old GTIN matches the relaunched product to the old ASIN. Transparency enrollment is per product and needs the GTIN the new listing will use.

## Fix

1. Issue a new GTIN (from the brand's own GS1 allocation) for the new product version.
2. Create the new listing with that GTIN.
3. Enroll the new product in Transparency with the new GTIN; the enrollment confirmation email goes to the account that enrolled it.
4. Request Transparency codes in the Transparency portal and have them printed and applied before the next shipment.
5. Hold the launch until the units carry valid codes.

## Verify

The product was enrolled in Transparency under the new GTIN and codes were requested for the next shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The detail page rules and Transparency SOP cover new-ASIN and enrollment rules separately; none links a relaunch GTIN to Transparency enrollment.
- Existing coverage: partial (`Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`).
