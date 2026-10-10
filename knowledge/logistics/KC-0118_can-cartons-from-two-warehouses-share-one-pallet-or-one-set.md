---
id: KC-0118
title: "Can cartons from two warehouses share one pallet or one set of FBA shipping labels"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > ship-from address, LTL pallet information, box labels"
surface_verified: false
symptom_keywords: ["combine warehouses on one pallet", "shipping labels multiple ship from", "LTL needs pallet dimensions", "units per carton mismatch packing list"]
error_text: []
asked_as: ["A seller sending stock from a US 3PL and from a factory overseas asked whether cartons from different warehouses could go on one pallet, and why LTL labels needed pallet dimensions first."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0118"
---

## Question

A seller sending stock from a US 3PL and from a factory overseas asked whether cartons from different warehouses could go on one pallet, and why LTL labels needed pallet dimensions first.

## Answer

Labels belong to one shipment and one ship-from address, so cartons from different warehouses need separate shipments and labels and cannot be combined on a pallet under one plan. For LTL, get pallet dimensions and a pickup date before creating labels, and check units per carton against the packing list first.

## Cause

Each shipment plan is tied to one ship-from address, and LTL pallet labels need pallet dimensions and a pickup date before they are issued; carton labels from one plan cannot be reused for another origin.

## Fix

1. Create a separate shipment (and labels) for each ship-from warehouse.
2. For LTL, collect pallet dimensions and a ready date from each warehouse before generating pallet labels; send FNSKU unit barcodes earlier so repacking can start.
3. Check the units per carton and carton dimensions in the packing list against the case-pack data in Seller Central and update them before labels are printed.
4. Compare LTL and small parcel cost in the workflow; for large volumes palletized LTL is usually cheaper.

## Verify

Each origin has its own shipment and labels, and box contents match the packing list.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: States that one shipment and its labels serve one ship-from warehouse, so cartons from different origins cannot share a pallet or labels, and that LTL labels need pallet dimensions first.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`).
