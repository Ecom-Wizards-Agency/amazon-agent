---
id: KC-0321
title: "Agency cannot get into a seller's Ads console during onboarding: the client contact needs advertising rights first, then grants the agency in Seller Central User Permissions"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-client-onboarding, amazon-ads-console]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["agency no advertising access", "grant agency access Amazon Ads", "authorized partner user permissions", "client cannot grant ads access", "onboarding access preflight"]
error_text: []
asked_as: ["During onboarding the client contact had no Amazon Ads access yet, so could not grant the agency access."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md", "Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0321"
---

## Question

During onboarding the client contact had no Amazon Ads access yet, so could not grant the agency access. After the Ads account owner granted advertising access, the agency still needed access through Seller Central before it could work.

## Answer

On a seller account, ask the client to grant agency access in Seller Central User Permissions, and first check that the client contact doing it holds advertising rights; a contact without them cannot pass them on. Confirm access by opening the account in Campaign Manager before planning work.

## Cause

For seller accounts, a seller account admin grants Amazon Ads access in Seller Central User Permissions; the Ads console's own Invite users route covers non-seller advertiser accounts. The client contact who was asked to add the agency had no advertising access yet, so the account owner first gave that contact advertising access. The contact then added the agency through Seller Central User Permissions, and after that the agency could work.

## Fix

1. Identify which client user is an admin on the seller account and holds advertising rights; a contact without those rights cannot grant them to anyone.
2. If needed, the account owner first gives that contact advertising access.
3. The contact or owner adds the agency user in Seller Central > Settings > User Permissions and grants the advertising and other required rights. Permission changes are the client's action.
4. The agency opens Campaign Manager, selects the client account and marketplace in the account selector and confirms that it sees the campaigns.

## Verify

The agency user opens Campaign Manager, selects the client account and marketplace in the account selector, and sees the campaigns; the Seller Central user also loads the account.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- First-party: `Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The hits cover AMC and Ads API onboarding, not the two-grant agency access sequence (Ads admin grant plus Seller Central authorized-partner permissions), which is new.
- Existing coverage: full (`Advertising Help After Login/articles/231-accessing-amazon-marketing-cloud-GYQH4WUFEQBVEN6N.md`, `Amazon Ads Help/articles/guides/004-amazon-ads-api-onboarding-overview.md`, `Amazon Ads Help/articles/knowledge-hub/010-python-authorization-amazon-ads-api.md`, `Advertising Help After Login/articles/073-permissions-definitions-for-the-ads-api-GR9KP77YZUD3UEZD.md`).
