---
id: KC-0157
title: "Units carry an old UPC that no longer matches the listing: do the carton labels cover it or must each unit be relabeled?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Send to Amazon > unit labels and box labels"
surface_verified: false
symptom_keywords: ["old UPC on units", "box labels vs unit labels", "relabel each unit FBA", "wrong barcode on product", "UPC changed new batch FBA inbound"]
error_text: []
asked_as: ["A client operator asked whether the carton labels for a US FBA inbound would map to an old UPC printed on the units, or whether each unit had to be relabeled."]
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
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0157"
---

## Question

A client operator asked whether the carton labels for a US FBA inbound would map to an old UPC printed on the units, or whether each unit had to be relabeled.

## Answer

Box labels never fix a unit barcode problem, because they identify cartons and not products. When units carry an outdated barcode, cover it on each unit with a label that matches the current listing before shipping. Send the warehouse unit labels and box labels as two named sets so nobody mistakes one for the other.

## Cause

Box (carton) labels identify the shipment and the box for receiving; they have nothing to do with the product barcode. Amazon identifies each unit by its own barcode, so units that carry a barcode that no longer matches the listing must each get a label with the barcode the current listing uses. Unit labels are produced when the SKU and its barcode are set up, separately from the box labels Send to Amazon prints after box content is entered.

## Fix

1. Check the barcode printed on the units against the barcode on the listing the shipment uses.
2. If they differ, print the unit labels for the current listing (Amazon barcode or the current manufacturer barcode) and cover the old barcode on every unit.
3. Print the box labels separately from Send to Amazon after box content is entered; they go on the outside of each carton.
4. Share both label sets in one agreed folder and tell the warehouse which is which before the carrier pickup.

## Verify

Every unit shows only one scannable barcode that matches the listing, every carton carries its own box label, and the shipment receives without labeling defects.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit spells out that box labels never replace unit barcodes, so units with an outdated UPC must each be relabeled to match the listing.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`).
