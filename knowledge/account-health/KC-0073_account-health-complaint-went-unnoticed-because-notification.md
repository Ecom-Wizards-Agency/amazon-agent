---
id: KC-0073
title: "Account Health complaint went unnoticed because notifications went to an unmonitored inbox; route Account Health notifications to an address someone reads"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Settings > Notification Preferences (Account Health notifications)"
surface_verified: false
symptom_keywords: ["missed account health notification", "account health email not seen", "change notification email Seller Central", "account health alerts wrong inbox", "add second email for notifications"]
error_text: []
asked_as: ["After an account problem, the agency asked the seller to verify the Notification Preferences and send Account Health notifications to a second inbox that is actually read, so such problems do not get "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md", "Amazon Seller Help/articles/124-account-management-G202083910.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-05
review_by: 2027-10
provenance: "ledger:KC-0073"
---

## Question

After an account problem, the agency asked the seller to verify the Notification Preferences and send Account Health notifications to a second inbox that is actually read, so such problems do not get lost.

## Answer

Account Health notifications go to whatever addresses are set in Notification Preferences. Check that section during onboarding and make sure an address the team reads daily receives Account Health notifications, ideally with a second monitored address, so a policy warning or complaint is not missed.

## Cause

Account Health notifications went to an address the team did not watch, so problems could be missed. The specific missed notice is not stated in the thread.

## Fix

1. Open Settings > Notification Preferences in Seller Central (account owner or a user with that permission; a settings change needs operator approval).
2. Find the Account Health notifications section and edit its recipient addresses.
3. Add or switch to an address that the team reads daily; keep a second monitored address so alerts are not lost.
4. Save and confirm the change on the page.

## Verify

Notification Preferences shows the monitored address under Account Health notifications, and the next Account Health email arrives there.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- First-party: `Amazon Seller Help/articles/124-account-management-G202083910.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party pages only name Notification Preferences; the onboarding check to route Account Health alerts to a monitored second address is not written down anywhere.
- Existing coverage: full (`sop-drafts/2026-06-07_daily-amazon-account-health-check.md`).
