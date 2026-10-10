---
id: KC-0299
title: "Campaigns running out of budget during Prime Day: how often to check and how much to raise"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads campaign manager, Budgets view"
surface_verified: false
symptom_keywords: ["out of budget prime day", "campaigns running out of budget during event", "prime day budget increase", "hourly budget check", "budget rule for peak event"]
error_text: []
asked_as: ["On Prime Day the account lead asked a specialist to check every client campaign hourly for out-of-budget status and raise budgets by an ACOS-based tier, because event traffic drains daily budgets earl"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/011-understand-budget-rules-GNSMLANWNF344YBE.md", "Advertising Help After Login/articles/013-create-budget-rules-for-sponsored-ads-campaigns-G3HZWVWYE23DBR2V.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0299"
---

## Question

On Prime Day the account lead asked a specialist to check every client campaign hourly for out-of-budget status and raise budgets by an ACOS-based tier, because event traffic drains daily budgets early.

## Answer

On a peak event day, check campaign budget status at a fixed interval and raise budgets only on campaigns that have run out, sized by ACOS tier, and leave the rest alone. A schedule-based or performance budget rule can do the same automatically if it is set before the event. Decide the tier direction before the day: the thread doubled budgets on campaigns above the ACOS threshold, while the agency's Prime Day SOP doubles the campaigns below target ACOS, so confirm which applies with the account lead.

## Cause

Peak-event traffic multiplies clicks, so daily budgets set for normal days run out hours before the day ends and the campaign stops serving during the highest-revenue day of the period.

## Fix

1. On the event day, check every campaign's budget status in campaign manager at a fixed interval (the thread used hourly).
2. For each campaign that is out of budget, read its ACOS for the event period.
3. Raise the budget by a large step (the thread used doubling) or a small fixed step depending on which side of an ACOS threshold the campaign sits; the threshold the thread used was 60%.
4. Leave campaigns that still have budget unchanged.
5. Exclude any marketplace the account lead names as an exception; the thread excluded one marketplace without giving the reason.
6. Have a second person re-check budgets later in the day, since campaigns can run out again after a raise.

## Verify

No campaign shows an out-of-budget status during the event hours, and the raised campaigns' event-day ACOS stays within the goal you set.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/011-understand-budget-rules-GNSMLANWNF344YBE.md`
- First-party: `Advertising Help After Login/articles/013-create-budget-rules-for-sponsored-ads-campaigns-G3HZWVWYE23DBR2V.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds an hourly in-event out-of-budget check with ACOS tiers whose direction conflicts with the Prime Day SOP, which only covers pre-event budget raises and rules.
- Existing coverage: full (`Advertising Help After Login/articles/013-create-budget-rules-for-sponsored-ads-campaigns-G3HZWVWYE23DBR2V.md`, `Advertising Help After Login/articles/011-understand-budget-rules-GNSMLANWNF344YBE.md`).
