---
id: KC-0075
title: "FBM On-Time Delivery Rate far below target although shipping template promises a long delivery window"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Shipping Performance; Settings > Shipping Settings"
surface_verified: false
symptom_keywords: ["On-Time Delivery Rate below target", "OTDR low FBM", "promised delivery date shorter than shipping template", "Shipping Settings Automation", "SSA promise dates wrong"]
error_text: ["On-Time Delivery Rate"]
asked_as: ["A client operations lead saw the FBM On-Time Delivery Rate far below the target."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/136-get-started-with-multi-location-inventory-GYCAQ9XRL273EVDX.md", "Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0075"
---

## Question

A client operations lead saw the FBM On-Time Delivery Rate far below the target. The affected orders missed the promised delivery date, yet the shipping template was set to a several-business-day delivery window with one-day handling, and the promised dates did not match that configuration. They asked whether Shipping Settings Automation (SSA) caused it.

## Answer

When FBM orders miss promised dates that look shorter than your shipping template, check whether Shipping Settings Automation is on: with it enabled, Amazon sets the promise from its own estimate rather than your template. Turn it off if your carrier cannot meet the automated promise, then monitor the On-Time Delivery Rate as new orders roll in. Remember that a slow carrier is still the seller's problem, so align the template with real delivery times.

## Cause

Shipping Settings Automation was enabled, so Amazon calculated its own, shorter promised delivery dates instead of using the template's transit times; the carrier's actual delivery time exceeded those automated promises.

## Fix

1. Download the On-Time Delivery report from Shipping Performance and compare each late order's promised delivery date with the actual delivery date.
2. Open Settings > Shipping Settings > Shipping templates and check whether Shipping Settings Automation is on; if it is, promised dates come from Amazon's estimate, not the template's transit times.
3. Check whether any ASINs on that template use Multi-location inventory, which requires SSA; turning SSA off removes that benefit.
4. If your carrier cannot meet the automated promise, turn off Shipping Settings Automation so the template's handling and transit times drive the promise (operator approval required before changing account settings).
5. Review your fulfilment partner's and carrier's real delivery times; the seller owns late deliveries even when the carrier is slow, and longer promises can lower conversion.
6. Recheck the On-Time Delivery Rate over the following weeks as new orders replace the late ones.

## Verify

Promised delivery dates on new FBM orders match the template window, and the On-Time Delivery Rate on Shipping Performance returns above target.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/136-get-started-with-multi-location-inventory-GYCAQ9XRL273EVDX.md`
- First-party: `Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links a low FBM On-Time Delivery Rate to Shipping Settings Automation overriding template transit times, which no captured page covers.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
