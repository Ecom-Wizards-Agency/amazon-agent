---
id: KC-0156
title: "FBA inbound from a third-party warehouse: who creates the shipment and labels, and who packs and hands over"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["third-party warehouse FBA shipment who creates", "raise order in Seller Central for third-party warehouse", "third-party warehouse needs labels FBA", "who prints FBA box labels"]
error_text: []
asked_as: ["The brand's third-party warehouse says the Amazon account manager must raise the order in Seller Central before stock can flow to the third-party warehouse for packing."]
synonyms: []
resolution_status: partial
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
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0156"
---

## Question

The brand's third-party warehouse says the Amazon account manager must raise the order in Seller Central before stock can flow to the third-party warehouse for packing. What are the steps on the Amazon side?

## Answer

With a third-party warehouse, the Amazon account manager creates the FBA shipment and buys the box labels in Send to Amazon first; the third-party warehouse then packs, applies one label per box and hands the boxes to the partnered carrier. Agree this split with the third-party warehouse's operations contact once, in writing or on a call, so neither side waits on the other.

## Cause

Not a fault: the third-party warehouse cannot act until a shipment exists in Seller Central, and the responsibility split was unclear in the third-party warehouse's SOP.

## Fix

1. The Amazon account manager decides the quantities needed at Amazon.
2. The account manager creates the shipment in Send to Amazon with the third-party warehouse as ship-from address and the box contents (confirmation needs operator approval).
3. With the Amazon-partnered carrier, buy and download the box labels in the workflow.
4. Send the labels to the third-party warehouse operations contact.
5. The third-party warehouse packs the boxes, applies one label per box and hands them to the carrier.

## Verify

The shipment shows the carrier tracking per box and moves to In transit, then Receiving.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the responsibility split between the account manager (shipment, labels) and a third-party warehouse (packing, labelling, carrier handover).
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`).
