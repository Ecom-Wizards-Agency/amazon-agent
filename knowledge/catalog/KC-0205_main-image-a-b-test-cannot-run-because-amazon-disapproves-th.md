---
id: KC-0205
title: "Main image A/B test cannot run because Amazon disapproves the current main image, and a second experiment waits until the running one ends"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-listing-images]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Brands > Manage Experiments"
surface_verified: false
symptom_keywords: ["main image A/B test not approved", "Manage Your Experiments image rejected", "cannot start second experiment", "MYE one experiment per ASIN", "original main image disapproved in experiment"]
error_text: []
asked_as: ["The brand owner sent several main image variants for Manage Your Experiments tests, asked which were not approved, and asked why a prepared image test had not started while a title test was running."]
synonyms: []
resolution_status: partial
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
provenance: "ledger:KC-0205"
---

## Question

The brand owner sent several main image variants for Manage Your Experiments tests, asked which were not approved, and asked why a prepared image test had not started while a title test was running.

## Answer

Manage Your Experiments runs only one experiment per ASIN at a time, so sequence title and image tests instead of expecting them in parallel. If Amazon's review rejects the current main image when you build an image experiment, leave the live image alone rather than swapping it to force a test, because the replacement path can cost you an image that still displays today. Check review results for the control and the variant before preparing more variants.

## Cause

Two separate constraints. First, by the agency's account, Amazon's image review disapproved the existing (control) main image as well as the variant, so no main image experiment could start without replacing the live main image; no Amazon notice text was quoted. Second, Manage Your Experiments allows only one experiment on a given ASIN at a time, so an image test on an ASIN with a running title test waits until that test ends. The thread does not show whether the title test ran on the same ASIN as the waiting image test.

## Fix

1. Read the image review result for both the control and the variant in Manage Experiments before planning further variants.
2. If the current live main image is itself disapproved for the experiment, do not replace the live main image just to unlock the test: a replaced image may not pass review again and cannot be restored reliably.
3. Keep the live main image and drop the main image experiment for that ASIN, or simplify the variant only if the control passes.
4. Queue experiments per ASIN: wait for a running title (or other) experiment on that ASIN to finish before starting the image experiment on it.
5. Let the experiment run its set duration (the MAG SOP gives 4 to 10 weeks) before declaring a winner.

## Verify

Manage Experiments shows the image experiment as running for the ASIN, with no other active experiment on that ASIN.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The one-experiment rule is covered; the advice to leave a live main image untouched when review rejects it as the experiment control is not in the captures.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-a-content.md`).
