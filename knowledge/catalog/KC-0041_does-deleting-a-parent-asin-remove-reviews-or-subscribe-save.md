---
id: KC-0041
title: "Does deleting a parent ASIN remove reviews or Subscribe & Save from the child ASINs?"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central variation family (parent ASIN)"
surface_verified: false
symptom_keywords: ["delete parent ASIN reviews", "will deleting parent remove reviews", "Subscribe and Save after removing parent", "break variation family impact", "remove parent listing"]
error_text: []
asked_as: ["The agency planned to delete a parent ASIN as part of an attempt to unblock child ASINs; the client asked whether deleting the parent would delete the reviews and Subscribe & Save."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0041"
---

## Question

The agency planned to delete a parent ASIN as part of an attempt to unblock child ASINs; the client asked whether deleting the parent would delete the reviews and Subscribe & Save.

## Answer

Deleting a parent ASIN does not delete reviews or Subscribe & Save, because both are tied to the child ASINs. The children leave the family, so the reviews are no longer shown aggregated across it. You can create a new parent and regroup the children later. Get the brand owner to approve before you delete the parent.

## Cause

Reviews and Subscribe & Save enrolment belong to the child ASINs. The parent only groups them, so deleting it removes the grouping: the children stop sharing a family page and their reviews are no longer shown aggregated.

## Fix

1. Confirm Subscribe & Save enrolment and reviews sit on the child ASINs.
2. Tell the client that deleting the parent only ends the grouping and the combined review display. Get their approval before deleting.
3. Delete the parent ASIN.
4. Recreate a parent and reassign the children later if the family is needed again.

## Verify

Each child ASIN still shows its own reviews and Subscribe & Save option after the parent is gone.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms from a live case that Subscribe & Save, like reviews, stays on the child ASINs when the parent is deleted.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-how-to-remove-a-listing-from-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `MAG SOPs/catalog/catalog-sop-breaking-a-phantom-parentage.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`).
