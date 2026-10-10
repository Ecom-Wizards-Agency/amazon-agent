---
id: KC-0063
title: "Ads console keeps showing Payment Failure and card charges are reversed although the account is active"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads console > Billing and payments > payment settings"
surface_verified: false
symptom_keywords: ["ads payment failure", "card charges reversed amazon ads", "campaigns paused payment failure", "change default card ads console", "payment failure account active"]
error_text: ["Payment Failure"]
asked_as: ["The Ads console showed 'Payment Failure' while the account was active."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md", "Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0063"
---

## Question

The Ads console showed 'Payment Failure' while the account was active. Adding another card did not help and the attempted charges showed as reversed. Setting a card from a different bank as default fixed it; switching back to the original card afterwards also worked.

## Answer

If the Ads console shows Payment Failure while the account is otherwise active, and new cards from the same bank also fail, make a card from a different bank the default so Amazon retries the payment. Amazon retries automatically after a payment method update. Once the payment clears you can usually return to the preferred card, but check the status again afterwards.

## Cause

Not established in the thread. The failure cleared once a different default card triggered a successful retry; that the original card also worked afterwards suggests a temporary bank-side decline rather than a card problem.

## Fix

1. Open the Ads billing and payment settings and confirm the 'Payment Failure' status.
2. Check the card details, available limit and whether the bank blocks online or foreign-currency charges.
3. If charges show as reversed, add a card from a different bank and make it the default payment method so Amazon retries the payment. Payment changes are the account holder's action.
4. Once the payment succeeds and campaigns deliver, switch back to the preferred card if needed and confirm the status stays clear.

## Verify

After the default card changed the payment went through; it also kept working after switching back to the original card.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the field fix of switching the default to a card from a different bank when same-bank cards keep failing with reversed charges.
- Existing coverage: full (`Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`, `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`, `Advertising Help After Login/_index/category-billing-and-payments.txt`, `Advertising Help After Login/articles/098-pay-for-ads-in-your-card-currency-GWUL24U4AVZEN8D6.md`).
