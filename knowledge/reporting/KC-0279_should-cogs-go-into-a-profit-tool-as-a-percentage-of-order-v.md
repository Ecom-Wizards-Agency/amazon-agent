---
id: KC-0279
title: "Should COGS go into a profit tool as a percentage of order value or as a fixed per-unit cost?"
kind: procedure
topic: reporting
status: reviewed
skills: [amazon-reporting]
marketplaces: [US]
marketplace_inferred: true
surface: "Sellerboard product cost settings"
surface_verified: false
symptom_keywords: ["Sellerboard COGS percentage", "how to set COGS in Sellerboard", "FBM costs missing in profit", "profit share calculation Amazon", "COGS per unit or percent"]
error_text: []
asked_as: ["The client wanted to set COGS in the profit tool as a flat percentage of revenue that varied with units per order and cart value, while the tool needs per-unit costs per SKU."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0279"
---

## Question

The client wanted to set COGS in the profit tool as a flat percentage of revenue that varied with units per order and cart value, while the tool needs per-unit costs per SKU.

## Answer

Enter COGS in a profit tool as a fixed per-unit amount per SKU (product plus freight to Amazon), never as a percentage of order value. The tool already deducts Amazon's FBA and referral fees, so only costs Amazon does not see belong there. Add FBM pick, pack and shipping as a separate per-order cost, and backdate to the start of the reporting period.

## Cause

The profit tool multiplies a per-unit COGS by units sold and deducts Amazon's own fees (referral, FBA fulfillment) separately. A percentage derived from another channel's economics, such as quantity-break discounts in the seller's own shop, does not match Amazon orders and misstates cost there. FBM pick, pack and shipping costs are not in Amazon's data, so they must be added separately.

## Fix

1. Ask the client for a per-unit product cost plus inbound freight to the Amazon country, per SKU, in currency rather than as a percentage.
2. If cost varies batch to batch, add a small buffer so it averages out month to month.
3. Enter the value per SKU in the profit tool's cost settings. Use batch-dated costs if freight changes per shipment.
4. For FBM orders, add a per-order fulfillment cost (warehouse pick and pack plus average shipping to the customer), since Amazon charges only its marketplace fee there.
5. Backdate the new costs to the start of the reporting period you need corrected.

## Verify

Recalculated net margin for a past month lands near the margin in the client's own P&L for the Amazon channel.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Profit tools need per-unit COGS in currency, not a percentage of order value, with FBM fulfillment added separately because Amazon fees are already deducted.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`, `AdLabs Help/articles/003-rpc-bidding-formula-acos-goals.md`).
