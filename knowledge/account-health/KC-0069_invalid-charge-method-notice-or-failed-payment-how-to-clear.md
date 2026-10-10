---
id: KC-0069
title: "Invalid Charge Method notice or failed payment: how to clear it and stop it recurring"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-ads-console]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Account Info (charge method); Amazon Ads > Payment settings"
surface_verified: false
symptom_keywords: ["invalid charge method", "update your payment method", "payment failure amazon", "credit card declined seller central", "campaigns paused payment failed", "add backup card"]
error_text: ["Invalid Charge Method"]
asked_as: ["The agency saw a payment-method warning in the account and asked the client to update the card."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: screenshot
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md", "Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md", "Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0069"
---

## Question

The agency saw a payment-method warning in the account and asked the client to update the card. The client updated it, the warning came back the next day, and the client updated it again and asked a second account admin to add a further card as backup. In a sibling thread on another account the notice read Invalid Charge Method and the client fixed it by replacing the card.

## Answer

When Amazon shows Invalid Charge Method or a payment failure, have the client's account admin replace or correct the card in the seller account or the Ads payment profile; the agency never handles card details. For Ads paid from the seller balance or Deduct from payment, add a card as the backup payment method so a failed charge falls back instead of pausing campaigns. Recheck the next day, because a replaced card can fail again.

## Cause

Amazon could not charge the card on file (expired, declined, or failing a validation check), so the charge method was flagged invalid. Why the first update did not hold was not established in the thread.

## Fix

1. Read the notice and note whether it concerns the seller account charge method or the advertising payment profile.
2. Ask an account admin who holds the card (the client, not the agency) to update or replace the card: in Seller Central under the charge method in Account Info (exact label not shown in the thread), or via Update payment profile in Amazon Ads billing. The agency does not handle card details.
3. Confirm the card is an accepted credit or debit card (no prepaid cards), active, with matching name, number and expiry, a valid billing address, and cleared for international and electronic charges.
4. In Seller Central, add another card to the account so a replacement primary is ready. In Amazon Ads, where the account pays from the seller account balance or Deduct from payment, add a credit or debit card as the backup payment method (Administration > Billing > Payment Settings > Change payment profile).
5. Recheck the account the next day; if the notice returns, have the cardholder ask the issuer whether it blocked the charge.

## Verify

The warning no longer shows in Seller Central or the Ads billing page the following day; for Ads, paused campaigns resume after the automatic payment retry.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`
- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party pages cover the fix; the card adds that the agency hands the card update to the client admin and that a replaced card can fail again the next day, so recheck.
- Existing coverage: full (`Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`, `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`, `Amazon Seller Help/articles/031-bank-account-and-credit-or-debit-card-information-for-your-seller-account-G19791.md`, `Advertising Help After Login/articles/094-update-your-payment-method-G2D9ZAAB4BUBDFY8.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
