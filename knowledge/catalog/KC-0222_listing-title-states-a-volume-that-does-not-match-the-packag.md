---
id: KC-0222
title: "Listing title states a volume that does not match the packaging: correct the size per variation from the pack images"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-seo]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central listing title (child ASINs of a size variation)"
surface_verified: false
symptom_keywords: ["title size does not match packaging", "wrong ml in title", "amazon asks to update title volume", "variation title wrong size", "title contradicts product image"]
error_text: []
asked_as: ["After an email about a listing title, the agency received packaging images showing a different fill volume from the one in the title, and asked the client which volumes each size variation should show"]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0222"
---

## Question

After an email about a listing title, the agency received packaging images showing a different fill volume from the one in the title, and asked the client which volumes each size variation should show.

## Answer

Take the size or volume in a title from the packaging, never from an earlier draft or a guess. When a title and the pack images disagree, confirm the value per variation with the brand owner and correct each child title and size attribute. Amazon may correct or suppress titles with inaccurate information.

## Cause

The title carried a volume with no source in the product data, so it contradicted the packaging images. Where the wrong value came from was not established in the thread.

## Fix

1. Collect the current packaging images or artwork for every size variation.
2. Confirm with the brand owner the exact size or volume for each variation.
3. Update each child ASIN title with its own size or volume; keep size out of the parent title.
4. Check the size attribute in each child matches the corrected title.
5. Allow 24 to 48 hours for the title change to display, then recheck the detail pages.

## Verify

Each child detail page shows a title whose volume matches the packaging image and the size attribute for that variation.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the per-variation correction flow when a title volume contradicts the packaging; the title guideline states the rule but not the fix.
- Existing coverage: full (`Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-trademark-tm-infringement-yank.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`).
