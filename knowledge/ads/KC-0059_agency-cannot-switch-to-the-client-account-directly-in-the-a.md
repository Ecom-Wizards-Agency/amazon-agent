---
id: KC-0059
title: "Agency cannot switch to the client account directly in the Ads console: manager account link request needs advertiser approval"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [DE, US]
marketplace_inferred: true
surface: "Amazon Ads > Advertising accounts > Manager accounts > review link request"
surface_verified: false
symptom_keywords: ["manager account link request", "approve agency as trusted partner", "client account not in ads account selector", "link advertiser to manager account", "switch account without Seller Central"]
error_text: []
asked_as: ["The agency needed the client to approve a manager account link request so the client advertising account could be selected directly in the Ads console instead of reaching it through the Seller Central"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/077-add-accounts-to-your-manager-account-G23QYEJNEX3FJFH5.md", "Advertising Help After Login/articles/075-understand-manager-accounts-GU3YDB26FR7XT3C8.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0059"
---

## Question

The agency needed the client to approve a manager account link request so the client advertising account could be selected directly in the Ads console instead of reaching it through the Seller Central workaround.

## Answer

If you reach a client's advertising account only through Seller Central, request to link it to your manager account and have the client's account administrator approve the review-link-request. Only an administrator of the advertiser account can approve it. Once approved, select the account directly in the Ads console account selector.

## Cause

Only manager account administrators can link accounts; when the agency is not an admin of the advertiser account, its link request goes to that account's administrator, who must review and approve it before the account appears under the agency manager account.

## Fix

1. From the agency manager account, request access to the advertiser account (Account or Advertiser ID plus marketplace).
2. Send the client administrator the review-link-request URL that Amazon generates and ask them to approve it (client action).
3. Wait for the client to confirm approval.
4. Open Campaign Manager and select the client account in the top-right account selector to confirm it is now reachable directly.

## Verify

The client advertiser account appears under the agency manager account and can be selected in the Ads console account selector without going through Seller Central.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/077-add-accounts-to-your-manager-account-G23QYEJNEX3FJFH5.md`
- First-party: `Advertising Help After Login/articles/075-understand-manager-accounts-GU3YDB26FR7XT3C8.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the agency use case: the client administrator approves the review-link-request so the account can be selected directly in the Ads console instead of via Seller Central.
- Existing coverage: full (`Advertising Help After Login/_index/category-account-management.txt`, `Advertising Help After Login/articles/077-add-accounts-to-your-manager-account-G23QYEJNEX3FJFH5.md`, `sop-drafts/2026-06-07_daily-amazon-account-health-check.md`, `Advertising Help After Login/articles/075-understand-manager-accounts-GU3YDB26FR7XT3C8.md`).
