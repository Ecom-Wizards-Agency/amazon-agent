---
id: KC-0219
title: "Promotion setup demands a higher minimum discount than the percentage the client asked for"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Advertising > Promotions (promotion type not named in the thread)"
surface_verified: false
symptom_keywords: ["promotion minimum discount higher than requested", "price discount minimum above requested percentage", "cannot set the requested promotion percentage", "minimum discount percentage price discount", "discount must be at least"]
error_text: []
asked_as: ["The client asked for a time-bound promotion at a set percentage, matching the discount on their own website, over two date windows."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md"]
related_sops: [docs/seller-central-procedures.md]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0219"
---

## Question

The client asked for a time-bound promotion at a set percentage, matching the discount on their own website, over two date windows. When the operator set it up, the Seller Central price discount flow only accepted a discount one percentage point higher than requested.

## Answer

When the promotion tool refuses the percentage the client asked for and shows a higher minimum, do not round down or submit silently. For price discounts a likely cause is Amazon's rule that a discount must be at least 5% off the 30-day lowest price, the current price and the reference price, so recent low prices raise the floor. Report the exact minimum to the client, get approval for the higher discount, then schedule it.

## Cause

Not established in the thread: the minimum appears only in a screenshot and the promotion type is not named. If it was a price discount, the first-party rules give a likely mechanism: the discount must be at least 5% off the 30-day lowest non-promotional price, at least 5% off the current price and at least 5% off any validated reference price, so a recent lower price can push the tool's minimum above a percentage taken off list price.

## Fix

1. Enter the requested discount in the price discount setup and read the minimum discount the tool shows for each product.
2. If the minimum is above the requested percentage, report the exact minimum to the client and ask whether to proceed at that level or skip the promotion (client approval required before submitting).
3. After approval, schedule the price discount for each date window at the approved percentage (operator approval required before submitting).
4. Send the client the confirmation that the discounts are scheduled.

## Verify

The promotion list shows each price discount as scheduled for the requested date windows at the approved percentage.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- Also in: `docs/seller-central-procedures.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The price discount page states the 5% thresholds but not the practical consequence that a requested percentage off list can be refused, or that the higher minimum needs client approval before scheduling.
- Existing coverage: full (`Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `MAG SOPs/catalog/catalog-sop-how-to-set-up-a-coupon.md`, `MAG SOPs/catalog/catalog-sop-creating-a-promo-code.md`, `Amazon Seller Help/articles/114-amazon-business-bulk-order-fee-discount-G2G7KPB963EMPEYD.md`).
