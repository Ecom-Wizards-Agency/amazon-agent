---
id: KC-0283
title: "Payout shows an amount held in reserve: Amazon holds funds against returns and claims and releases them later"
kind: reference
topic: reporting
status: reviewed
skills: [amazon-reporting]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["money held in reserve", "account level reserve", "payout reserve new account", "when is reserve released", "balance on hold returns"]
error_text: []
asked_as: ["A seller saw part of the balance held in reserve on the payments page and asked whether Amazon keeps it in case of returns and releases it after some time."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/157-payments-faq-G69122.md", "Amazon Seller Help/articles/171-disburse-on-demand-GSCWUZNYQRY4LEZH.md", "Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0283"
---

## Question

A seller saw part of the balance held in reserve on the payments page and asked whether Amazon keeps it in case of returns and releases it after some time.

## Answer

An amount held in reserve is Amazon keeping funds against returns, refunds and claims, not money lost. A delivery date reserve moves to the account balance after the delivery date plus 7 days, and Amazon may set a wider reserve based on account risk; the agency observed holds of about two weeks. If it does not release, ask Selling Partner Support to review the account's reserve settings.

## Cause

Amazon may establish a reserve on an account based on its assessment of risk (Business Solutions Agreement), and a delivery date reserve moves funds to the account balance after the delivery date plus 7 days (Disburse on Demand page). The agency said the hold typically lasts about the first two weeks; the thread does not establish the reserve type, whether the account was new, or the exact release date.

## Fix

1. Open Payments and read the reserve line in the payout summary.
2. Treat it as funds held against returns, refunds and claims, not a lost amount; a delivery date reserve releases after the delivery date plus 7 days.
3. If the reserve does not release as expected, ask Selling Partner Support or Seller Assistant to review the account's reserve settings (operator approval needed before submitting a case).

## Verify

A later settlement shows the previously reserved amount released to the available balance.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/157-payments-faq-G69122.md`
- First-party: `Amazon Seller Help/articles/171-disburse-on-demand-GSCWUZNYQRY4LEZH.md`
- First-party: `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The local Payments FAQ capture lists the account level reserve question without its answer, so the new-account hold and release pattern is net new.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `Advertising Help After Login/articles/060-branded-keyword-guidelines-and-keyword-suspension-G2QZJUGUT4RGLJ6N.md`, `Amazon Seller Help/articles/166-express-payout-bank-account-and-debit-card-policies-GHRCBB7RE3HSLGHC.md`, `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`).
