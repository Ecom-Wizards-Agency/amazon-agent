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
error_text: ["You already have a protection role", 5461, 6789]
asked_as: ["The client was invited to a licensed brand in Brand Registry."]
synonyms: ["Markenregistrierung", "brand approval", "error 5461"]
resolution_status: partial
fix_source: client
evidence_location: case
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md"]
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0005"
---

## Question

The client was invited to a licensed brand in Brand Registry. Accepting the invite failed with 'You already have a protection role', although no brand appeared in the account. Once the brand appeared in Brand Overview, creating products still failed, and the client could not assign the Brand Representative selling role to the company seller account.

## Answer

Before calling it a Brand Registry problem, sort it into three questions: does the user hold a protection role, does the seller account hold a selling role through its merchant token, and is the account approved to create ASINs for this brand in this category (error 5461)? 'You already have a protection role' means the invite duplicates an existing role, so ask the Administrator to change roles instead of re-inviting. For 5461, apply with real product photos, wait 24 hours after approval, then resubmit with a timestamped error screenshot if it persists. When Support replies generically, restate the exact on-screen message and attach a screenshot.

## Cause

Three separate permission layers were mixed up. Protection roles (Administrator, Rights Owner, Registered Agent) decide which Brand Registry tools a user can reach. The user already held the Rights Owner role, so a second invite for it could not be accepted, and Rights Owner and Registered Agent are mutually exclusive for the same brand. Selling roles (Brand Representative, Reseller) attach to a seller account's merchant token, not to a Brand Registry login. Amazon's help pages say both kinds of role can only be assigned or removed by the brand Administrator. Creating new ASINs for that brand in that category needed a separate brand-category listing approval (error 5461), which neither role grants.

## Fix

1. Open a Brand Registry case quoting the exact conflict message. If Support answers with generic role definitions, restate the actual on-screen blocker and attach a screenshot. Case sends need operator approval.
2. Apply for permission to create ASINs for the brand and category with photos of the physical branded product. After approval, error 5461 can persist up to 24 hours; if it still shows, resubmit with a timestamped screenshot of the 5461 error showing the brand.
3. For the protection-role conflict, ask an Administrator to change the user's roles under User Permissions > Connected users > Manage (for example to Administrator). A new invite does not change an existing role.
4. For the selling role, the Administrator assigns Brand Representative under Manage > Manage selling roles > Connect a selling partner account, using the seller account's merchant token. From the seller side, request it with the Brand Benefit Eligibility tool: Brands > Build your brand > View registered brands > Eligible brands > Request selling role. The Administrator has 30 days to decide; benefits follow within 48 hours of approval. Requests need operator approval.
5. If the seller account cannot accept the selling-role invite, the Administrator opens Brand Registry Support > Technical issue and quotes error code 6789. Support handles a selling role without the Administrator only to remove it when the Administrator cannot be reached.

## Verify

Amazon's quoted acceptance confirms the brand-category listing approval. The test listing and the Administrator role change were planned but not confirmed in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md` (captured and read 07.10.2026): the three protection roles, Administrator-only assignment in User Permissions, Rights Owner and Registered Agent mutually exclusive.
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md` (read 07.10.2026): Administrator-only selling roles, Brand Benefit Eligibility requests, error code 6789, Support only for removal.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The three-layer triage (protection role, selling role, 5461 approval), the 'already have a protection role' message and the 24-hour wait with a timestamped resubmit are not covered.
- Existing coverage: partial (a MAG SOP dropped on 08.10.2026, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, a MAG SOP dropped on 08.10.2026, `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`).
- Unconfirmed: the thread said Support grants a selling role when contacted from the selling account itself. The selling-roles page contradicts this: only the Administrator assigns selling roles, and Support is named only for removing a role when the Administrator cannot be reached.
- The protection-roles page also lets a user who already has an enrolled brand request a protection role through Brand Registry Support > Update brand ownership; the thread did not try it.
- The message 'You already have a protection role', error 5461 and the 24-hour wait appear in neither help page.
- Confidence is medium, not high: one thread; the role pages back the role mechanism but not the 5461 listing approval.
