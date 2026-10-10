---
id: KC-0236
title: "Variation child missing from the listing until a missing attribute Amazon asked for is filled in"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Manage All Inventory > listing issues / Edit listing"
surface_verified: false
symptom_keywords: ["variation option disappeared", "size option missing from listing", "Amazon asks for scent attribute", "child ASIN not showing missing attribute"]
error_text: []
asked_as: ["The client asked why one size option of the product no longer existed on the listing; Amazon was asking for an attribute value (scent) on that child."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/152-attributes-guide-GBWHYLJ7NNQMXBAQ.md"]
related_sops: [knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0236"
---

## Question

The client asked why one size option of the product no longer existed on the listing; Amazon was asking for an attribute value (scent) on that child.

## Answer

When a variation option vanishes from a listing, check whether Amazon is asking for a missing attribute on that child before you rebuild parentage. Supply the accurate value and resubmit. Amazon's attributes guide treats a missing required attribute as an error to fix by providing the value. Confirm on the detail page that the child returns.

## Cause

Amazon was requesting a missing attribute value on the child listing, and the agency stated that the child would return once the value was supplied. The thread does not show the child returning, and why Amazon newly required the attribute was not established.

## Fix

1. Open the missing child in Manage All Inventory and read the listing issue or the attribute Amazon is requesting.
2. Get the actual value from the brand owner or the product packaging. Do not guess; listing data must accurately describe the product.
3. Fill in the requested attribute and save or resubmit.
4. Recheck the detail page after processing to confirm the child is back in the family.

## Verify

The child option shows again on the parent detail page and the listing issue clears.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/152-attributes-guide-GBWHYLJ7NNQMXBAQ.md`
- Also in: `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The attributes guide covers missing-attribute errors and KC-0006 covers another cause of vanishing children, but not a child dropping from the family until an Amazon-requested attribute is filled.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `MAG SOPs/catalog/catalog-sop-error-99003.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `Amazon Seller Help/articles/134-listings-apis-GD76M4FUWL4NEU32.md`).
