---
id: KC-0012
title: "FBM offer not selling because the account is in vacation mode; reactivate listings, set a shipping template and confirm the 3PL uploads tracking"
kind: diagnosis
topic: account-health
status: draft
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Settings > Account Info > Listing status (vacation mode); Settings > Shipping Settings > Shipping templates"
surface_verified: false
symptom_keywords: ["FBM not selling", "how do I know FBM started", "vacation mode listings inactive", "FBM offer inactive", "3PL tracking upload FBM"]
error_text: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md", "Amazon Seller Help/articles/001-account-settings-G181.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-shipping-template-for-fbm-listings.md", "MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md"]
supersedes: []
contradicts: []
observed: 2025-03
review_by: 2026-03
provenance: "ledger:KC-0012"
---

## Question

The client asked how to tell whether their FBM offer had started selling.

## Answer

When an FBM offer shows no orders, first check that the account's listing status is not set to vacation mode, which deactivates all seller-fulfilled offers at once. After reactivating, check the shipping template and confirm the fulfiller uploads tracking automatically before the first orders arrive. A late or missing tracking upload hurts the late-shipment and valid-tracking metrics. If FBA and FBM offers share an ASIN, the FBM offer needs a lower landed price to take the Buy Box.

## Cause

The account's listing status was set to vacation mode, which makes all seller-fulfilled (FBM) offers inactive. The FBM offer could not win the Buy Box or take orders.

## Fix

1. Under Account Info > Listing status, switch from vacation (inactive) back to active. Settings changes need operator approval.
2. If an FBA offer shares the ASIN, price the FBM offer slightly below it so it can win the Buy Box. Price changes need operator approval.
3. Update the shipping template under Shipping Settings so FBM rates and transit times are correct.
4. Confirm the 3PL has an Amazon integration or uploads tracking numbers; valid tracking and on-time confirmation feed the late-shipment and valid-tracking metrics.

## Verify

The client confirmed the shipping template was updated and the 3PL said it is integrated. No FBM order or Buy Box win is confirmed in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- First-party: `Amazon Seller Help/articles/001-account-settings-G181.md`
- Also in: `MAG SOPs/catalog/catalog-sop-shipping-template-for-fbm-listings.md`
- Also in: `MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source gives 'FBM offer not selling, check vacation mode' as a diagnosis or joins it with the 3PL tracking check.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-shipping-template-for-fbm-listings.md`, `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`, `Amazon Seller Help/articles/001-account-settings-G181.md`, `MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md`).
