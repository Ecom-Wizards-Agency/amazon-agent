---
id: KC-0158
title: "Do FBA units need FNSKU labels when they already carry a manufacturer barcode, and how heavy may a carton be?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Send to Amazon > Choose inventory to send / Pack individual units"
surface_verified: false
symptom_keywords: ["FNSKU label needed?", "manufacturer barcode instead of FNSKU", "carton weight limit 50 lb", "units per box FBA", "22.5 kg box limit"]
error_text: []
asked_as: ["A client operator asked whether previously produced FNSKU labels were still needed, and how many units per box the warehouse should pack for a US inbound that would be split across several fulfillment"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", "MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0158"
---

## Question

A client operator asked whether previously produced FNSKU labels were still needed, and how many units per box the warehouse should pack for a US inbound that would be split across several fulfillment centers.

## Answer

FNSKU labels are optional only when the SKU uses manufacturer-barcode tracking and the seller is an eligible brand owner; resellers must still use Amazon barcodes. Keep every box of standard-size units under 50 lb (about 22.6 kg) and round the quantity so all cartons hold the same number of units. Decide units per box first, because Send to Amazon asks for packing before it proposes the fulfillment-center split, and the split then comes in whole boxes.

## Cause

When a brand owner's SKU is set to manufacturer-barcode tracking, the product's own barcode identifies the unit and FNSKU labels are optional. Since Amazon ended commingling, resellers without the brand role must use Amazon barcodes even when the product has a manufacturer barcode, so 'no FNSKU needed' holds only for eligible brand owners. Carton limits come from Amazon: a box of standard-size units must not exceed 50 lb (about 22.6 kg; the thread used 22.5 kg as a safe figure). In Send to Amazon the units per box are entered before placement, and Amazon then splits the shipment across fulfillment centers in whole boxes, so identical cartons keep every destination clean.

## Fix

1. Check the SKU barcode type and the brand role. If the SKU is set to manufacturer barcode and the seller is the brand owner, skip FNSKU labels and use the product barcode; otherwise apply Amazon barcode labels.
2. Pick units per box so that each box of standard-size units stays under 50 lb.
3. Round the shipment quantity to a multiple of units per box so every carton is identical.
4. Enter that case-pack configuration in Send to Amazon step 1, then review the placement split, which assigns whole boxes per fulfillment center, before telling the packer how to label cartons per destination.

## Verify

Send to Amazon accepts the case-pack configuration with no overweight warning, the placement split lists whole boxes per destination, and every carton weighs under 50 lb.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The 50 lb box limit and manufacturer-barcode option sit in separate SOPs; no unit combines them into a units-per-box planning rule for a multi-center split.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
