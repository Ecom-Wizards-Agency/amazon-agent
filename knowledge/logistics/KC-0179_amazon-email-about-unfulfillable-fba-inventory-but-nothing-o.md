---
id: KC-0179
title: "Amazon email about unfulfillable FBA inventory but nothing obvious to remove: check the unfulfillable reason and create a removal or disposal order"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > Manage FBA Inventory (Unfulfillable); Create removal order"
surface_verified: false
symptom_keywords: ["unfulfillable inventory email", "cannot find inventory to remove", "damaged and defective units at FBA", "remove or dispose unfulfillable units", "why are units unfulfillable"]
error_text: []
asked_as: ["The seller received an Amazon email about unfulfillable inventory and could not find anything to remove, and asked why the units could not go back into sellable stock."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md", "MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md", sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0179"
---

## Question

The seller received an Amazon email about unfulfillable inventory and could not find anything to remove, and asked why the units could not go back into sellable stock.

## Answer

When Amazon reports unfulfillable inventory, open the unfulfillable inventory view and read the reason for each unit; damaged and defective units are routine and cannot return to sellable stock. Ask the client whether to return the units to an address they name or dispose of them, and create the removal order only with approval. If you enable automatic removal, choose return to seller rather than disposal unless the client approves disposal in writing.

## Cause

Some units at the fulfillment center were classified unfulfillable. The screenshot split them between damaged and defective units, which cannot return to sellable stock. The thread does not quote the Amazon email, so the exact notice wording is unknown.

## Fix

1. Open the unfulfillable inventory view and read the unfulfillable reason per unit (for example damaged or defective).
2. Ask the client whether to return the units or dispose of them.
3. For a return, get the destination address from the client before creating the order.
4. With operator approval, create the removal order for the unfulfillable quantity.
5. Optionally set automatic removal for unfulfillable inventory to return to seller with an approved address. Keep disposal and liquidation off unless the client approves them in writing (see the new-client disposal-prevention draft).

## Verify

The unfulfillable quantity drops to zero once the removal order completes, and the removal order shows the expected units and destination.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`
- Also in: `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The removal SOPs cover creating the order; this adds the triage path from an unfulfillable-inventory email to the per-unit reason before choosing removal or disposal.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`).
