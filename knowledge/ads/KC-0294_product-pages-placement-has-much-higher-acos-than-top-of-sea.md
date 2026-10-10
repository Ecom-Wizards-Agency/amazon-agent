---
id: KC-0294
title: "Product pages placement has much higher ACOS than top of search but its bid adjustment is already 0%"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["product pages high ACOS", "placement modifier already 0", "shift budget to top of search", "placement rebalancing", "rest of search product pages ACOS"]
error_text: []
asked_as: ["In a Sponsored Products account, product pages placements ran at several times the ACOS of top of search, yet the product pages placement adjustments were already at 0%, so there was nothing to lower."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/007-understand-bid-adjustments-in-sponsored-ads-GQ4R4FR4H56JL6V8.md", "Advertising Help After Login/articles/009-adjust-sponsored-products-bids-GYYZVM7LGSRYGWV5.md"]
related_sops: []
supersedes: []
contradicts: ["AdLabs Help/articles/002-placement-bidding-adjustments.md"]
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0294"
---

## Question

In a Sponsored Products account, product pages placements ran at several times the ACOS of top of search, yet the product pages placement adjustments were already at 0%, so there was nothing to lower.

## Answer

Placement adjustments are increase-only, so a high-ACOS Product pages placement already at 0% cannot be cut directly. Shift spend by raising the Top of search adjustment on the best-converting campaigns, and lower the base bid at the same time if Product pages spend itself must fall. Test an Amazon Business adjustment where that placement converts well, and recheck placement ACOS after one to two weeks.

## Cause

Placement bid adjustments only increase the base bid for a placement; they cannot go below 0%. Once Product pages is at 0%, it cannot be cut directly. The levers are to raise the adjustment on the better-converting placements, or to lower the base bid and raise the Top of search adjustment so the effective Top of search bid holds while Product pages bids fall.

## Fix

1. Pull placement performance per campaign (Bid adjustments tab or the placement report) and compare ACOS for Top of search, Rest of search, Product pages and Amazon Business.
2. Confirm the Product pages adjustment is already 0%.
3. Raise the Top of search adjustment on the best-converting campaigns and the auto campaign. Raising it alone adds Top of search spend but does not cut Product pages spend; to reduce Product pages bids, lower the base bid and raise Top of search to compensate. Bid changes need operator approval.
4. Where Amazon Business placements show low ACOS, add a modest Amazon Business adjustment as a test on the highest-spending campaigns.
5. Review placement ACOS again after one to two weeks and reduce boosts that raise ACOS without adding sales.

## Verify

Share of spend moves toward Top of search and blended campaign ACOS falls in the next placement report.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/007-understand-bid-adjustments-in-sponsored-ads-GQ4R4FR4H56JL6V8.md`
- First-party: `Advertising Help After Login/articles/009-adjust-sponsored-products-bids-GYYZVM7LGSRYGWV5.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: When product pages ACOS is high and its adjustment is already 0%, shift spend by boosting Top of search on the best converters and testing Amazon Business.
- Existing coverage: full (`AdLabs Help/articles/002-placement-bidding-adjustments.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`, `Advertising Help After Login/articles/009-adjust-sponsored-products-bids-GYYZVM7LGSRYGWV5.md`, `Advertising Help After Login/articles/232-understand-sponsored-products-off-amazon-advertising-GYTD2Z3SYMAAMVXA.md`).
