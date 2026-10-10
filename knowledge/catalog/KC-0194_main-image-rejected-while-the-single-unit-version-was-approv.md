---
id: KC-0194
title: "Main image rejected while the single-unit version was approved: a pack-count banner or graphic in the background"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-listing-images, amazon-image-production, amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central image upload (main image)"
surface_verified: false
symptom_keywords: ["main image rejected pack banner", "2 pack ribbon main image", "multipack badge rejected", "main image graphics background", "image approved for 1 pack but not 2 pack"]
error_text: []
asked_as: ["An image upload for a 2-pack variant was rejected while the matching 1-pack image was approved; the only difference was the pack-count graphics in the background."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/153-product-image-guide-G1881.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0194"
---

## Question

An image upload for a 2-pack variant was rejected while the matching 1-pack image was approved; the only difference was the pack-count graphics in the background.

## Answer

If a multipack's main image is rejected while the single-unit image passed, look for a pack-count ribbon or badge first. Main images may not contain text or graphics in the background or over the product, so remove the banner and show the real units instead. Put pack-count callouts on secondary images.

## Cause

Main images may not carry text, logos, color blocks or other graphics covering the product or in the background. The pack-count ribbon was such a graphic, so the multipack main image failed while the clean single-unit image passed.

## Fix

1. Compare the rejected main image with an approved sibling and isolate added graphics (pack-count ribbons, badges, text).
2. Export the main image without the banner and re-upload it.
3. If the pack count must be visible, show the actual number of units in the image instead of a graphic label, following the multipack imaging standards.
4. Keep pack-count callouts for secondary images.

## Verify

The re-uploaded main image without the pack-count graphic is accepted and shows on the detail page (acceptance was not confirmed in the thread).

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/153-product-image-guide-G1881.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties a specific rejection pattern (multipack main image rejected, single-unit sibling approved) to the pack-count ribbon as the cause, which the image guide states only generally.
- Existing coverage: full (`Amazon Seller Help/articles/153-product-image-guide-G1881.md`, `MAG SOPs/catalog/logistics-sop-package-dimensions-and-weight-update.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`).
