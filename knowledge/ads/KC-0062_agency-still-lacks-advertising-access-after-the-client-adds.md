---
id: KC-0062
title: "Agency still lacks advertising access after the client adds a user; invite the right email under Settings > User Permissions"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-client-onboarding, amazon-ads-console]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Settings > User Permissions"
surface_verified: false
symptom_keywords: ["give agency advertising access", "add user seller central advertising", "user permissions invite wrong email", "agency cannot see ads account", "grant ads console access to partner"]
error_text: []
asked_as: ["The agency asked the client to grant advertising access."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md", "Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0062"
---

## Question

The agency asked the client to grant advertising access. The client's first attempt used the wrong email address and was done in the wrong place.

## Answer

Give the client the exact login email and point them to Settings > User Permissions in Seller Central, where a seller account admin selects Add User. Check that the invite goes to that email and includes advertising rights, then confirm access by selecting the advertiser in Campaign Manager. A short click-through demo avoids a second round trip.

## Cause

The invitation was sent to an email address other than the agency's login, and it was not made through Seller Central User Permissions, where a seller account admin invites users and sets their advertising rights.

## Fix

1. Send the client the exact email address the agency uses to log in.
2. Ask a seller account admin to open Settings > User Permissions in Seller Central and select Add User (or the authorized partner option) for that email.
3. Ask them to grant the advertising permission the agency needs before saving.
4. Accept the invitation from the agency inbox and confirm the advertiser appears in the Amazon Ads account selector.

## Verify

Open Campaign Manager and confirm the client's advertiser account and marketplace are selectable from the agency login.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md`
- First-party: `Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the common failure (invite sent to the wrong email or outside Seller Central User Permissions) to the first-party add-user steps.
- Existing coverage: full (`Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`, `Advertising Help After Login/articles/187-add-or-remove-users-from-your-organization-s-account-GJHUF3HF98KVR4RM.md`, `Advertising Help After Login/_index/category-account-management.txt`, `Advertising Help After Login/articles/231-accessing-amazon-marketing-cloud-GYQH4WUFEQBVEN6N.md`).
