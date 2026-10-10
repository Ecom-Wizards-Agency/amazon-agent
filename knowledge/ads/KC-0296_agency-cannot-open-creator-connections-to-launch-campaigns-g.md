---
id: KC-0296
title: "Agency cannot open Creator Connections to launch campaigns: grant the Creator Connections user permission and Editor access"
kind: procedure
topic: ads
status: reviewed
skills: [amazon-creator-connections, amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads > Brand content > Creator connections; Seller Central > Settings > User Permissions > user > Creator Connections; Ads account user role"
surface_verified: false
symptom_keywords: ["creator connections no access", "cannot open creator connections permissions", "creator connections editor permission", "brand content creator connections access"]
error_text: []
asked_as: ["The agency needed to launch Creator Connections campaigns (Advertising > Brand content) but could not open the tool because of permissions, and asked the client to share access."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/196-create-and-manage-a-creator-connections-campaign-GMANECFAFD49W23Y.md", "Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0296"
---

## Question

The agency needed to launch Creator Connections campaigns (Advertising > Brand content) but could not open the tool because of permissions, and asked the client to share access.

## Answer

If you cannot open Creator Connections, check the agency user's role first: Viewer cannot create campaigns, and raising the user to Editor resolved it in the source case. If that is not enough, ask an admin to grant the Creator Connections permission in Seller Central under Settings > User Permissions > the user > Creator Connections. A new advertiser may need up to 7 to 10 business days after creating the advertising account before access appears.

## Cause

The agency user's role did not allow Creator Connections. The thread confirms only that raising the agency user's role to Editor resolved it; it does not show whether that role was set in Seller Central or in the Ads account, and the lead answered 'No' to the first permission screenshot. Amazon's help separately says admins grant access in Seller Central under Settings > User Permissions > Target User > Creator Connections.

## Fix

1. Ask the account admin to raise the agency user from Viewer to Editor (or Admin) so it can create campaigns.
2. If access is still missing, ask the admin to open Seller Central > Settings > User Permissions, select the agency user and grant the Creator Connections permission.
3. Reload Amazon Ads and open Brand content > Creator connections.
4. If the advertising account was created recently, allow up to 7 to 10 business days, as Amazon's help states, before escalating.

## Verify

The agency user opens Brand content > Creator connections and sees the option to create a campaign.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/196-create-and-manage-a-creator-connections-campaign-GMANECFAFD49W23Y.md`
- First-party: `Advertising Help After Login/articles/068-understand-account-permissions-GM4EFDQQPG9LGL3F.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms in practice that Creator Connections access needs both the Seller Central Creator Connections permission and an Editor-level Ads role.
- Existing coverage: full (`Advertising Help After Login/articles/196-create-and-manage-a-creator-connections-campaign-GMANECFAFD49W23Y.md`, `Advertising Help After Login/_index/category-account-management.txt`, `Advertising Help After Login/_index/ads-support-before-you-begin-dom.txt`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Advertising Help After Login/_index/category-audiences-and-targeting.txt`).
