---
id: KC-0115
title: "Where to find and handle new FBM orders, and how often to check them"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Orders > Manage Orders > Unshipped (MFN)"
surface_verified: false
symptom_keywords: ["where are FBM orders", "how to ship merchant fulfilled orders", "unshipped orders page", "FBM orders not noticed"]
error_text: []
asked_as: ["A client's team member asked how to see and manage FBM orders to send to customers; orders had started arriving without anyone noticing."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/049-manage-orders-faq-G69124.md", "Amazon Seller Help/articles/042-search-orders-G28151.md", "Amazon Seller Help/articles/040-fbm-order-reports-G651.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md"]
supersedes: []
contradicts: []
observed: 2024-12
review_by: 2027-10
provenance: "ledger:KC-0115"
---

## Question

A client's team member asked how to see and manage FBM orders to send to customers; orders had started arriving without anyone noticing.

## Answer

FBM orders are shipped by the seller straight to the customer, not from Amazon's fulfillment centers. Find them under Orders > Manage Orders > Unshipped and check that view at least once a day, as Amazon recommends, instead of relying on the Sold, Ship Now email; the FBM Unshipped Orders report is an alternative. Confirm shipment for every order: Amazon cancels an order whose shipment is not confirmed within 30 days of the order date.

## Cause

Not a fault. FBM orders appear in Manage Orders under Unshipped and are shipped by the seller directly to the customer; nobody was checking that view.

## Fix

1. Open Orders > Manage Orders and filter Unshipped (seller-fulfilled orders).
2. Ship each order directly to the customer and confirm shipment with tracking.
3. Check Manage Orders at least once a day; do not rely on the Sold, Ship Now email alone.
4. Optionally use the FBM Unshipped Orders report.

## Verify

The Unshipped view is empty or every order in it is within its ship-by date.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/049-manage-orders-faq-G69124.md`
- First-party: `Amazon Seller Help/articles/042-search-orders-G28151.md`
- First-party: `Amazon Seller Help/articles/040-fbm-order-reports-G651.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms the first-party daily-check rule in the context of a team that missed its first FBM orders.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `Amazon Seller Help/articles/047-pending-orders-G40571.md`, `Amazon Seller Help/articles/106-fulfill-amazon-custom-orders-G201822830.md`, `Amazon Seller Help/articles/049-manage-orders-faq-G69124.md`, `Amazon Seller Help/articles/005-manage-orders-G28141.md`).
