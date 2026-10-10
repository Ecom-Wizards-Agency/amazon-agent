---
id: KC-0286
title: "Ads campaigns stop with payment failure while paying from the seller account balance"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads billing and payments"
surface_verified: false
symptom_keywords: ["ads payment failure", "campaigns paused payment failed", "seller account balance insufficient ads", "add backup payment method ads", "campaign not delivering billing"]
error_text: ["Payment failure"]
asked_as: ["During a peak sales event the Ads console showed a payment failure and campaigns stopped delivering."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md", "Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md", "Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0286"
---

## Question

During a peak sales event the Ads console showed a payment failure and campaigns stopped delivering. The payment method was the seller account balance, and the brand did not understand why funds were insufficient.

## Answer

If campaigns pause with a payment failure while ads are paid from the seller account balance, the funds available (balance minus reserves and pending charges) did not cover the invoice. Add a credit or debit card as a backup payment method; Amazon retries the payment, charges the card if the balance falls short, and campaigns resume once payment succeeds. Set the backup card before peak events.

## Cause

Ads were charged against the seller account balance. When Amazon cannot charge the default payment method, campaigns pause. For balance-funded accounts the usable amount is funds available: the balance minus holds, reserves and pending charges, so a balance that looks large can still fail an invoice. Why funds were short was not established in the thread.

## Fix

1. In the Ads console go to Administration > Billing > Payment Settings and confirm the payment method shows Seller account balance.
2. Click Change payment profile, click Edit next to Seller account balance, check Add a backup payment method and add a credit or debit card (billing change, needs owner approval).
3. Wait for Amazon to retry the payment automatically.
4. Check that campaign status returns to Delivering.

## Verify

Invoice status turns to paid and campaign status is back to Delivering.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`
- First-party: `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties the seller-account-balance payment method to peak-season ad pauses and the backup card as the fix, which the help pages cover separately.
- Existing coverage: full (`Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`, `Advertising Help After Login/_index/category-billing-and-payments.txt`, `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`, `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`).
