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
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md", "Amazon Seller Help/articles/001-account-settings-G181.md", "Amazon Seller Help/articles/099-common-reasons-you-cannot-find-your-handmade-listings-GRCWJ4KHBNQ3SNTB.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-03
review_by: 2027-10
provenance: "ledger:KC-0012"
---

## Question

The client asked how to tell whether their FBM offer had started selling.

## Answer

When an FBM offer shows no orders, first check that the account's listing status is not set to vacation mode, which deactivates all seller-fulfilled offers at once. After reactivating, check the shipping template and confirm the fulfiller uploads tracking automatically before the first orders arrive. A late or missing tracking upload hurts the late-shipment and valid-tracking metrics.

## Cause

The account's listing status was set to vacation mode, which makes all seller-fulfilled (FBM) offers inactive. The FBM offer could not win the Buy Box or take orders.

## Fix

1. Under Account Info > Listing status, switch from vacation (inactive) back to active. Settings changes need operator approval.
2. Update the shipping template under Shipping Settings so FBM rates and transit times are correct.
3. Confirm the 3PL has an Amazon integration or uploads tracking numbers; valid tracking and on-time confirmation feed the late-shipment and valid-tracking metrics.

## Verify

The client confirmed the shipping template was updated and the 3PL said it is integrated. No FBM order or Buy Box win is confirmed in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- First-party: `Amazon Seller Help/articles/001-account-settings-G181.md`
- First-party: `Amazon Seller Help/articles/099-common-reasons-you-cannot-find-your-handmade-listings-GRCWJ4KHBNQ3SNTB.md` (vacation settings as a reason listings cannot be found; Handmade scope)
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source gives 'FBM offer not selling, check vacation mode' as a diagnosis or joins it with the 3PL tracking check.
- Existing coverage: partial (a MAG SOP dropped on 08.10.2026, `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`, `Amazon Seller Help/articles/001-account-settings-G181.md`, a MAG SOP dropped on 08.10.2026).
- The dedicated help article 'Listing status for vacations, holidays, and other absences' is not captured locally. 028 states the rule in one line, 001 only links it, and 099 gives the vacation check for Handmade listings. The FBM-only scope of vacation mode also rests on that article. Capture it before verifying this unit.
- Unsupported: the thread's advice that an FBM offer sharing an ASIN with an FBA offer needs a lower landed price to take the Buy Box. No cited source backs it.
