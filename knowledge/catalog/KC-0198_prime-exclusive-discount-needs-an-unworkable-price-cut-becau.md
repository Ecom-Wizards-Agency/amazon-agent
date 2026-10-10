---
id: KC-0198
title: "Prime Exclusive Discount needs an unworkable price cut because an unauthorized seller's low price set the benchmark"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Prime Exclusive Discounts"
surface_verified: false
symptom_keywords: ["prime exclusive discount required price too low", "hijacker lowest price prime discount", "win buy box from hijackers prime day", "prime exclusive discount not possible use coupon", "lowest price 30 days other seller discount"]
error_text: []
asked_as: ["With unauthorized sellers undercutting the listing, the seller asked whether to price below them for a month, and the team planned a Prime Day Prime Exclusive Discount to win the Featured Offer."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md"]
supersedes: []
contradicts: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md"]
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0198"
---

## Question

With unauthorized sellers undercutting the listing, the seller asked whether to price below them for a month, and the team planned a Prime Day Prime Exclusive Discount to win the Featured Offer.

## Answer

A price discount, including a Prime Exclusive Discount, must be at least 5% off the 30-day lowest non-promotional price customers paid across all sellers. An unauthorized seller's low price can therefore push the required promotional price below your margin, and an event setup screen may ask for a deeper cut. Read the benchmark and the required discount on the setup screen and compute the promotional price against cost and fees before you commit. When the discount is not viable, a Prime Member Coupon is the fallback, though it does not show a strike-through price.

## Cause

Amazon benchmarks price discounts against the 30-day lowest non-promotional price customers paid on the ASIN across all sellers. A low price an unauthorized seller had charged days earlier therefore became the reference. The discount the setup screen required off that price made the deal margin-negative: about 20% per the team's reading, while the captured help page states a 5% minimum. The Prime Exclusive Discount was therefore not viable.

## Fix

1. Before planning a price promotion on a listing with other sellers, check the lowest price the setup screen uses as its benchmark.
2. Compute the required promotional price from that benchmark and check it against product cost and fees.
3. If the result is below a viable margin, do not submit the Prime Exclusive Discount.
4. Use a Prime Member Coupon instead, accepting that it shows differently from a strike-through discount (submission needs operator approval).
5. Keep working the unauthorized-seller problem separately; a promotion does not remove the low benchmark.

## Verify

The coupon is active for the event and the listing's Featured Offer status is checked during the event.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties the first-party lowest-price benchmark to the unauthorized-seller case and names the coupon fallback, and records the thread's 20% figure against the page's 5%.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
