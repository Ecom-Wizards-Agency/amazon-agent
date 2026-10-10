---
id: KC-0241
title: "Agency has Seller Central access but no Brand Registry access"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-client-onboarding, amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["no brand registry access", "invite user brand registry", "brand registry user permissions", "agency cannot see brand registry", "seller central access not brand registry"]
error_text: []
asked_as: ["The client thought access had already been given, but the agency could not use Brand Registry; a client team member pointed out that access must be granted separately in Brand Registry."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-01
review_by: 2027-10
provenance: "ledger:KC-0241"
---

## Question

The client thought access had already been given, but the agency could not use Brand Registry; a client team member pointed out that access must be granted separately in Brand Registry.

## Answer

Seller Central user access does not carry over to Brand Registry. Ask a brand Administrator to invite the email of your Brand Registry account through User Permissions and assign the roles you need. Invite the address you actually sign in with, and check the roles after you accept, because an invitation without the right role leaves tools hidden.

## Cause

Brand Registry user permissions are managed separately from Seller Central user permissions. A Brand Registry Administrator must invite the user's Brand Registry account email to the brand and assign roles; accepting the invitation alone may leave the user without the needed rights.

## Fix

1. The agency user creates or signs in to a Brand Registry account (Seller Central credentials can be used) and accepts the terms and conditions.
2. A brand Administrator opens Brand Registry, clicks the gear icon, selects User Permissions, then Invite a user to your brand.
3. The Administrator enters the exact email address tied to the agency user's Brand Registry account, selects the brand and the store, and chooses the protection roles the agency needs (Administrator, Rights Owner or Registered Agent). Selling roles are assigned to Seller Central accounts separately.
4. The agency user accepts the invitation.
5. If tools are still missing after acceptance, the Administrator opens User Permissions > Connected users > Manage and adds the missing protection roles.

## Verify

The agency user sees the brand in Brand Registry and can open the tools the assigned role grants, such as Report a Violation.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Little beyond the roles page: it frames the separate Brand Registry invite as an agency onboarding step and warns that acceptance alone may leave roles unassigned.
- Existing coverage: full (`Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`).
