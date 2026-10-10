---
id: KC-0013
title: "Offers keep reappearing in Pricing Health as above the Featured Offer or uncompetitive: which to price-match and which need a margin check"
kind: decision-aid
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Pricing > Pricing Health"
surface_verified: false
symptom_keywords: ["recurring pricing health alerts", "price above featured offer", "uncompetitive price competitive price threshold", "FBM offer flagged pricing health", "automated pricing not clearing pricing health"]
error_text: [uncompetitive, "Competitive Price Threshold", "Featured Offer"]
asked_as: ["Several offers had been recurring in Pricing Health for weeks."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0013"
---

## Question

Several offers had been recurring in Pricing Health for weeks. Some sat only slightly above the Featured Offer price; others were marked uncompetitive with an Amazon threshold far below the current price. Some flagged offers were enrolled in an automated pricing rule and still did not clear. Which offers should be lowered, and what does matching the deep threshold cost?

## Answer

Treat Pricing Health as two queues. Match offers that are only slightly above the Featured Offer price once the owner approves, and put offers with a deep Competitive Price Threshold gap through a per-unit margin check first, because fees, product cost and VAT do not fall with the price. Re-check after a few days, because Amazon moves the threshold and adds new offers. An FBM offer priced above its FBA twin will keep getting flagged.

## Cause

Pricing Health flags offers priced above the Featured Offer price or above Amazon's Competitive Price Threshold, and such offers can lose Featured Offer eligibility. Two patterns showed up: small gaps that a price match closes, and deep threshold gaps where matching would cut the price roughly in half. FBM offers that the seller deliberately prices a little above the FBA offer on the same product kept appearing as small gaps. Amazon also recalculates the threshold over time, so the flagged list changes between checks. Why the automated pricing rule did not clear the flags was not established in the thread.

## Fix

1. Open Pricing Health and list every flagged offer with its current price, the Featured Offer price and the Competitive Price Threshold.
2. Split the list: offers only slightly above the Featured Offer price (low-risk match) and offers whose threshold is far below the current price (margin review).
3. For deep-gap offers, calculate contribution per unit at the threshold price after referral fee, fulfillment fee, product cost and VAT before proposing any change.
4. Ask the account owner to approve the low-risk matches; stop before changing any price without that approval.
5. Apply only the approved price changes and record old and new price per SKU.
6. Leave deep-gap offers unchanged until a minimum acceptable margin is agreed; accept that they may stay ineligible for the Featured Offer.
7. Re-check Pricing Health after a few days: confirm matched offers cleared and look for newly added offers, since the threshold moves.
8. If FBM offers are intentionally priced above FBA offers, expect them to recur and decide with the owner whether to keep that price gap.
9. Audit any automated pricing rule whose enrolled SKUs still show in Pricing Health.

## Verify

The matched offers no longer appear in Pricing Health on the next check and the account's pricing status stays healthy.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a two-queue triage beyond KC-0011: match small Featured Offer gaps after approval, margin-check deep Competitive Price Threshold gaps, and expect FBM offers priced above FBA twins to recur.
- Existing coverage: full (`knowledge/account-health/KC-0011_buy-box-featured-offer-lost-to-a-pricing-health-uncompetitiv.md`, `Amazon Seller Help/articles/137-featured-offer-G37911.md`).
