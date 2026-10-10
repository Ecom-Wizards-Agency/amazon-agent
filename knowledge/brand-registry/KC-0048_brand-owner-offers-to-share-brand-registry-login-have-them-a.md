---
id: KC-0048
title: "Brand owner offers to share Brand Registry login: have them add the agency as a user under User Permissions instead"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-client-onboarding]
marketplaces: [all]
marketplace_inferred: true
surface: "Brand Registry > User Permissions"
surface_verified: false
symptom_keywords: ["share brand registry credentials", "give agency brand registry access", "add user brand registry", "brand registry admin invite", "user permissions brand registry"]
error_text: []
asked_as: ["A brand owner logged into Brand Registry and Seller Central with the same account asked how best to share Brand Registry credentials so the agency could move faster."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md", "Amazon Seller Help/articles/232-role-assignment-error-messages-GPQTLD2Z4EYAVGX5.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0048"
---

## Question

A brand owner logged into Brand Registry and Seller Central with the same account asked how best to share Brand Registry credentials so the agency could move faster.

## Answer

Never take a brand owner's Brand Registry password; ask them to invite your team's email under User Permissions instead. Only an Administrator can assign roles, and Amazon recommends at least two Administrators per brand, so granting the agency Administrator access is normal when it runs the brand's protection work.

## Cause

Credential sharing is unnecessary: a Brand Registry Administrator can invite other users and assign protection roles through User Permissions, and the invitee uses their own Amazon login.

## Fix

1. Ask the brand owner not to share login credentials.
2. The brand owner, as Administrator, opens User Permissions in Brand Registry and invites the agency's email address with the Administrator role (or the narrower role the work needs).
3. The agency accepts the invitation with its own Brand Registry account.
4. Confirm access, then tell the brand owner which information is still needed.

## Verify

The agency user appears in User Permissions with the assigned role and can open the brand's Brand Registry tools.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- First-party: `Amazon Seller Help/articles/232-role-assignment-error-messages-GPQTLD2Z4EYAVGX5.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the agency-onboarding practice of refusing shared Brand Registry credentials in favour of an Administrator invite under User Permissions.
- Existing coverage: full (`Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `Amazon Seller Help/articles/214-brand-registry-application-process-GN2GYQVPR7R4VMPB.md`).
