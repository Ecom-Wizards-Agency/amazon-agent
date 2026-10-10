---
id: KC-0067
title: "Agency cannot open the Ads console for a newly added marketplace until a campaign exists and its user access covers that country"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-client-onboarding]
marketplaces: [DE]
marketplace_inferred: false
surface: "Amazon Ads console > Administration > Account access and settings; Seller Central > Campaign Manager"
surface_verified: false
symptom_keywords: ["cannot access Ads console new marketplace", "advertising account not showing for new country", "ads access missing after marketplace launch", "create placeholder campaign to activate ads account", "agency user missing country access ads"]
error_text: []
asked_as: ["The agency could not reach the Ads console for the brand in a newly opened European marketplace and asked the brand owner to create any campaign there so the console would become accessible."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md", "Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0067"
---

## Question

The agency could not reach the Ads console for the brand in a newly opened European marketplace and asked the brand owner to create any campaign there so the console would become accessible.

## Answer

When the Ads console for a newly launched marketplace is not reachable, ask the account admin to create one minimal auto campaign there and to add that country to the agency user's ads permissions. Then select the brand and country in Campaign Manager and confirm access before planning work. Pause the placeholder campaign once access is confirmed.

## Cause

The thread shows two blockers: the marketplace had no advertising activity yet, so the agency user could not reach that country's Ads console, and the agency user's ads permissions did not cover the new country. Amazon's user invitation flow sets country access per user for sponsored ads, which fits the second blocker. The thread does not confirm the exact mechanism for the first.

## Fix

1. Ask the account owner (a Seller Central or Ads admin) to create one Sponsored Products auto campaign with a minimal daily budget in the new marketplace; the agency pauses it afterwards.
2. Ask the admin to check the agency user's ads permissions and add the new country (Ads console: Administration > Account access and settings > Users > Change permissions; seller accounts: Seller Central User Permissions).
3. Reload Campaign Manager, select the brand and the new country in the top-right account selector and confirm the console opens.
4. Pause or archive the placeholder campaign once access works (a campaign change; follow the approval gate).

## Verify

The new country appears in the account selector for the agency user and Campaign Manager opens with the placeholder campaign listed.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/070-add-or-remove-users-from-your-account-GDQVHVQMY9F88PCA.md`
- First-party: `Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source covers the placeholder-campaign workaround for reaching a new marketplace's Ads console; the first-party page only covers per-country user access.
- Existing coverage: full (`Advertising Help After Login/_index/ads-support-before-you-begin-dom.txt`, `Advertising Help After Login/articles/073-permissions-definitions-for-the-ads-api-GR9KP77YZUD3UEZD.md`).
