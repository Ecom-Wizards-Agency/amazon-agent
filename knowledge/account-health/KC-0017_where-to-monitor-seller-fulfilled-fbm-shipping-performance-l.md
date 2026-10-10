---
id: KC-0017
title: "Where to monitor seller-fulfilled (FBM) shipping performance: late shipment, cancellation and tracking metrics"
kind: reference
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Shipping Performance"
surface_verified: true
symptom_keywords: ["where to see FBM shipping performance", "late shipment rate dashboard", "FBM cancellation rate where", "shipping performance page seller central", "monitor merchant fulfilled delivery metrics"]
error_text: []
asked_as: ["A seller asked where in Seller Central they can monitor shipping performance for seller-fulfilled orders."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0017"
---

## Question

A seller asked where in Seller Central they can monitor shipping performance for seller-fulfilled orders.

## Answer

Monitor seller-fulfilled shipping on the Shipping Performance detail page under Performance > Account Health. It lists late shipments, pre-fulfillment cancellations and tracking defects with the orders behind each. Check it regularly when you fulfil any offers yourself, because a late shipment rate above target puts the account at risk.

## Cause

Not a fault. Seller-fulfilled shipping metrics sit on the Shipping Performance detail page under Account Health, not on the order pages.

## Fix

1. Open Seller Central > Performance > Account Health.
2. In the Shipping Performance section, open the detail view on the late shipment rate tab.
3. Review late shipment rate, pre-fulfillment cancel rate and the tracking metrics, and the defective orders listed under each.
4. Compare each rate against its target; the late shipment rate target in the MAG SOP is under 4% over 10 and 30 days.

## Verify

The Shipping Performance detail page shows the late shipment rate, cancellation rate and their defective orders for the seller-fulfilled channel.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Names the Account Health Shipping Performance detail page as the single place to monitor seller-fulfilled late shipment, cancellation and tracking metrics; the MAG SOP covers the target but not where to look.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
