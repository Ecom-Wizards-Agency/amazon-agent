---
id: KC-0005
title: "Brand visible in Brand Registry but listing creation still blocked: separate protection roles, selling roles and the brand-category listing approval (error 5461)"
kind: diagnosis
topic: brand-registry
status: draft
skills: [amazon-catalog]
marketplaces: [DE]
marketplace_inferred: true
surface: "Brand Registry (user roles, Brand Overview); Seller Central > Add a Product; Brand Registry support case"
surface_verified: false
symptom_keywords: ["already have a protection role", "error 5461 brand", "cannot create listing for brand in brand registry", "assign brand representative selling role", "licensed brand invite failed"]
error_text: ["You already have a protection role", 5461]
resolution_status: partial
fix_source: client
evidence_location: case
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-brand-registry-roles.md", "MAG SOPs/catalog/catalog-sop-error-8566.md", "MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md", "MAG SOPs/catalog/brand-registry-sop-how-to-submit-a-ticket-to-brand-registry.md"]
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2026-04
provenance: "ledger:KC-0005"
---

## Question

The client was invited to a licensed brand in Brand Registry. Accepting the invite failed with 'You already have a protection role', although no brand appeared in the account. Once the brand appeared in Brand Overview, creating products still failed, and the client could not assign the Brand Representative selling role to the company seller account.

## Answer

Before calling it a Brand Registry problem, sort it into three questions: does the user hold a protection role, does the seller account hold a selling role through its merchant token, and is the account approved to create ASINs for this brand in this category (error 5461)? 'You already have a protection role' means the invite duplicates an existing role, so ask the Administrator to change roles instead of re-inviting. For 5461, apply with real product photos, wait 24 hours after approval, then resubmit with a timestamped error screenshot if it persists. When Support replies generically, restate the exact on-screen message and attach a screenshot.

## Cause

Three separate permission layers were mixed up. The user already held a Rights Owner protection role, so a second Rights Owner invite cannot be accepted; only the Administrator assigns roles. Selling roles (Brand Representative, Reseller) attach to a seller account's merchant token, not to a Brand Registry login, and only the brand Administrator grants them, or Support when contacted from the selling account itself. Creating new ASINs for that brand in that category needed a separate brand-category listing approval (error 5461), which Brand Registry visibility does not lift.

## Fix

1. Open a Brand Registry case quoting the exact conflict message. If Support answers with generic role definitions, restate the actual on-screen blocker and attach a screenshot. Case sends need operator approval.
2. Apply for permission to create ASINs for the brand and category with photos of the physical branded product. After approval, error 5461 can persist up to 24 hours; if it still shows, resubmit with a timestamped screenshot of the 5461 error showing the brand.
3. For the selling role, ask the brand Administrator to change the user's role to Administrator or to assign Brand Representative to the seller account's merchant token. Alternatively, contact Support from the selling account that needs the role.
4. Remember that the Administrator can change user rights directly; a new invite does not.

## Verify

Amazon's quoted acceptance confirms the brand-category listing approval. The test listing and the Administrator role change were planned but not confirmed in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- Also in: `MAG SOPs/catalog/catalog-sop-brand-registry-roles.md`
- Also in: `MAG SOPs/catalog/catalog-sop-error-8566.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Also in: `MAG SOPs/catalog/brand-registry-sop-how-to-submit-a-ticket-to-brand-registry.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The three-layer triage (protection role, selling role, 5461 approval), the 'already have a protection role' message and the 24-hour wait with a timestamped resubmit are not covered.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-brand-registry-roles.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `MAG SOPs/catalog/catalog-sop-error-8566.md`, `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`).
