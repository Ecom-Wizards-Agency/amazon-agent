---
id: KC-0273
title: "Optimized child titles do not show on the detail page because the variation family displays the parent title"
kind: diagnosis
topic: seo
status: reviewed
skills: [amazon-seo]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central > Manage All Inventory > Variations; product detail page"
surface_verified: false
symptom_keywords: ["child title not showing on detail page", "detail page shows parent title", "variation title not updating", "optimized title not visible", "A/B test title with many variations"]
error_text: []
asked_as: ["A teammate asked to rewrite the title and test main images before pushing ads harder on main keywords."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md", "Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-parentage-creation.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0273"
---

## Question

A teammate asked to rewrite the title and test main images before pushing ads harder on main keywords. All child ASIN titles had already been optimized, but the detail page still showed an older title, and a title A/B test was not possible because the family had too many variants.

## Answer

When an optimized title does not appear on a variation family's detail page, update the parent ASIN title. Amazon shows the parent title on the detail page and child titles only in the cart. Put the main keywords right after the brand name, keep size and colour out of the parent title, and stay within the 75-character limit. If Manage Your Experiments cannot test the family, make the change directly and measure before and after.

## Cause

In a parent-child variation family the detail page displays the parent ASIN's title; child titles appear only once the item is in the cart. Editing only the child titles therefore leaves the visible title unchanged.

## Fix

1. Open the variation family in Seller Central and confirm which title the detail page shows.
2. Rewrite the parent ASIN title as well as the child titles, with the highest-priority keywords right after the brand name; keep size and colour in the child titles only and keep new titles within the current 75-character limit.
3. If Manage Your Experiments does not offer a title test for the family (the capture ties eligibility to recent traffic; the thread blamed the number of variants, which no capture confirms), change the title directly and compare performance before and after.
4. Brief any main-image test as a separate piece of work.

## Verify

After 24 to 48 hours of processing, reload the detail page of several children and confirm the new parent title is shown; compare conversion and keyword rank for the periods before and after the change.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`
- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: `MAG SOPs/catalog/catalog-sop-parentage-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links the parent-title display rule to the common symptom of optimized child titles not showing, and adds the before-and-after fallback when a large family cannot run a title experiment.
- Existing coverage: full (`Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`, `Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md`, `Amazon Seller Help/articles/096-get-started-with-amazon-handmade-G2NVGK9X3Y4XRT9H.md`).
