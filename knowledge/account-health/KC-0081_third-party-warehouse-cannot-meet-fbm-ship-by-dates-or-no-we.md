---
id: KC-0081
title: "Third-party warehouse cannot meet FBM ship-by dates or no weekend fulfilment: raise the default handling time"
kind: decision-aid
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Settings > Shipping Settings (default handling time); Account Health > Shipping Performance"
surface_verified: false
symptom_keywords: ["can we set no fulfilment on weekends", "ship-by deadlines too tight for warehouse", "late shipment rate warning email FBM", "increase handling time for all SKUs", "shipping performance warning longest shipping template"]
error_text: []
asked_as: ["The seller's outsourced fulfilment warehouse could not ship merchant-fulfilled orders within the ship-by dates Amazon set, and asked whether a setting stops Amazon counting weekends."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md", "MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0081"
---

## Question

The seller's outsourced fulfilment warehouse could not ship merchant-fulfilled orders within the ship-by dates Amazon set, and asked whether a setting stops Amazon counting weekends. In a later thread the seller received a shipping performance warning email although the slowest available shipping template was already in use.

## Answer

When an outsourced warehouse cannot ship merchant-fulfilled orders by the ship-by date, raise the default handling time in Shipping Settings so the promised ship-by date matches what the warehouse can actually do. Weigh the longer delivery promise against conversion. Check whether the account has an operating-days setting for weekends, and watch the late shipment rate afterwards because it counts toward account health.

## Cause

The ship-by date Amazon shows on a merchant-fulfilled order follows the offer's handling time. With a short default handling time, the warehouse's real processing time ran past the promised ship-by date, so shipment confirmations arrived late and the late shipment rate rose. The thread did not test whether template transit time or an operating-days setting changes the ship-by date. It used only the handling time.

## Fix

1. Confirm the warehouse's real order-to-confirmation time, including weekend and holiday gaps.
2. In Shipping Settings, raise the default handling time for all items so the ship-by date matches that real time. This lengthens the customer-facing delivery promise, so agree it with the account owner first.
3. Check whether Shipping Settings has an operating-days or weekend option for the account. The thread did not check this.
4. If the slowest shipping template is already in use and late shipments continue, ask the warehouse to confirm shipment inside the new handling window.
5. Watch the late shipment rate in Account Health > Shipping Performance over the following weeks.

## Verify

Ship-by dates on new orders in Manage Orders move out by the added handling days, and the late shipment rate in Account Health trends down; the thread reports the numbers improving after the change.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Also in: `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Handling time, not template transit time, moves the ship-by date, so raising the default handling time is the lever when an outsourced warehouse misses FBM ship-by dates or cannot work weekends.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
