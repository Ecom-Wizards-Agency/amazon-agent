---
id: KC-0039
title: "Image A/B test result is unclear: keep the main image identical when testing the secondary images"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [all]
marketplace_inferred: true
surface: "Brands > Manage Experiments"
surface_verified: false
symptom_keywords: ["image A/B test inconclusive", "test secondary images manage experiments", "main image changed during image test", "listing images experiment setup"]
error_text: []
asked_as: ["A main-image experiment came back insignificant with the old version winning, and the team set up a second experiment for the secondary listing images."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0039"
---

## Question

A main-image experiment came back insignificant with the old version winning, and the team set up a second experiment for the secondary listing images.

## Answer

Test one variable at a time in Manage Your Experiments. When you test the secondary listing images, keep the main image identical in both versions so click-through stays constant and any difference comes from the gallery. Test the main image separately.

## Cause

An image experiment that changes the main image and the secondary images at once cannot attribute the result; the main image drives search click-through while the gallery drives detail page conversion.

## Fix

1. In Manage Experiments, create the product images experiment for the secondary images.
2. Keep the main image identical in both versions so only the gallery differs.
3. Verify on the live experiment that both versions show the same main image.
4. Let the experiment run to significance before deciding.

## Verify

Both experiment versions show the same main image and differ only in secondary images.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the single-variable rule for image experiments: keep the main image identical when testing the secondary gallery.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-a-content.md`).
