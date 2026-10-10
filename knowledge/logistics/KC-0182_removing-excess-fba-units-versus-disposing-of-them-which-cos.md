---
id: KC-0182
title: "Removing excess FBA units versus disposing of them: which costs less?"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["removal vs disposal cost", "return or dispose fba inventory", "removal order fee per unit", "disposal fee same as removal"]
error_text: []
asked_as: ["The client asks whether to have excess FBA units returned or disposed of, given the cost per unit."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md", "MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0182"
---

## Question

The client asks whether to have excess FBA units returned or disposed of, given the cost per unit.

## Answer

Compare the current per-item removal and disposal fees before choosing, because Amazon charges both per item and they can be equal. When they are equal and the units are resellable, return them rather than destroy them. Confirm the destination and receiving capacity with the client before creating the removal order.

## Cause

Amazon charges a per-item fee for both removal (return) and disposal orders; in this case the per-unit fee was the same for both, so cost did not favour disposal.

## Fix

1. Look up the current per-item removal and disposal fees for the unit's size tier.
2. If the fees are equal, prefer a return removal order when the units are resellable, and arrange receiving with the warehouse that will take them.
3. Create the removal order only after the client confirms the destination address and receiving capacity (operator approval required).

## Verify

The removal order shows the expected per-item fee in its order details, and the receiving warehouse confirms it received the returned units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Existing pages cover how to create removal and disposal orders but not the decision rule of returning resellable units when both per-item fees are equal.
- Existing coverage: full (`knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`, `MAG SOPs/catalog/catalog-sop-negative-feedback-removal.md`).
