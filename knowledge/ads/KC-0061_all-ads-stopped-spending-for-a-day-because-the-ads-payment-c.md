---
id: KC-0061
title: "All ads stopped spending for a day because the ads payment card was rejected"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads > Billing and payments; Campaign Manager"
surface_verified: false
symptom_keywords: ["ad spend dropped to zero for a day", "all campaigns stopped spending", "ads paused payment failure", "credit card rejected ads", "ads down over the weekend"]
error_text: []
asked_as: ["Ad spend dropped for a whole day over a weekend and nobody noticed; the client asked what happened."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md", "Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md", "Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0061"
---

## Question

Ad spend dropped for a whole day over a weekend and nobody noticed; the client asked what happened.

## Answer

If every campaign stops spending at once, check the advertising billing page for a payment failure before touching bids or budgets. A rejected card puts the account into payment failure and pauses all campaigns until the payment goes through. Add a backup card and monitor for zero-spend days, weekends included.

## Cause

The default payment card for advertising was rejected. When Amazon cannot charge the default payment method, the account goes into payment failure and campaigns pause until the payment succeeds.

## Fix

1. When spend drops across all campaigns at once with no schedule change, check Billing and payments for a payment failure notice first.
2. Update or fix the payment method (card active, limit, issuer restrictions); Amazon retries automatically. Payment profile changes need operator approval.
3. Add a debit or credit card as a backup payment method so a failed default is charged to the backup.
4. Allow up to 24 hours for the account to re-enable after updating the payment method.
5. Set up an alert or daily check for zero-spend days, including weekends.

## Verify

Billing shows the payment as successful, the payment-failure banner is gone, and campaigns show spend again.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/099-resolve-a-payment-failure-G2SQRLBPB8TY587E.md`
- First-party: `Advertising Help After Login/articles/087-payment-methods-sponsored-ads-GMELNQQNEEVLX456.md`
- First-party: `Advertising Help After Login/articles/091-add-a-backup-payment-method-GPGZ28EK9WM4LZ2E.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Gives the triage order for an all-campaign zero-spend day: check billing for a payment failure before bids or budgets, and monitor weekends.
- Existing coverage: full (`Advertising Help After Login/articles/237-best-practices-for-using-the-ads-agent-in-amc-to-generate-amc-sql-queries-GZTSBQTMR2VHPL85.md`, `Advertising Help After Login/articles/186-sites-selection-for-sponsored-ads-campaigns-GJGYD2FKNF3MUWBQ.md`, `Advertising Help After Login/articles/049-understand-ads-agent-GKT6KLCX98F5LWKM.md`).
