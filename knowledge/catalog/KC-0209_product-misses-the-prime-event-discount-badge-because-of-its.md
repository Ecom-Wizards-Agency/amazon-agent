---
id: KC-0209
title: "Product misses the Prime event discount badge because of its star rating; a fallback price discount stacks with an existing Subscribe & Save coupon"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Advertising > Price discounts; Coupons; Subscribe & Save"
surface_verified: false
symptom_keywords: ["no Prime badge because of rating", "Prime exclusive discount not eligible star rating", "event badge missing low rating", "price discount stacks with Subscribe and Save coupon", "backup discount for Prime event"]
error_text: []
asked_as: ["Ahead of a Prime event, the team found that several products would not get the Prime event badge because of their ASIN rating, and asked whether to fall back to a regular price discount and how that i"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md", "Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-set-up-a-coupon.md"]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0209"
---

## Question

Ahead of a Prime event, the team found that several products would not get the Prime event badge because of their ASIN rating, and asked whether to fall back to a regular price discount and how that interacts with an existing Subscribe & Save coupon.

## Answer

Check event discount eligibility in the Price Discounts tool early, because event criteria can differ from the standing three-star minimum, and a product that fails gets no event badge. If you fall back to a regular price discount, end any overlapping Subscribe & Save coupon first, since Amazon adds coupons and promotional discounts on top of Subscribe & Save discounts.

## Cause

In the thread, a product whose rating had dropped below four stars was shown as ineligible for the Prime event badge. The standing first-party rule is a three-star minimum for price discounts, and Amazon states that event criteria may change and are shown in the Price Discounts tool, so the thread does not establish the exact event threshold. Seller coupons and promotional discounts are added on top of Subscribe & Save discounts, so a regular price discount running next to a Subscribe & Save coupon lets shoppers stack both.

## Fix

1. In Seller Central > Advertising > Price Discounts, check the event eligibility for each product early and note which ones fail on rating.
2. For ineligible products, decide whether a regular (non-event) price discount is still worth running without the event badge (operator decision).
3. Before a regular price discount goes live, end any overlapping Subscribe & Save coupon so the two discounts do not stack below the intended price.
4. Creating or ending promotions and changing bids needs operator approval.

## Verify

The product page shows only the intended discounted price, and the Subscribe & Save coupon is no longer offered alongside it.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- First-party: `Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-set-up-a-coupon.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party pages state the rating floor and the stacking rule separately; the card joins them into an event fallback decision and records that the team saw a stricter cutoff than three stars.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
