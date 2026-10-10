---
id: KC-0127
title: "Multi-destination Send to Amazon plan: box labels cannot be generated until every shipment in the plan is packed and its packing information submitted"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Pack individual units / box packing information > Confirm shipping > Print box labels"
surface_verified: false
symptom_keywords: ["cannot print FBA box labels", "labels not available multi destination shipment", "3PL packed only some destinations", "packing information not complete for all shipments", "carton quantities differ from planned"]
error_text: []
asked_as: ["An account manager handed over a multi-destination FBA transfer from a third-party warehouse to a teammate."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0127"
---

## Question

An account manager handed over a multi-destination FBA transfer from a third-party warehouse to a teammate. The warehouse had packed some destinations, its packing files disagreed with the planned quantities, and the warehouse was waiting for carton labels, pallet labels and pickup routing.

## Answer

When a third-party warehouse packs a multi-destination Send to Amazon plan in stages, do not promise labels after the first destinations are packed. Collect and submit packing information for every shipment in the plan first, because the workflow only reaches Confirm shipping and Print box labels after packing is confirmed. Reconcile packed quantities against the plan before submitting, and decide short SKUs quickly rather than holding the whole plan.

## Cause

In the Send to Amazon workflow, packing information is entered per pack group for the whole plan; the workflow moves on to Confirm shipping and Print box labels only after the packing information is confirmed. Because only part of the destinations had been packed, official labels for the plan could not be generated yet.

## Fix

1. Reconcile the warehouse's packing files against the plan: confirm which tab or file describes the physical cartons, list every SKU whose packed quantity differs from the planned quantity, and confirm gross pallet weights including pallet and wrapping.
2. Decide each short SKU: wait for replenishment, or ship without the missing units so the shipment is not held up; record the decision.
3. Submit the packing information for the destinations that are packed so the packing data reflects what the warehouse physically packed.
4. Send the warehouse the packing templates for the remaining destinations and get their carton contents, dimensions and weights.
5. Once every shipment in the plan has complete packing information, confirm shipping (operator approval: this accepts placement and carrier charges), then print box labels and pallet labels and give the warehouse the carton-to-label mapping and the bill of lading.

## Verify

Send to Amazon shows packing information confirmed for every shipment in the plan and the Print box labels step becomes available; label count matches the carton count the warehouse reported.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP gives the step order, but not that a staged multi-destination plan blocks every label until all shipments are packed, nor the reconcile-then-decide-short-SKUs routine for a 3PL handover.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`).
