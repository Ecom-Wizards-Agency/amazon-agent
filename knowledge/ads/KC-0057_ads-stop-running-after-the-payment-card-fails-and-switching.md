---
id: KC-0057
title: "Ads stop running after the payment card fails and switching to seller balance does not help"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-troubleshooting]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads console > Billing and payments > Payment settings"
surface_verified: false
symptom_keywords: ["ads paused payment failed", "credit card declined advertising", "deduct from seller balance not working", "campaigns stopped no email from Amazon", "advertising payment failure"]
error_text: []
asked_as: ["The card on the advertising account had a problem at the issuer and campaigns stopped during a peak event."]
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
contradicts: ["Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md"]
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0057"
---

## Question

The card on the advertising account had a problem at the issuer and campaigns stopped during a peak event. Switching the payment to deduct from the Amazon seller balance did not work, and the seller received no email about the failure and found it by accident.

## Answer

If ads stop suddenly, check Billing and payments before anything else, because a failed charge pauses every campaign. Deduct from seller balance is not an emergency fallback when the available balance is low; add a backup card ahead of peak events instead. Do not rely on a failure email reaching you: on peak days check the billing status directly.

## Cause

When Amazon cannot charge the default advertising payment method, campaigns pause. Deducting from the seller balance only works when the funds available, after reserves and pending charges, cover the charge in full, so a low balance makes that fallback fail too.

## Fix

1. Open Billing and payments in the Ads console and check the payment status and failure reason.
2. Check whether funds available in the seller account cover the outstanding amount before choosing deduct from seller balance.
3. Update the payment profile with a working card; the thread needed several cards before one went through. Allow for a pre-authorization charge on a new card.
4. Add a second card as a backup payment method so a future failure falls through to it.
5. Do not judge the same-day ACOS of the recovery day: attributed sales lag clicks, so read ACOS on the following days.

## Verify

Campaigns show delivering again and the invoice or payment status shows paid.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`
- First-party: `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The help page covers payment failures, but not that deduct-from-balance fails when available funds are low during an outage, nor that no failure email may arrive.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`).
