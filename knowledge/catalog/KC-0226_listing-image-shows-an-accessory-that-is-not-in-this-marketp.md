---
id: KC-0226
title: "Listing image shows an accessory that is not in this marketplace's package"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-listing-images]
marketplaces: [US]
marketplace_inferred: false
surface: "Listing image gallery"
surface_verified: false
symptom_keywords: ["image shows accessory not included", "adapter not included in US package", "listing image wrong package contents", "image review client correction"]
error_text: []
asked_as: ["During client review of a new image set, the client pointed out that one image named an accessory that ships only in other regions and is not in this marketplace's package; the agency proposed rewordi"]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/153-product-image-guide-G1881.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0226"
---

## Question

During client review of a new image set, the client pointed out that one image named an accessory that ships only in other regions and is not in this marketplace's package; the agency proposed rewording the copy to cover both regions, and the client asked to remove the accessory from this marketplace's image.

## Answer

Build each marketplace's image set from that marketplace's package contents, and remove any accessory that ships only in other regions instead of rewording around it. Amazon's image guide forbids showing accessories that are not included and could confuse the customer as a main-image requirement; applying the same standard to secondary images was the client's decision here and keeps the images accurate.

## Cause

The image copy was written for the global product, but the package sold in this marketplace does not include one of the region-specific accessories. An image that names or shows an accessory not in the box misstates the package contents.

## Fix

1. Check each image against the package contents for the specific marketplace, not the global product.
2. Remove any accessory that is not shipped in that marketplace's package from the image and its copy.
3. Have the client confirm the package contents before the images are uploaded.

## Verify

Every accessory named or shown in the marketplace's images is in that marketplace's box.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/153-product-image-guide-G1881.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Applies the image-guide rule on non-included accessories to per-marketplace package differences in secondary images.
- Existing coverage: partial (`Amazon Seller Help/articles/153-product-image-guide-G1881.md`).
