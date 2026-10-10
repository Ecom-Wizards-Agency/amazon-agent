---
id: KC-0052
title: "Agency user cannot open Brand Analytics after the brand was connected to the account"
kind: diagnosis
topic: brand-registry
status: reviewed
skills: [amazon-reporting, amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Brands > Brand Analytics; Settings > User Permissions"
surface_verified: false
symptom_keywords: ["Brand Analytics not visible", "no access to Brand Analytics", "Brand Analytics permission agency user", "Brand Analytics missing after brand registry", "grant Brand Analytics rights"]
error_text: []
asked_as: ["After the brand was correctly connected to the seller account, the account owner could see Brand Analytics but the agency user could not use it."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0052"
---

## Question

After the brand was correctly connected to the seller account, the account owner could see Brand Analytics but the agency user could not use it.

## Answer

When Brand Analytics works for the account owner but not for you, the brand connection is fine and your user simply lacks the permission. Ask the primary user to grant Brand Analytics in User Permissions; account-level eligibility and user-level rights are separate. Brand Analytics is a Brand Representative selling benefit, so a Reseller role will not unlock it.

## Cause

Brand Analytics became available on the account once the brand was connected with a qualifying role, but each secondary user still needs that feature granted in user permissions by the account's primary user or an admin.

## Fix

1. Confirm the brand is connected to the seller account in Brand Registry with a Brand Representative role.
2. Ask the account's primary user to open Brand Analytics to confirm the account has access.
3. Have the primary user grant the agency user the Brand Analytics permission in Settings > User Permissions.
4. Reload the Brand Analytics dashboard as the agency user.

## Verify

The agency user opens the Brand Analytics dashboard and sees the brand's reports.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Separates account-level Brand Analytics eligibility from the per-user permission an agency user still needs.
- Existing coverage: full (`Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`).
