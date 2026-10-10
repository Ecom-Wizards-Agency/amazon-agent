---
id: KC-0284
title: "Some orders show a referral fee and others show none: how is the referral fee calculated?"
kind: diagnosis
topic: reporting
status: reviewed
skills: [amazon-reporting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central payments and order transaction view"
surface_verified: false
symptom_keywords: ["how is the referral fee calculated", "some orders have no referral fee", "referral fee missing on order", "Amazon commission per sale", "referral fee credited back on refund"]
error_text: []
asked_as: ["A client stakeholder could not work out how the referral fee is calculated and saw that some orders carry one while others do not."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md", "Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md", "Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0284"
---

## Question

A client stakeholder could not work out how the referral fee is calculated and saw that some orders carry one while others do not.

## Answer

Treat the referral fee as Amazon's commission: a category percentage of what the buyer actually pays for the item, with a per-item minimum. When an order shows no fee, first check whether it is a refund (fee credited back minus the Refund Administration Fee), not yet settled, a zero-value order, a multi-item order, or an order where a New Seller Incentives brand bonus covered the whole fee, before assuming an error. Use the Referral Fee Preview report to see the expected fee per listing at the current price.

## Cause

The referral fee is a category-specific percentage of the item's sales proceeds: the item price plus any shipping or gift wrap the seller charges. How taxes count follows the store's tax policies, and Amazon's own examples use the price before taxes. The fee schedule sets a per-item minimum, and the fee moves with the actual selling price, including coupon or deal discounts. Rows without a new fee are usually refunds (the fee is credited back minus a Refund Administration Fee), orders not yet settled, zero-value replacement or promotional orders, multi-item orders where the fee sits on another line, or orders where a New Seller Incentives brand bonus covers the whole fee, so no referral fee line is shown. The thread explained the mechanism but did not check the specific orders.

## Fix

1. Look up the product's referral fee category and percentage on the Selling on Amazon fee schedule, or download the Referral Fee Preview report from Inventory reports.
2. Multiply the rate by the item's actual sales proceeds (price after coupons or deals, plus seller-charged shipping) and apply the per-item minimum.
3. For each order without a fee, check whether it is a refund row, an order not yet settled, a zero-value replacement or promotional order, a multi-item order with the fee on another line, or an order where a New Seller Incentives brand bonus covered the whole fee.
4. If an order fits none of these, collect the order IDs and compare them in the transaction view before raising anything with Seller Support (case submission needs operator approval).

## Verify

The recomputed fee for a sample of settled orders matches the referral fee line in the transaction view, and every order without a fee falls into one of the listed cases.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`
- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- First-party: `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Lists the practical reasons an order shows no referral fee, which the agreement text does not spell out.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`).
