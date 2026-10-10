---
id: KC-0019
title: "Dormant seller account redirects to inactiveAccount and the billing page after Continue: re-add the card"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > inactiveAccount page > seller verification > billing (charge method)"
surface_verified: false
symptom_keywords: ["seller account inactive dormant", "inactiveAccount redirect billing", "reactivate dormant seller account", "re-verify ID dormant account"]
error_text: [inactiveAccount]
asked_as: ["The agency asked the client to reactivate a dormant Seller Central account by re-verifying IDs; after clicking Continue the client kept landing on the billing page."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md", "Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-02
review_by: 2027-10
provenance: "ledger:KC-0019"
---

## Question

The agency asked the client to reactivate a dormant Seller Central account by re-verifying IDs; after clicking Continue the client kept landing on the billing page.

## Answer

When a dormant seller account redirects to the inactiveAccount page and then to billing, re-add a valid credit card; the account reactivates once identity and the charge method are both current. Only the account owner can do this because it touches identity and payment details.

## Cause

Amazon deactivates dormant accounts and requires re-verification; the reactivation flow sent the user to billing because a valid charge method was needed. The thread does not state why the card was missing or invalid.

## Fix

1. Have the account owner sign in; Seller Central shows the inactiveAccount page.
2. Click Continue and complete the identity re-verification.
3. When the flow lands on the billing page, re-add a valid credit card as the charge method.
4. Reload Seller Central and confirm the account is active.

## Verify

Seller Central opens normally without the inactiveAccount redirect.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`
- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The charge-method help page covers adding a card, but not the dormant-account inactiveAccount redirect to billing and its fix.
- Existing coverage: partial (`Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `sop-drafts/2026-08-08_amazon-client-onboarding.md`).
