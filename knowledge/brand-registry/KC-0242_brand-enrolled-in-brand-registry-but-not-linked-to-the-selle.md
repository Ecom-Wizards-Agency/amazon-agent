---
id: KC-0242
title: "Brand enrolled in Brand Registry but not linked to the seller account the agency manages"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-client-onboarding]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central User Permissions; Brand Registry User Permissions and Manage selling roles"
surface_verified: false
symptom_keywords: ["connect brand registry to seller central", "brand registry invite awaiting acceptance", "agency needs brand registry admin", "link brand to seller account", "grant agency access brand registry"]
error_text: []
asked_as: ["During onboarding, the client had enrolled the brand directly in Brand Registry and added the agency in Seller Central, but the brand was not connected to the seller account and the Brand Registry inv"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md", "Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0242"
---

## Question

During onboarding, the client had enrolled the brand directly in Brand Registry and added the agency in Seller Central, but the brand was not connected to the seller account and the Brand Registry invite stayed at awaiting acceptance.

## Answer

Seller Central access does not give Brand Registry rights, and only a Brand Registry Administrator can connect a seller account to the brand. Ask the client's Administrator to invite the agency's Brand Registry account with the Administrator role, or to connect the seller account themselves, then connect the seller account as Brand Representative under Manage selling roles before listing.

## Cause

Brand Registry roles and Seller Central permissions are separate. Only a Brand Registry Administrator can assign roles and connect a selling partner account to the brand, so an agency with Seller Central access or a lower Brand Registry role cannot link the brand until it holds the Administrator role.

## Fix

1. Ask the client to add the agency user in Seller Central (User Permissions or the partner invite) with the needed rights, and accept the invite.
2. Make sure the agency user has a Brand Registry account and has accepted its terms, then ask the client's Brand Registry Administrator to invite that account's email under User Permissions with the Administrator role.
3. Accept the Brand Registry invite. A lower role such as Registered Agent cannot connect the seller account; if the brand is still not connected, ask the Administrator to upgrade the role to Administrator or to connect the account themselves.
4. As Administrator, connect the seller account under Manage > Manage selling roles > Connect a selling partner account (Seller Central, Brand Representative), and accept the invitation in Seller Central.
5. Only then create or edit listings under the brand.

## Verify

The seller account shows as active on the Connected tab of Manage selling roles, and listing creation under the brand works.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the onboarding sequence and the awaiting-acceptance email check to the role rules the help pages already state.
- Existing coverage: full (`Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`).
