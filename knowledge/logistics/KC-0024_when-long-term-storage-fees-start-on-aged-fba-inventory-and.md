---
id: KC-0024
title: "When long-term storage fees start on aged FBA inventory and how to estimate them"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Reports > Fulfillment > Long-Term Storage Fee Charges / FBA Inventory age"
surface_verified: false
symptom_keywords: ["when are long-term storage fees charged", "aged inventory surcharge estimate", "181 days storage fee", "overstock storage fee projection"]
error_text: []
asked_as: ["A seller with an overstocked variation asked when long-term storage fees would first be charged and how much to expect."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0024"
---

## Question

A seller with an overstocked variation asked when long-term storage fees would first be charged and how much to expect.

## Answer

Long-term storage fees are charged monthly on the 15th once units pass the 181-day threshold, by cubic feet per age bucket. Project the remaining units into each bucket from current sales velocity to see when the expensive buckets start. Weigh that cost against the margin lost on a discount before you clear stock early.

## Cause

Long-term storage fees are assessed monthly on the 15th on inventory that has passed the aging threshold; the charge scales with cubic feet in each age bucket, with a higher rate in the oldest buckets.

## Fix

1. Find the date each batch passes the 181-day age threshold.
2. Expect the first charge on the next 15th after that date.
3. Compute cubic feet per unit (L x W x H in inches / 1728) and multiply by the projected units left in each age bucket.
4. Apply the current rate for each bucket from the fee page; rates rise sharply in the oldest buckets and peak months.
5. Compare the projected fee with the profit cost of a promotion or removal to clear the stock before the oldest buckets.

## Verify

The Long-Term Storage Fee Charges report or the Transaction view shows the first charge on the projected 15th.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Sources name the fee and its reports but not the 15th-of-month timing after 181 days or the cubic-foot bucket projection a seller can run ahead of time.
- Existing coverage: full (`Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md`).
