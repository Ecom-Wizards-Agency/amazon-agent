---
id: KC-0251
title: "Agency cannot assign brand rights to selling accounts in Brand Registry"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: "Brand Registry > User permissions"
surface_verified: false
symptom_keywords: ["assign brand rights to selling account", "brand registry administrator role", "add secondary user brand registry", "brand representative assignment", "agency brand registry access"]
error_text: []
asked_as: ["A brand owner wanted the agency to create new products under the brand and asked whether inviting the agency's email as a secondary user with the Administrator role is enough."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md", "Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-03
review_by: 2027-10
provenance: "ledger:KC-0251"
---

## Question

A brand owner wanted the agency to create new products under the brand and asked whether inviting the agency's email as a secondary user with the Administrator role is enough.

## Answer

Ask the brand owner to invite the agency's email as a secondary Brand Registry user with the Administrator role. Only an Administrator can assign selling roles, so a lower role cannot connect the brand to the selling accounts that create products.

## Cause

Selling roles (Brand Representative, Reseller) and protection roles can only be assigned by a Brand Registry Administrator, so the agency needs the Administrator role on its own Brand Registry user.

## Fix

1. The brand owner invites the agency's email as a secondary user in Brand Registry.
2. The owner assigns the Administrator role to that user.
3. The agency accepts the invitation.
4. The agency opens selling role assignments and confirms it can assign the brand to the needed selling accounts.

## Verify

The agency can open selling role assignments and assign the brand to another selling account.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the agency-access procedure: an agency user needs the Administrator role to assign selling roles, which the existing unit and help page only state as a rule.
- Existing coverage: partial (`Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`).
