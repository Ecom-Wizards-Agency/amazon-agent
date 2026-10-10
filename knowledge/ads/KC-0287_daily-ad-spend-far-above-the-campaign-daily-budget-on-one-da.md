---
id: KC-0287
title: "Daily ad spend far above the campaign daily budget on one day"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ads-performance-briefs, amazon-audit]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads Campaign Manager campaign settings (budget)"
surface_verified: false
symptom_keywords: ["ad spend spike one day", "spent more than daily budget", "why was ad spend so high yesterday", "budget overspend Amazon Ads", "unspent budget rollover"]
error_text: []
asked_as: ["A client asked why ad spend on one day was far above the usual daily level."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Advertising Help After Login/articles/010-understand-budgets-GTGPQGUXNCTHE2DS.md", "Advertising Help After Login/articles/014-edit-your-budget-GVYUKBJQFPH7ZQ2L.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0287"
---

## Question

A client asked why ad spend on one day was far above the usual daily level.

## Answer

Treat a one-day spend spike as normal budget pacing before treating it as a fault: Amazon can spend up to 100% above the daily budget on high-traffic days using budget left over from quieter days, and caps the month at daily budget times days in the month. Check that earlier days underspent and that the month stays within that cap, and switch the campaign to the 25% increase setting if the client needs flatter daily spend.

## Cause

A Sponsored ads daily budget is an average over the calendar month. Amazon uses leftover budget from low-traffic days to raise the budget by up to 100% on high-traffic days (or 25% if the campaign setting is changed), while keeping monthly spend at or below daily budget times days in the month.

## Fix

1. Compare the day's spend per campaign with each campaign's daily budget and check whether earlier days in the month underspent.
2. Confirm the month's total spend will stay within daily budget times the days in the month; Amazon applies this cap over the calendar month, so one day above budget is expected when earlier days left budget unused.
3. If single-day spikes are unacceptable, change the campaign setting so Amazon raises the daily budget by only 25% (Sponsored ads > Campaigns > Settings), or lower the daily budget; a budget or setting change needs approval.
4. Explain to the client that the spike reuses unspent budget from earlier days and does not raise the monthly total.

## Verify

Monthly spend per campaign does not exceed daily budget times days in the month.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/010-understand-budgets-GTGPQGUXNCTHE2DS.md`
- First-party: `Advertising Help After Login/articles/014-edit-your-budget-GVYUKBJQFPH7ZQ2L.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Applies the first-party budget rollover rule to the common client question of a single-day spend spike and how to check it against the monthly cap.
- Existing coverage: full (`Advertising Help After Login/articles/226-unspent-campaign-budget-in-portfolios-beta-GXAJ8NNCDCQ4XEX5.md`, `Advertising Help After Login/articles/010-understand-budgets-GTGPQGUXNCTHE2DS.md`).
