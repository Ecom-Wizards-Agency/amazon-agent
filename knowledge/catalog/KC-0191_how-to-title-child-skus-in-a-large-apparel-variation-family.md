---
id: KC-0191
title: "How to title child SKUs in a large apparel variation family: shared base title plus each child's color and size"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Catalog > Edit listing / flat file"
surface_verified: false
symptom_keywords: ["variation child titles", "child ASIN title color size", "base title for variations", "parent title without size", "apparel variation titles"]
error_text: []
asked_as: ["A team member preparing title updates for an apparel variation family with many child SKUs asked whether every child should share one base title with only the color and size adjusted per child."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-parentage-creation.md"]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0191"
---

## Question

A team member preparing title updates for an apparel variation family with many child SKUs asked whether every child should share one base title with only the color and size adjusted per child.

## Answer

Give every child in a variation family the same base title and add only that child's color and size. Keep size and color out of the parent title, because Amazon shows the parent title on the detail page and a child's title only once that child is in the cart. Check that the color and size in each title match the child's variation attributes.

## Cause

Amazon's title guideline says the detail page displays the parent ASIN's title, and a child ASIN's title appears only once that ASIN is added to the customer's cart; it never appears on the detail page. Size and color therefore belong in each child title and not in the parent title.

## Fix

1. Write one base title for the family: brand, product type and key attributes, without color or size.
2. Use the base title unchanged as the parent ASIN title.
3. For each child SKU, append that child's own color and size to the base title so the attributes match the child's variation values.
4. For a large family, submit the title changes in bulk (flat file or FlatFilePro) rather than child by child; this is agency practice, not shown in the thread. Submitting the update needs operator approval.

## Verify

Spot-check several children in the edited listing or the exported file: each child title equals the base title plus its own color and size, and the parent title contains neither.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`
- Also in: `MAG SOPs/catalog/catalog-sop-parentage-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Little beyond the first-party title guideline; it adds the practice of one shared base title applied in bulk across a large family.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `MAG SOPs/catalog/catalog-sop-error-99003.md`).
