---
id: KC-0026
title: "Want to match an off-Amazon single-unit price by charging shipping: FBA offers cannot add a shipping fee, so price a multipack per unit instead"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Pricing; FBM shipping templates; Promotions (sale price)"
surface_verified: false
symptom_keywords: ["charge shipping on FBA listing", "add shipping fee FBA", "single unit price too low for fees", "match website price on Amazon", "multipack price per unit"]
error_text: []
asked_as: ["The client wanted to test the same low per-unit price it runs on its own website on a single-pack Amazon listing, and asked whether it could charge a shipping fee on top as the website does."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md", "Amazon Seller Help/articles/142-price-your-item-G62551.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0026"
---

## Question

The client wanted to test the same low per-unit price it runs on its own website on a single-pack Amazon listing, and asked whether it could charge a shipping fee on top as the website does.

## Answer

To match a low per-unit price from another channel, do not drop the single-pack below a viable margin and do not plan on a shipping surcharge for FBA, because FBA offers cannot add one. Charge shipping only on a seller-fulfilled offer through its shipping template, and expect paid shipping to cost conversion. The usual answer is a multipack priced at the target per-unit price, applied as a sale price or discount.

## Cause

A single-pack at the target price leaves too little margin after Amazon fees. An FBA offer cannot carry a separate shipping charge; only a seller-fulfilled offer can charge shipping through its shipping template, and the team expected paid shipping to hurt conversion.

## Fix

1. Check the single-pack margin after fees at the target price before testing it.
2. If the idea is to recover margin through a shipping charge, note that this only works on an FBM offer via the shipping template; an FBA offer cannot add one.
3. Prefer to keep the single-pack at its normal price and bring a multipack down to the target price per unit.
4. Apply the multipack price as a price discount or sale price (operator approval for the price change).

## Verify

The client agreed to keep the single-pack price and set the multipack to the target per-unit price through a price discount.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md`
- First-party: `Amazon Seller Help/articles/142-price-your-item-G62551.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: FBA pages cover free shipping and fees, but no source states that an FBA offer cannot carry a shipping charge or the multipack-per-unit alternative.
- Existing coverage: partial (`Amazon Seller Help/articles/113-amazon-business-fba-multi-unit-fulfillment-fee-discount-GMZ5WFTZHCM4Q4C5.md`, `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`).
