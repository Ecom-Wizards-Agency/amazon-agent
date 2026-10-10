---
id: KC-0077
title: "FBM Late Shipment Rate stays above 4% until handling time is raised"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Settings > Shipping Settings > shipping template handling time; Account Health > Late Shipment Rate"
surface_verified: false
symptom_keywords: ["late shipment rate too high", "LSR above 4 percent", "increase handling time FBM", "account flagged risky late shipments", "how to lower late shipment rate"]
error_text: ["Late Shipment Rate"]
asked_as: ["The client saw the Late Shipment Rate improve over the last 10 days but still sit well above the Amazon threshold over 30 days, and asked what else could be done."]
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
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0077"
---

## Question

The client saw the Late Shipment Rate improve over the last 10 days but still sit well above the Amazon threshold over 30 days, and asked what else could be done.

## Answer

When FBM orders are confirmed late, extend handling time so the ship-by date matches what the warehouse can really do, then give the rolling window time to recover. Step up by one day at a time and check the rate after each change. Account-level risk flags can lag behind the metric itself.

## Cause

Not fully established in the thread; inferred from the fix. Orders were confirmed after their ship-by date because the promised handling time was shorter than the fulfilment operation needed. A longer handling time moves the ship-by date to one the operation can meet.

## Fix

1. Raise the handling time in the shipping template (or per-SKU handling time) to two days; this had already been done in the backend.
2. Wait for the rolling window to refresh; the rate improves gradually as old late orders age out.
3. If the rate is still too high, raise handling time to three days.
4. Keep confirming shipment in Seller Central on or before the ship-by date.

## Verify

The Late Shipment Rate in Account Health drops below 4%; in this case it fell below 4% while the account still showed an at-risk flag for a time.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Also in: `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The MAG late-shipment SOP already gives the 4% threshold and says to extend handling time for recurring late shipments; this card adds stepping handling time up one day at a time, the slow rolling-window recovery and the lag of the account-level risk flag behind the metric.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`).
