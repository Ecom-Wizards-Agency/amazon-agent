---
id: KC-0248
title: "Which access does an agency need after the brand owner registers: Seller Central user and Brand Registry role?"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-client-onboarding, amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["what rights does the agency need brand registry", "add agency to brand registry", "brand registry admin role agency", "add authorized partner seller central"]
error_text: []
asked_as: ["Brand owners finished their registrations and asked what rights the agency needs and how to add the agency in Seller Central and in Brand Registry."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-06
review_by: 2027-10
provenance: "ledger:KC-0248"
---

## Question

Brand owners finished their registrations and asked what rights the agency needs and how to add the agency in Seller Central and in Brand Registry.

## Answer

Give the agency two separate accesses: a Seller Central user with the needed permissions and a Brand Registry user with the Administrator role. Only an Administrator can assign Brand Registry roles, so a lower role blocks the agency from managing users and selling roles. Register the brand under the owner's login so ownership never has to be transferred.

## Cause

Seller Central user permissions and Brand Registry roles are managed separately; Brand Registry roles can only be assigned by an Administrator, so the agency needs the Administrator protection role to manage the brand fully.

## Fix

1. In Seller Central, add the agency as a user or authorised partner with the permissions the scope needs (menu path not shown in the thread or a local capture; confirm it live).
2. Have the agency create a Brand Registry account and accept the terms first; the Administrator can only invite an email address that already has a Brand Registry account.
3. In Brand Registry, open user management (top right of the page), invite the agency's Brand Registry email and assign the Administrator protection role.
4. Prefer registering the brand under the brand owner's own login rather than the agency's, so the brand need not be moved later.

## Verify

The agency user can sign in to Brand Registry with the Administrator role and see the brand, and the Seller Central invite is accepted.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Combines the two separate agency accesses (Seller Central user and Brand Registry Administrator) and the advice to register under the owner login.
- Existing coverage: full (`Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`).
