---
id: KC-0253
title: "Brand not available when creating a listing in a reactivated or second-region seller account: connect that account to the brand by merchant token"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [UK, US]
marketplace_inferred: false
surface: "Brand Registry > Manage > Manage selling roles > Connect a selling partner account"
surface_verified: false
symptom_keywords: ["brand not linked to account", "cannot select brand when creating listing", "connect seller account to brand registry", "merchant token brand registry", "reactivated UK account brand missing"]
error_text: []
asked_as: ["After a dormant seller account in another region was reactivated (by updating the card on file), the team could not create listings because the brand was not linked to that account."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0253"
---

## Question

After a dormant seller account in another region was reactivated (by updating the card on file), the team could not create listings because the brand was not linked to that account.

## Answer

A brand selling role belongs to one seller account, identified by its merchant token, so a reactivated or second-region account will not see the brand until the Administrator connects it. Have the Administrator use Connect a selling partner account with that merchant token, choose the role to match the account's real relationship to the brand, accept the invitation in the connected account, and allow some time before retrying listing creation.

## Cause

Brand selling roles attach to a specific seller account through its merchant token. The reactivated regional account was a separate selling account with no selling role for the brand, so the brand did not appear when creating listings.

## Fix

1. Reactivate the dormant account if needed (in the thread, updating the payment card on file was enough; an error message can linger briefly).
2. Get the merchant token of that account from the gear icon > Account Info > Business information (needs a user with access to it).
3. As the brand Administrator, open Brand Registry > Manage > Manage selling roles, click Connect a selling partner account and choose Seller Central accounts.
4. Choose the selling role, select the account from the drop-down or Other account with its merchant token, choose the brand and click Connect selling account. Amazon defines Brand Representative as a partner directly employed by the brand and Reseller as an external third-party seller; the agency chose Reseller to limit content influence on the main marketplace, a benefit the capture does not establish (operator decision).
5. Accept the invitation from the email in the connected Seller Central account; the role shows as active on the Connected tab only after acceptance. If acceptance fails, open Brand Registry Support > Technical issue and quote error code 6789.
6. Retry listing creation and check that the brand appears.

## Verify

The brand appears as selectable when creating a listing in the connected account.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the reactivated second-region account case: the brand is missing until the Administrator connects that account's merchant token, which KC-0005 covers only for a single account.
- Existing coverage: full (`knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`).
