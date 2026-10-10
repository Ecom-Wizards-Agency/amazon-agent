---
id: KC-0111
title: "Subscribe & Save subscriptions look lost after an FBA stockout or removal: deliveries are paused, not cancelled, and resume when stock returns"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-reporting, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Subscribe & Save performance dashboard / report"
surface_verified: false
symptom_keywords: ["[\"subscribe and save subscriptions paused\", \"S&S subscribers lost after stockout\", \"subscriptions paused out of stock\", \"subscribe and save after removal order\", \"transfer subscribers to new SKU\"]"]
error_text: []
asked_as: ["The client feared that Subscribe & Save subscriptions had been cancelled while its FBA stock was out and being removed."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0111"
---

## Question

The client feared that Subscribe & Save subscriptions had been cancelled while its FBA stock was out and being removed. The agency suggested a new SKU and a subscriber transfer as the only fix.

## Answer

When stock runs out, Amazon pauses Subscribe & Save deliveries rather than cancelling subscriptions, and deliveries resume when you send inventory or fix the price. Restock the same SKU before transferring subscribers to a new one. Keep stockouts short, because products that fail the program's performance bar, which counts inventory levels, are removed and their subscriptions cancelled.

## Cause

Amazon pauses Subscribe & Save deliveries when the seller does not have enough inventory to fulfil upcoming orders; a pause alone does not cancel the subscriptions. Separately, the program's performance reviews weigh the seller's ability to keep inventory high enough, and enrolled products that fail the minimum bar are removed from the program with subscriptions cancelled, so long or repeated stockouts carry a separate risk.

## Fix

1. ["1. Check the Subscribe & Save report: paused subscriptions on an out-of-stock SKU are not cancelled.", "2. Send inventory back into FBA on the same SKU, or finish the pending removal and then restock, rather than creating a new SKU.", "3. Recheck the subscription count once stock is live; deliveries resume on their own."]

## Verify

After restock the active subscription count matches the pre-stockout level.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The first-party page states the pause rule; new is the field confirmation that subscriptions resumed without loss after restock, so a new SKU and subscriber transfer were unnecessary.
- Existing coverage: full (`Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`, `MAG SOPs/README.md`).
