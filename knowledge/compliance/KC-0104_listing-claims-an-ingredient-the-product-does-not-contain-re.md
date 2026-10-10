---
id: KC-0104
title: "Listing claims an ingredient the product does not contain: remove it from text and images and re-check claims against the label"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-catalog, amazon-seo]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Catalog > Edit product"
surface_verified: false
symptom_keywords: ["listing claims ingredient not in product", "wrong ingredient in bullets", "inaccurate product claim listing", "remove false ingredient claim", "image shows ingredient product does not contain"]
error_text: []
asked_as: ["The client pointed out that the live listing said the product contained an ingredient it does not contain."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0104"
---

## Question

The client pointed out that the live listing said the product contained an ingredient it does not contain. The agency removed the claim the same day and scheduled a corrected image.

## Answer

Check every ingredient or material claim against the product label before it goes live, even when someone said earlier that the claim was fine. Amazon requires product information that is accurate and does not mislead customers about the product's characteristics. When a false claim is found, remove it from the text at once and replace any image that shows it.

## Cause

The ingredient claim had gone into the listing on an earlier understanding that the client had approved it, and nobody checked it against the product label. The thread does not show whether reviews or images repeated the claim, beyond an image correction being scheduled.

## Fix

1. Remove the incorrect ingredient claim from title, bullets, description and backend fields through Catalog > Edit product or a listing feed.
2. Brief a corrected image for any gallery or A+ image that shows the claim and replace it.
3. Re-check every ingredient and material claim against the physical label or specification sheet.
4. Confirm the corrected text is live on the product page.

## Verify

The live product page, images and A+ no longer mention the ingredient, and every remaining ingredient claim matches the label.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that a false ingredient claim spreads into Vine reviews and must be checked against the label; G200390640 only states the accuracy rule.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`, `knowledge/compliance/KC-0002_cosmetic-applicator-listing-removed-as-an-uncleared-medical.md`, `MAG SOPs/catalog/catalog-sop-mental-health-disorder-and-sleep-disorder-claims.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `MAG SOPs/catalog/catalog-sop-cancelling-your-vine-enrolled-products-on-seller-central.md`).
