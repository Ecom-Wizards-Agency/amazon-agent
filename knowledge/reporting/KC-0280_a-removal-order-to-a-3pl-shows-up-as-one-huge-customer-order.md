---
id: KC-0280
title: "A removal order to a 3PL shows up as one huge customer order and inflates COGS in the daily P&L"
kind: diagnosis
topic: reporting
status: reviewed
skills: [amazon-reporting, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > Removal orders; third-party P&L / profit tool order breakdown"
surface_verified: false
symptom_keywords: ["removal order counted as sale in P&L", "huge COGS spike one order", "removal order ID in orders report", "cost of removal to 3PL", "S01 order ID removal"]
error_text: []
asked_as: ["The client finance lead saw one order in the daily order breakdown that added a very large COGS amount, suspected it was the transfer of a whole product line from FBA to the client's 3PL, and asked ho"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0280"
---

## Question

The client finance lead saw one order in the daily order breakdown that added a very large COGS amount, suspected it was the transfer of a whole product line from FBA to the client's 3PL, and asked how much that transfer would finally cost.

## Answer

If one order suddenly adds COGS equal to many units at full product cost, check whether it is a removal order to your own warehouse. Find the matching removal order in Seller Central > Inventory > Removal orders, exclude the order from the P&L, and track the real cost as per-item removal fees. Give the final cost only after the removal order completes, when the Removal Order Detail Report shows the fees charged.

## Cause

A removal order shipping FBA stock to the seller's own warehouse appeared in the order data under an Amazon order ID that corresponded to the removal order; the removal order itself carried a different ID. The P&L tool booked every removed unit as one customer order and charged the full inventory cost (units times unit COGS) as COGS. The real Amazon cost of the transfer is the per-item removal fees, which depend on size and weight.

## Fix

1. Divide the unexpected COGS by the order quantity; if the result equals the product's unit cost, the tool counted inventory value, not a fee.
2. In Seller Central > Inventory > Removal orders, find the removal order that corresponds to the order in the P&L (match the date, SKU, quantity and destination; the removal order ID may differ from the order ID) and read its destination, status and requested, shipped, cancelled and pending quantities.
3. Exclude that order from the internal P&L so the inventory transfer is not counted as a sale with COGS.
4. Estimate the real cost from the per-item removal fees by size and weight, and report the final cost after the removal order completes, using the Removal Order Detail Report, which lists the fees charged for completed removal orders.

## Verify

After excluding the removal order, the day's COGS returns to normal levels, and once the removal completes the Removal Order Detail Report shows the removal fees charged for it.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source explains that a removal order to the seller's 3PL can appear in a profit tool as one customer order and inflate COGS; the removal SOPs cover creating and reporting removals only.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`, `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`).
