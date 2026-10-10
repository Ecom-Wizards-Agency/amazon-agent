---
id: KC-0124
title: "Pulling all FBA stock of a product back but the FBA offer keeps selling and part of the removal order shows cancelled: removals cannot target batches, and reserved units must be removed in later orders"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Inventory > Manage FBA Inventory > Create removal order; Reports > Removal Order Detail"
surface_verified: false
symptom_keywords: ["removal order partially cancelled", "FBA offer still winning buy box during removal", "remove specific batch from FBA", "reserved units not available for removal", "close FBA keep FBM"]
error_text: []
asked_as: ["A seller was removing an affected product from FBA while keeping an FBM offer on the same listing."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0124"
---

## Question

A seller was removing an affected product from FBA while keeping an FBM offer on the same listing. The FBA offer was still active and winning the Buy Box, a client stakeholder assumed some FBA units were unaffected and could stay, and part of the removal order showed as cancelled although thousands of units had already shipped back.

## Answer

Treat FBA units of one SKU as interchangeable: a removal order cannot pick batches, so remove all FBA stock when any batch is affected. Close the FBA offer while the removal runs so it stops winning the Buy Box. Expect part of a large removal to show as cancelled because reserved units cannot be removed yet, and plan several removal orders to empty the SKU.

## Cause

A removal order targets inventory by SKU, condition and quantity, so a seller cannot choose which physical units or batches come back. The thread notes one exception: Amazon itself blocking a specific batch. When only some batches are affected, the whole FBA stock of the SKU has to be removed. Units that sit in reserved status while Amazon settles them (for example awaiting scanning) are not available for removal, so that part of the order shows as cancelled and needs later removal orders. The FBA offer stays buyable until the seller closes it.

## Fix

1. Confirm with the stakeholders that a removal order cannot select batches, so every FBA unit of the SKU must come back unless Amazon itself has blocked a specific batch.
2. Close the FBA offer so the FBM offer takes the Buy Box during the removal, and leave the FBM offer active (operator approval before changing offer status).
3. Create the removal order for all fulfillable and unfulfillable units available for removal, and read the Total inventory not available for removal legend for the reason codes.
4. Check the Removal Order Detail report. Quantities shown as cancelled in the thread had moved to reserved and were not yet removable.
5. Re-check FBA inventory as reserved units become available and create follow-up removal orders until no units remain.

## Verify

The FBA offer is inactive, the removal order detail shows shipped quantities, and the FBA inventory page shows no available or reserved units left for the SKU.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The removal SOP covers creating and cancelling removals, but not that batches cannot be targeted, that reserved units show as a cancelled part of the order, or that the FBA offer must be closed while FBM stays live.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/README.md`).
