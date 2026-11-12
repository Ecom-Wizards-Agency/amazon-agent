---
id: KC-0324
title: "Upload preview requires Color on a parent although the blank template marks it inapplicable"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Add Products via Upload > Preview file and fix errors"
surface_verified: false
symptom_keywords: ["parent color required", "preview template conflict", "gray parent attributes"]
error_text: ["This information is required to submit your product."]
asked_as: ["Should I fill Color on a parent when the template marks it inapplicable?"]
synonyms: ["Color Map", "non-buyable parent", "parentage exemption"]
resolution_status: partial
fix_source: agency
evidence_location: run-note
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["skills/amazon-catalog/references/parentage-flatfile-playbook.md"]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0324"
---

## Question

The upload preview flags Color Map and Color on a non-buyable parent, but the fresh template marks those cells gray. Should the parent contain a color?

## Answer

Keep those fields blank when the target account's fresh template explicitly exempts the parent. Do not invent a color to clear the preview. Check the parent condition and submission scope before using any supported full-file submission option; the server's per-row processing result remains the verdict.

## Cause

The observed preview conflicts with the template's parent exemption. For the observed nutritional-supplement template, the parent condition selects a gray inapplicable rule with stopIfTrue before the required-border rule. The preview's internal cause is unverified.

## Fix

1. Verify the fresh template's seller, marketplace, product type and dataRow.
2. Check Data Definitions, the Instructions legend and conditional-formatting formulas. Confirm that the parent condition makes the color fields inapplicable.
3. Reconcile every intended parent and child row. A ready-row count alone must not cause the parent to be omitted.
4. With authorization for the exact payload, use a supported route that submits the complete file unchanged. If the scope or exemption is uncertain, obtain the current parent-specific schema or Amazon confirmation first.

## Verify

Read the processing summary per row, including successful-with-other-errors results. An observed full-file submission accepted the blank parent colors without a Color error. Verify saved relationships and storefront state separately; review-pending or compliance findings can still delay publication.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: [Retrieve a Product Type Definition](https://developer-docs.amazon/sp-api/docs/retrieve-a-product-type-definition), which distinguishes PARENT schemas from CHILD schemas.
- Also in: `skills/amazon-catalog/references/parentage-flatfile-playbook.md`.
- Evidence: team vault ledger row for this id.

## Gaps

Observed for a US nutritional-supplement template. Do not generalize the exemption to other product types without checking their fresh template. Final publication was still under Amazon review in the observed run.
