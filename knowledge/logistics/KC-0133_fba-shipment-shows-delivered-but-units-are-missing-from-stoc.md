---
id: KC-0133
title: "FBA shipment shows delivered but units are missing from stock: the warehouse is still receiving them"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Shipments (status Delivered / Checked in / Receiving / Closed); inventory reports"
surface_verified: false
symptom_keywords: ["shipment delivered but not in stock", "units not showing after delivery", "how long does FBA receiving take", "delivered not booked in", "inventory missing from stock report after delivery"]
error_text: []
asked_as: ["The client could not find the units of a 3PL-to-FBA shipment in the stock report even though the shipment had been sent, and asked whether they had arrived and how long booking in takes."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0133"
---

## Question

The client could not find the units of a 3PL-to-FBA shipment in the stock report even though the shipment had been sent, and asked whether they had arrived and how long booking in takes.

## Answer

Units of a delivered FBA shipment become available only after the fulfillment center receives them, so a shipment in Delivered, Checked in or Receiving status will not yet show in sellable stock. Check the shipment status before treating units as missing. Receiving can take a while; the agency's working estimate was up to about two weeks, and no local Amazon page gives a number. Reconcile and raise a discrepancy only after the shipment closes short.

## Cause

The shipment had been delivered but the fulfillment center was still receiving it. Units count as available only once received, so they do not appear as sellable stock while the shipment is in Checked in or Receiving.

## Fix

1. Open the shipment in the Shipping Queue and read its status (In transit, Delivered, Checked in, Receiving, Closed).
2. If it is Delivered, Checked in or Receiving, expect the units to appear only as they are received; they are not lost.
3. Allow time for receiving; the agency estimated up to two weeks, which is not a first-party figure.
4. If units are still missing once the shipment closes, reconcile the shipment and open an investigation (operator approval before submitting a case).

## Verify

The agency confirmed the shipment had arrived and was in receiving; the client was told to expect the units within about two weeks.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The FBA inventory page lists the receiving statuses, but no source gives the practical up-to-two-weeks wait or ties missing stock to the Receiving status.
- Existing coverage: partial.
