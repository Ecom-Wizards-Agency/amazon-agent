---
id: KC-0327
title: "Variation type is locked after the parent listing is created"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Manage products > Edit parent listing > Variations"
surface_verified: true
symptom_keywords: ["variation theme disabled", "change Size to Package Size Name", "locked variation type"]
error_text: ["The variation type cannot be edited after the parent SKU is created."]
asked_as: ["Can an existing variation family change from Size to Package Size Name?"]
synonyms: ["Pack Size", "variation theme migration"]
resolution_status: diagnosis-only
fix_source: unknown
evidence_location: run-note
confidence: high
verification: verified
verified_on: "2026-11-08"
verified_how: "live-ui"
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-10
provenance: "ledger:KC-0327"
---

## Question

Why are all variation-type controls disabled when editing an existing parent?

## Answer

Seller Central locks the variation theme after creating the parent listing. The live UI instructs the seller to delete the parent SKU and create a new family with the desired theme. A disabled Package Size Name control can indicate a locked existing family even when that theme is supported for the product type.

## Cause

The existing parent retains its original theme. Child labels or package-size attributes alone do not change the family's variation theme.

## Fix

1. Confirm the account, marketplace, current family, and the desired theme's availability for the actual product type. The current US `SKIN_SERUM` template supports `PACKAGE_SIZE_NAME`, but its definition requires a marketing size name that appears on the external packaging. A desired selector label alone does not establish that value.
2. Preserve the current hierarchy and child listing data. Prepare the exact parent-only removal and rebuild plan under `skills/amazon-catalog/references/team-catalog-change-workflow.md`.
3. Obtain approval for the parent deletion and rebuild. Do not interpret a request to rename the selector as approval to delete the parent.
4. Use ordered files with a verification gate after parent removal and before rebuilding. Preserve the existing child listings.

## Verify

For diagnosis, capture the disabled controls and the parent-rebuild instruction. After an approved rebuild, verify processing per SKU, the retained child ASINs, the family hierarchy, and the customer-facing selector.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: Seller Central parent Variations editor, read live on 08.11.2026; no help-page capture yet.
- First-party: current US `SKIN_SERUM` blank template, Valid Values and Data Definitions for Variation Theme Name and Package Size Name, downloaded and inspected on 08.11.2026.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

The lock and the UI's rebuild instruction were verified. Rebuild execution, processing duration, and retention of the previous parent ASIN were not verified in this check. Verify theme availability separately for each product type and marketplace.
