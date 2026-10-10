---
id: KC-0230
title: "Which Subscribe and Save discount levels can a seller set, and what do repeat deliveries get?"
kind: reference
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Subscribe & Save > Manage Products"
surface_verified: false
symptom_keywords: ["subscribe and save minimum discount", "subscribe and save 20 percent", "S&S reorder discount max", "subscribe and save only some sizes", "list price comparison on subscription"]
error_text: []
asked_as: ["The client wanted to match its own shop's subscription offer on Amazon: a larger discount on the first subscription, a smaller one on rebills, only on some pack sizes, and asked whether the reference "]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0230"
---

## Question

The client wanted to match its own shop's subscription offer on Amazon: a larger discount on the first subscription, a smaller one on rebills, only on some pack sizes, and asked whether the reference retail price could be shown.

## Answer

Subscribe and Save is set per product: un-enroll the sizes that should not carry it and pick one seller-funded base tier (0, 5, 10, 15 or 20%) that applies on every delivery; Amazon may add 5% when a buyer groups five or more enrolled items. For a larger first-order discount, add a Subscribe & Save coupon, which applies to the first delivery of a new subscription. Check the current help page before quoting minimums or reorder caps.

## Cause

Subscribe and Save uses one seller-funded base discount per enrolled product, chosen from fixed tiers and applied on every delivery, plus an Amazon-funded extra 5% when a buyer has five or more enrolled products arriving together. A first-delivery-only discount is a separate Subscribe & Save coupon, not a second tier. The thread's informal claims of a 5% minimum and a 10% reorder cap do not match the help page.

## Fix

1. Open Subscribe & Save > Manage Products. Eligible replenishable products are auto-enrolled at the default enrollment discount (0% unless changed), so opt out of automatic enrollment or un-enroll the sizes that should not carry a subscription discount.
2. Choose the base funding tier per product: 0%, 5%, 10%, 15% or 20%. It applies on every delivery.
3. For a larger discount on the first delivery only, add a Subscribe & Save coupon, which is redeemable on the first delivery of a new subscription (creating the coupon needs operator approval).
4. Set any reference or list price separately; Subscribe and Save does not control a strike-through price comparison.

## Verify

Manage Products shows the selected tier on each enrolled product and the detail page shows the subscription price.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Records that informal agency claims of a 5% minimum and a 10% reorder cap conflict with the help page's fixed 0 to 20% tiers applied on every delivery.
- Existing coverage: full (`Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`, `MAG SOPs/catalog/merchandising-sop-amazon-list-price-mrsp.md`, `MAG SOPs/catalog/catalog-sop-how-to-set-up-a-coupon.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`).
