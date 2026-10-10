---
id: KC-0285
title: "Per-unit Amazon fees change when a coupon or promotion runs: the referral fee is a percentage of the actual sale price"
kind: rule
topic: reporting
status: reviewed
skills: [amazon-reporting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central Manage inventory 'Estimated fee per unit sold' widget / Fee Preview report"
surface_verified: false
symptom_keywords: ["estimated Amazon fees per order", "why did the referral fee drop", "fees lower with coupon", "per-unit fee estimate", "referral fee percentage of price"]
error_text: []
asked_as: ["The client asked for the estimated fees, shipping cost and other costs Amazon charges on each order."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md", "Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md", "Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0285"
---

## Question

The client asked for the estimated fees, shipping cost and other costs Amazon charges on each order.

## Answer

When a stakeholder asks what Amazon charges per order, give the total estimated fee per unit and split it into the referral fee and the fulfillment fee. The referral fee is a category percentage of what the buyer actually pays, so coupons and promotions lower it. The fulfillment fee is not price-based and does not shrink with a discount. Expect per-order fees to differ from the full-price estimate whenever a discount runs, and check one discounted order's transaction detail to confirm.

## Cause

Amazon's per-unit fee for an FBA item is mainly the referral fee plus the FBA fulfillment fee. The referral fee is based on the Sales Proceeds of the transaction at the category rate on the Selling on Amazon Fee Schedule. The thread says a coupon or promotion lowers the referral fee because the buyer pays less. No local capture states the coupon case directly. The fulfillment fee is not a percentage of price, so it does not scale with a discount. The thread did not establish whether a discount can move an item into a different FBA fee tier.

## Fix

1. Open the 'Estimated fee per unit sold' widget on Manage inventory, or download the Fee Preview report from Fulfillment reports, and give the total estimated fee per unit for the SKU.
2. Split the total into the referral fee (category rate applied to the sale price) and the FBA fulfillment fee (set by Amazon's FBA fee table, not a percentage of price).
3. Explain that a sale under a coupon or promotion has a lower sale price and so a lower referral fee, which means per-order fees differ from the full-price estimate. Confirm this on a real discounted order before relying on it.
4. Any reply to the client is an external message and needs operator approval before it is sent.

## Verify

Compare the referral fee on a full-price order with one sold under a coupon in the order's transaction detail; the referral fee should scale with the discounted item price.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`
- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- First-party: `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties the stakeholder question about per-order fees to the rule that coupons and promotions lower the referral fee, which the captured fee pages state only through a worked example.
- Existing coverage: partial (`Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/114-amazon-business-bulk-order-fee-discount-G2G7KPB963EMPEYD.md`, `Amazon Seller Help/articles/078-brand-referral-bonus-GL9HPJ34VBFP76HX.md`, `Amazon Seller Help/articles/131-merch-collab-fees-and-royalties-GVD6A7JWY484GRYF.md`).
