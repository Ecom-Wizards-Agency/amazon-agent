---
id: KC-0132
title: "Removal order to an outside warehouse: what the address needs and what to tell the warehouse about tracking and timing"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Create removal order (ship-to address); Removal order detail"
surface_verified: false
symptom_keywords: ["removal order to 3PL", "removal order phone number required", "removal order no tracking", "when will removal ship", "removal shipped in several boxes"]
error_text: []
asked_as: ["The client asked to move FBA stock back to its own outside warehouse and then wanted to know whether it would come by truck or courier, whether everything would move in a single transfer, the expected"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0132"
---

## Question

The client asked to move FBA stock back to its own outside warehouse and then wanted to know whether it would come by truck or courier, whether everything would move in a single transfer, the expected ship date and the tracking numbers.

## Answer

Before creating a removal order to an outside warehouse, collect a contact phone number with the address. Set expectations early: Amazon picks the carrier, may ship the removal in several parts, gives no ship date up front, and can take 90 days or more. Track the order through the removal detail reports and reconcile received units against the order total.

## Cause

Amazon processes removal orders on its own schedule, chooses the carrier itself, and may send the stock as more than one shipment; the seller gets no carrier choice, consolidation or ship date in advance. The MAG SOP says removals can take 90 days or more and that a tracking ID becomes available once the order is processed. The thread also reports that the ship-to address form asked for a contact phone number; no local source confirms that.

## Fix

1. ["1. Collect the warehouse name, full address, contact person and phone number before creating the removal order; in this case the form asked for a phone number.", "2. Create the removal order with that address (operator approval before submitting).", "3. Tell the warehouse up front: the removal may arrive as several shipments, Amazon picks the carrier, ship dates are not known in advance, and processing can take 90 days or more.", "4. Share the total units expected so the warehouse can reconcile.", "5. Track progress with the Removal Order Detail and Removal Shipment Detail reports, which show tracking once each shipment is processed, rather than waiting for one tracking number."]

## Verify

The removal shipment detail report lists each shipment as it leaves, and the warehouse's received units reconcile to the removal order total.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The removal SOP covers creation and timing; new here are the required contact phone and the expectations to set with the receiving warehouse (several shipments, no carrier, date or single tracking).
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`, `MAG SOPs/catalog/catalog-sop-negative-feedback-removal.md`, `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`).
