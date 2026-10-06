---
id: KC-0004
title: "FBA capacity limit used up for the month: submit a Capacity Manager request (reservation-fee bid) or ship to AWD"
kind: procedure
topic: logistics
status: draft
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Shipments > Capacity Monitor > Capacity Manager; Send to Amazon; AWD"
surface_verified: false
symptom_keywords: ["FBA capacity limit reached", "capacity manager request", "capacity bid reservation fee", "no capacity to send to FBA", "AWD instead of FBA capacity"]
error_text: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-09
provenance: "ledger:KC-0004"
---

## Question

The client's operations team needed to send a new multipack SKU from a 3PL into FBA but had already used the month's FBA capacity. They had submitted a capacity bid and asked for other options.

## Answer

When FBA capacity is used up, submit a Capacity Manager increase request at once. Requests are reviewed several times a week, and one was approved within a day for the current month, so the help page's next-month framing does not always apply. Use AWD as the fallback, because it replenishes FBA as space frees up. Close to Q4, expect slower AWD-to-FBA transfers and prefer a capacity request when the stock must sell soon.

## Cause

The monthly FBA storage-type capacity limit was fully used, so Send to Amazon would not accept more volume until the limit was raised.

## Fix

1. Check utilization against current and upcoming limits in Capacity Monitor.
2. In Capacity Manager, submit a capacity increase request for the storage type and period with the requested cubic feet and a maximum reservation fee per cubic foot (the capacity bid). The bid commits a fee and needs operator approval.
3. Fallback: send the stock to AWD, which replenishes FBA automatically when there is demand and space.
4. Close to Q4, plan for slower AWD-to-FBA transfers and FC receiving, and prefer a capacity request when the stock must sell soon.
5. Once Amazon approves the extra capacity, create the shipment in Send to Amazon.

## Verify

Amazon approved the extra capacity about one day after the request, and the client created the shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The AWD fallback, the Q4 caveat on AWD-to-FBA speed and the observed next-day approval are not in the existing SOP or help page.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md`, `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`).
