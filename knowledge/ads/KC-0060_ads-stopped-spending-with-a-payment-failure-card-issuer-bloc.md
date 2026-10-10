---
id: KC-0060
title: "Ads stopped spending with a Payment failure: card issuer blocked the Amazon Ads charge"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads > Billing and payments > Payment settings"
surface_verified: false
symptom_keywords: ["ads not spending", "payment failure on ads", "campaigns paused billing", "card blocked amazon ads charge", "update charge method ads"]
error_text: ["Payment failure"]
asked_as: ["Ad spend stopped (or the Ads console showed a payment failure) and the agency asked the client whether Amazon was still spending and to fix the advertising payment method."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md", "Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0060"
---

## Question

Ad spend stopped (or the Ads console showed a payment failure) and the agency asked the client whether Amazon was still spending and to fix the advertising payment method.

## Answer

When ads stop spending, check Ads billing for a payment failure before touching campaigns. Have the account owner check whether the card issuer blocked the charge and update the payment method; Amazon then retries and reactivates campaigns. A backup payment method prevents the next pause.

## Cause

Amazon Ads could not charge the default payment method, which pauses campaigns. In one case the card issuer blocked the Amazon charges as a security measure; in others the charge method needed updating.

## Fix

1. Check the Ads console billing page for a payment failure notice and the failed transactions.
2. Ask the client (payment-method owner) to check with the card issuer whether the Amazon Ads charge was blocked, and to allow it or update the charge method in Payment settings (client action; agencies must not handle payment details).
3. After the update, Amazon retries the payment automatically; confirm campaigns reactivate and spend resumes.
4. Recommend adding a backup payment method so a failed card does not pause campaigns again.

## Verify

The billing page shows the retried payment as paid and campaigns deliver impressions and spend again.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that a card issuer security block on the Amazon Ads charge is a real cause of sudden spend stops and that the payment-method owner, not the agency, clears it.
- Existing coverage: full (`Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`, `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`, `Advertising Help After Login/articles/084-understand-amazon-ads-billing-cycles-GY3YNTWRZYVPLADL.md`, `Advertising Help After Login/articles/186-sites-selection-for-sponsored-ads-campaigns-GJGYD2FKNF3MUWBQ.md`, `Advertising Help After Login/articles/098-pay-for-ads-in-your-card-currency-GWUL24U4AVZEN8D6.md`).
