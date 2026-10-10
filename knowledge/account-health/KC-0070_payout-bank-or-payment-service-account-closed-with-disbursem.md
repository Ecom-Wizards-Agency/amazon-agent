---
id: KC-0070
title: "Payout bank or payment-service account closed with disbursement due soon: replace the deposit method and tell Seller Support"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Settings > Account Info > Deposit Methods; Seller Support case"
surface_verified: false
symptom_keywords: ["payout account shut down", "payment provider closed our account", "change deposit method", "new bank account for Amazon payouts", "disbursement bank account closed"]
error_text: []
asked_as: ["The seller's payment-service account that received Amazon payouts was closed by the provider without a clear reason, and the seller asked what else could receive Amazon payouts before the next disburs"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md", "Amazon Seller Help/articles/161-acceptable-bank-accounts-and-payment-service-providers-GKLETRP8MLF7CVFX.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0070"
---

## Question

The seller's payment-service account that received Amazon payouts was closed by the provider without a clear reason, and the seller asked what else could receive Amazon payouts before the next disbursement a few days later.

## Answer

When the account that receives Amazon payouts is closed, replace the deposit method in Seller Central with another acceptable account before the next disbursement rather than trying to recover the closed one. Amazon pays out only to a bank account issued to the seller by a deposit-taking bank or a participating payment service provider, never to a card or an online payment system, and the bank information must stay current. If you notify Seller Support, state only the facts and offer a bank statement as proof.

## Cause

The payout destination itself became unusable because the payment provider closed the account; nothing on the Amazon side was wrong. The provider's reason was not established in the thread.

## Fix

1. ["1. Open a bank account issued to the seller's own legal entity by a deposit-taking bank, or by a payment service provider that participates in Amazon's PSP program, located in a country supported by the Amazon Currency Converter.", "2. In Seller Central, replace the deposit method on the Deposit methods page for every affected marketplace and complete any verification Amazon asks for.", "3. Optionally draft a short factual Seller Support note stating that only the deposit account changed and offering a bank statement as proof. Operator approval is required before sending.", "4. Watch the next disbursement and forward any verification request from Amazon to the agency."]

## Verify

The new deposit method shows as active in Seller Central without a verification banner and the next disbursement arrives in the new account.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`
- First-party: `Amazon Seller Help/articles/161-acceptable-bank-accounts-and-payment-service-providers-GKLETRP8MLF7CVFX.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The captures say payouts need a current bank account, but none gives the urgent swap-and-notify sequence for a closed payout account.
- Existing coverage: partial (`Amazon Seller Help/articles/166-express-payout-bank-account-and-debit-card-policies-GHRCBB7RE3HSLGHC.md`, `Amazon Seller Help/articles/161-acceptable-bank-accounts-and-payment-service-providers-GKLETRP8MLF7CVFX.md`, `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`, `Amazon Seller Help/articles/186-payments-for-global-accounts-G201468470.md`, `Amazon Seller Help/articles/165-express-payout-frequently-asked-questions-GA24UN79VBPKXZXX.md`).
