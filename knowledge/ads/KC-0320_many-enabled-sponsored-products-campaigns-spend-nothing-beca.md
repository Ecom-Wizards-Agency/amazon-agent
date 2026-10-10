---
id: KC-0320
title: "Many enabled Sponsored Products campaigns spend nothing because bids sit far below the suggested range or a tool multiplier cuts them"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [DE, IT, ES]
marketplace_inferred: false
surface: "Amazon Ads Console > Sponsored Products > campaign targeting (suggested bid range, placement adjustments); bid-management tool settings"
surface_verified: false
symptom_keywords: ["zero spend campaigns", "enabled campaigns no impressions", "campaigns not spending budget", "bids too low to win auctions", "placement multiplier below 1 cutting bids"]
error_text: []
asked_as: ["An account had a large share of enabled Sponsored Products campaigns spending nothing, while nominal daily budgets far exceeded actual spend; the team asked why these campaigns stayed dark and how to "]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/006-set-bids-in-a-sponsored-products-campaign-GTMXQWASBRZTHLF2.md", "Advertising Help After Login/articles/001-understand-bidding-GDS2E64R9GQ35768.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0320"
---

## Question

An account had a large share of enabled Sponsored Products campaigns spending nothing, while nominal daily budgets far exceeded actual spend; the team asked why these campaigns stayed dark and how to activate them without overspending.

## Answer

When many enabled campaigns spend nothing, check bids before budgets. Targets bidding well below Amazon's suggested range tend to lose the auction however large the budget is. Also check any bid-management tool for multipliers below 1.0, which silently cut every bid. Raise starved bids in small paced steps with caps, and diagnose anything still dark after a week for eligibility or volume problems instead of bidding higher.

## Cause

Targets were starved. In the zero-spend campaigns, targets with under 100 impressions in 30 days sat below Amazon's suggested bid range and lost the auctions. In a set of campaigns, a bid-management tool also applied an internal placement multiplier between 0.4 and 0.8, which silently cut every bid by 20 to 60 percent. Budget was not the constraint: campaigns with large nominal budgets spent a small fraction of them because their bids lost. (The 'about a third of suggested-high' figure in the thread describes the core rank keywords, which were serving with low top-of-search share, not the zero-spend campaigns.)

## Fix

1. List enabled campaigns and targets with near-zero impressions over the last 30 days.
2. Compare each starved target's bid with Amazon's suggested bid range in the Ads Console.
3. Check any bid-management tool for placement or bid multipliers below 1.0 and reset them to 1.0 where they were not intended.
4. Raise starved bids in paced steps (the team settled on about +20 percent per step, larger only when far below the suggested range) with a per-market cap; apply only after operator approval.
5. Leave budgets as they are; let bids carry the activation and raise budgets only for campaigns that start converting.
6. After about seven days, diagnose anything still at zero impressions individually (eligibility, moderation, duplicate targeting, no search volume) instead of raising bids further.

## Verify

Formerly zero-spend campaigns start recording impressions and spend within one to two days of the bid change; the number of serving campaigns rises in the daily check.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/006-set-bids-in-a-sponsored-products-campaign-GTMXQWASBRZTHLF2.md`
- First-party: `Advertising Help After Login/articles/001-understand-bidding-GDS2E64R9GQ35768.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The existing unit covers campaigns that stop delivering despite healthy bids; this card covers campaigns that never serve because bids sit far below the suggested range or a tool multiplier cuts them.
- Existing coverage: full (`knowledge/ads/KC-0009_sponsored-products-campaigns-suddenly-stop-delivering-impres.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`).
