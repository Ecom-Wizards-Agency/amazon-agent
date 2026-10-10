---
id: KC-0018
title: "Seller Central registration: which company's bank statement to upload when the IP owner and the paying company differ, and whether the store name must match the brand"
kind: rule
topic: account-health
status: reviewed
skills: [amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central registration"
surface_verified: false
symptom_keywords: ["which bank statement seller central registration", "bank statement different company", "store name already taken", "store name brand name", "seller verification bank statement"]
error_text: []
asked_as: ["A new seller registering Seller Central under the trademark-owning company, while a separate management company pays costs and receives revenue, asked whose bank statement to upload, and whether a rej"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/184-registration-requirements-by-store-G201468460.md", "Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md", "Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0018"
---

## Question

A new seller registering Seller Central under the trademark-owning company, while a separate management company pays costs and receives revenue, asked whose bank statement to upload, and whether a rejected store name meant the brand name was taken.

## Answer

Upload verification documents, including the bank statement, for the exact legal entity the Seller Central account is registered under, even if a sister company pays the bills. The store name is just the account's display name: it does not need to match the brand, and you can change it later, so a refused name does not block anything.

## Cause

Seller verification checks that documents match the business registered on the account, so the bank statement must belong to the legal entity the account is registered under. The store (display) name is independent of the brand name used in Brand Registry and listings and can be changed later.

## Fix

1. Decide which legal entity owns the seller account (here the trademark owner).
2. Upload a bank statement for that same entity during verification, not for an affiliated paying company.
3. If the desired store name is refused, pick any available variant; it does not affect the brand name and can be changed later in account settings.

## Verify

Verification passes without a document mismatch request.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/184-registration-requirements-by-store-G201468460.md`
- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- First-party: `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that the bank statement must match the registered entity even when an affiliated company pays, and that a refused store name is unrelated to the brand name and changeable.
- Existing coverage: full (`Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/184-registration-requirements-by-store-G201468460.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`).
