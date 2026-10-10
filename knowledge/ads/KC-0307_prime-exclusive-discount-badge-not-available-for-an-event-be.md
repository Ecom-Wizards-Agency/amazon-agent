---
id: KC-0307
title: "Prime Exclusive Discount badge not available for an event because the product star rating is below the event threshold"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Advertising > Prime Exclusive Discounts / Price discounts"
surface_verified: false
symptom_keywords: ["no prime badge prime day", "prime exclusive discount rating requirement", "PED minimum star rating", "prime exclusive discount not eligible rating", "prime deal badge missing"]
error_text: []
asked_as: ["Before a Prime event the ads manager found that the product would not get the Prime Exclusive Discount badge because of its rating, and the team discussed what the minimum rating now is."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md"]
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0307"
---

## Question

Before a Prime event the ads manager found that the product would not get the Prime Exclusive Discount badge because of its rating, and the team discussed what the minimum rating now is.

## Answer

Check the event-specific eligibility criteria for Prime Exclusive Discounts, including the minimum star rating, in the Price Discounts tool well before each Prime event; do not carry over a number from an earlier event. The always-on minimum is three stars, but events can apply stricter criteria, and the team noticed no announcement of a change; for one event the team understood the minimum to be 4.0 stars. Products below the event threshold need a different promotion type.

## Cause

The product's star rating was below the minimum the team believed applied to Prime Exclusive Discounts for this event: 4.0 stars, according to a team statement. The thread cites no Amazon page or tool screen. Team members disagreed on the earlier threshold (one recalled 3.8, another 3.5). The captured Price discounts help page sets a three-star product minimum at all times and says events can apply stricter criteria, which are shown in the Price Discounts tool.

## Fix

1. Several weeks before a Prime event, open the Price Discounts tool and read the eligibility criteria shown for that event, including the minimum product star rating.
2. Compare each planned product's current star rating to that threshold.
3. If a product is below it, plan another promotion type such as a standard price discount or coupon (approval needed before submitting any promotion). Grow ratings for later events only through Amazon-compliant means such as Request a Review or Vine, never incentivised reviews.
4. Rebalance the event plan for ads and pricing around the promotion type the product can actually run.

## Verify

The Price Discounts tool accepts the product for the Prime Exclusive Discount for the event, or the fallback promotion shows as scheduled without errors.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The captured help page only gives the always-on three-star minimum; the event-specific Prime Exclusive Discount rating threshold (seen at 4.0, previously 3.5) and the advice to check it per event are new.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
