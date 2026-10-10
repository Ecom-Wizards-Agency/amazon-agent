---
id: KC-0136
title: "Units per carton changed after the FBA shipment was created: edit it or recreate the shipment?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon"
surface_verified: true
symptom_keywords: ["change case pack after shipment created", "units per carton changed FBA shipment", "send more or fewer units than shipment plan", "create shipment from 3PL warehouse", "redo Send to Amazon shipment"]
error_text: []
asked_as: ["The seller wanted to send a bridge quantity from a US third-party warehouse to FBA while the main shipment was still in transit."]
synonyms: []
resolution_status: resolved
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
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0136"
---

## Question

The seller wanted to send a bridge quantity from a US third-party warehouse to FBA while the main shipment was still in transit. The agency did not have the warehouse as a ship-from address, and the warehouse had not confirmed which carton configuration (units per carton) it held. The seller asked whether the carton setup could be changed later if it turned out different.

## Answer

Confirm the units per carton with the sending warehouse before you create an FBA shipment, because confirmed packing information cannot be changed without cancelling and recreating the shipment. If the carton configuration changes, build a new shipment, have it checked, and cancel the old one. A small difference in unit quantity was treated as tolerable, but no Amazon rule backs that, so check the current inbound defect rules before relying on it.

## Cause

Send to Amazon does not allow changes to confirmed packing information (units per carton). A different carton configuration means cancelling the shipment and creating a new one (MAG SOP, Send to Amazon FAQ). The ship-from address also cannot be changed after confirmation. The agency also said a different unit quantity draws at most a warning or reminder; no source backs that.

## Fix

1. Add the third-party warehouse as a ship-from address in Send to Amazon before building the shipment.
2. Confirm the units per carton the warehouse actually holds before entering packing information; do not assume the previous shipment's configuration.
3. If the carton configuration changes after the shipment is created, create a new shipment with the correct packing information instead of editing the old one.
4. Have a second person check the new shipment (ship-from, SKUs, units per carton, quantity) before cancelling the old one.
5. Cancel the superseded shipment, then enter the carrier tracking number on the shipment that will actually travel.

## Verify

Only one active shipment remains for the send-in, its packing information matches the cartons the warehouse will ship, and the tracking number is entered.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP explains packing setup but not that a changed units-per-carton forces a new shipment while a quantity difference was treated as tolerable.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
