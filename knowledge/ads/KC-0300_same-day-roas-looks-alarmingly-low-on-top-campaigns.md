---
id: KC-0300
title: "Same-day ROAS looks alarmingly low on top campaigns"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads Console > Portfolios and campaigns, today's date range"
surface_verified: false
symptom_keywords: ["ROAS very low today", "same day ROAS dropped", "campaigns bleeding today", "intraday ROAS check", "should we lower budget until ROAS recovers"]
error_text: []
asked_as: ["A stakeholder saw a portfolio's ROAS for the current day far below normal and asked whether campaigns needed closer intraday babysitting or a lower starting budget raised only when ROAS looked good."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/192-create-a-sponsored-products-campaign-GKLSYGFS2YD33FER.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0300"
---

## Question

A stakeholder saw a portfolio's ROAS for the current day far below normal and asked whether campaigns needed closer intraday babysitting or a lower starting budget raised only when ROAS looked good.

## Answer

Never judge or cut campaigns on same-day ROAS, because attributed sales arrive late and are credited back to the click date. Compare a completed day against the same weekday a week earlier and read ad ROAS together with TACOS. A falling ad ROAS with a flat or better TACOS means organic sales are carrying the account, not that ads are bleeding.

## Cause

Ad-attributed sales are credited to the date of the ad click and reach the console with a delay (Amazon states metrics can take up to 12 hours to populate, and purchases inside the attribution window keep arriving after the click). The current day's attributed sales are therefore incomplete, and the previous day's can still move, so same-day ROAS is understated.

## Fix

1. Do not judge campaigns on the current day's ROAS.
2. Compare a completed day with the same weekday one week earlier (ad ROAS and TACOS side by side).
3. Use TACOS to see whether organic sales offset a lower ad ROAS.
4. If the question is branded versus non-branded demand, compare Search Query Performance week over week, noting that it under-reports against total sales.
5. Act on bleeding targets only after their data window has settled.

## Verify

Re-check the same day a few days later: its attributed sales and ROAS rise as late conversions are credited.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/192-create-a-sponsored-products-campaign-GKLSYGFS2YD33FER.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source tells operators to stop reading same-day ROAS and to compare same-weekday ad ROAS with TACOS instead.
- Existing coverage: partial (`AdLabs Help/articles/004-bid-optimization-guide.md`).
