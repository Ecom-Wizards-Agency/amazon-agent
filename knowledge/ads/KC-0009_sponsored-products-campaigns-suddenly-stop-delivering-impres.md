---
id: KC-0009
title: "Sponsored Products campaigns suddenly stop delivering impressions despite healthy bids, stock and Buy Box"
kind: diagnosis
topic: ads
status: draft
skills: [amazon-ads-console]
marketplaces: [US]
marketplace_inferred: false
surface: "Amazon Ads Console > Sponsored Products campaign delivery; Amazon Ads support case"
surface_verified: false
symptom_keywords: ["campaigns stopped getting impressions", "ad spend dropped overnight", "sponsored products not delivering", "impressions dropped suddenly", "duplicate campaign fixes delivery"]
error_text: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/019-copy-a-campaign-GPFGH67KMNLQ5TKU.md", "Advertising Help After Login/articles/006-set-bids-in-a-sponsored-products-campaign-GTMXQWASBRZTHLF2.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0009"
---

## Question

The client saw daily ad spend fall to a fraction of its usual level overnight. Several SP campaigns stopped delivering impressions although bids were adequate, and revenue dropped sharply.

## Answer

If SP campaigns lose most of their impressions overnight while bids, budget, stock, Buy Box and eligibility all check out, first confirm with hourly data that the drop came before any change of yours. Then open an Ads support case with specific campaign and ASIN examples and ask about backend caps. As a workaround, launch identical duplicates of the affected campaigns, because the fault can sit on the campaign entity. Bid increases and bidding-strategy changes mostly raise CPC without restoring delivery.

## Cause

Not established. Agency checks ruled out budgets, stock, advertised SKUs, Buy Box, eligibility, placements, schedules, invalid traffic and the agency's own bid changes; hourly data put the onset before those changes. Amazon first blamed low bids, then an SP video creative, and pausing it changed nothing. Duplicated copies of the affected campaigns delivered normally, which points to an Amazon-side fault tied to those campaign entities, but Amazon never confirmed it.

## Fix

1. Use native hourly campaign data to find the hour delivery fell and check whether any of your own changes came before it.
2. Rule out the usual causes: exhausted budget, out-of-stock or suppressed advertised SKU, lost Buy Box, ad ineligibility, placement or schedule rules, bid rules, recent negatives or exclusions.
3. Roll back recent bid, placement and exclusion changes on the affected campaigns, then compare a matched 24-hour window with the baseline. Changes need operator approval.
4. Testing a bidding-strategy change (Down only to Up and down) raised CPC without bringing back delivery.
5. Open an Amazon Ads support case with example ASINs and campaign IDs and ask directly whether a backend spending cap or delivery restriction sits on the account or on those campaigns.
6. If the originals still do not deliver, duplicate them with identical settings and launch the copies. Launching needs operator approval.

## Verify

The duplicated campaigns showed normal delivery and sales rose sharply the next day, but that day was a sales event, which confounds the result. Amazon gave no root cause and the case was still open.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/019-copy-a-campaign-GPFGH67KMNLQ5TKU.md`
- First-party: `Advertising Help After Login/articles/006-set-bids-in-a-sponsored-products-campaign-GTMXQWASBRZTHLF2.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source gives a delivery-loss troubleshooting sequence or the duplicate-campaign workaround.
- Existing coverage: none.
- Confidence is low: one thread, and the cited help pages cover copying a campaign and setting bids, not why delivery stopped.
