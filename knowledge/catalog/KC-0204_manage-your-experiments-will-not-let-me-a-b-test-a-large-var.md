---
id: KC-0204
title: "Manage Your Experiments will not let me A/B test a large variation family: what to do instead"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-listing-images]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Brands > Manage Your Experiments"
surface_verified: false
symptom_keywords: ["can't A/B test", "experiment not eligible", "manage your experiments variations limit", "MYE ineligible ASIN", "test images without experiments"]
error_text: []
asked_as: ["A teammate could not run an image A/B test on a product in a large variation family and asked for alternatives."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0204"
---

## Question

A teammate could not run an image A/B test on a product in a large variation family and asked for alternatives.

## Answer

When Manage Your Experiments refuses an ASIN, run a before-and-after test: write down the current content and baseline metrics, change the top children directly and compare equal periods. Treat the result as weaker than a true split test because time effects are not controlled. Check the wizard's eligibility status rather than assuming a variation-count rule.

## Cause

Not established in the thread. Manage Your Experiments refused the product, and a teammate believed experiments are limited to parents with a small number of children. The capture lists brand ownership and enough recent traffic per ASIN as the eligibility rules and says several variants can be tested with the Multi-attribute experiment type, so the variation-count limit is not confirmed.

## Fix

1. Check the eligibility status the experiment wizard shows for the ASIN.
2. If it is ineligible, record the current content and the baseline metrics (sessions, conversion, sales) for a fixed period.
3. Make the change directly on the top-selling children.
4. Compare the same metrics for an equal period after the change and note seasonality or ad changes that could confound it.

## Verify

A before-and-after comparison over equal periods exists for the changed ASINs.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a before-and-after fallback for ASINs that Manage Your Experiments refuses and records an unconfirmed variation-count limit against the published eligibility.
- Existing coverage: full (`Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-a-content.md`).
