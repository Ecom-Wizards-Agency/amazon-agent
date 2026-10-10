---
id: KC-0128
title: "Unshipped FBA shipments created by mistake: can they be cancelled without hurting performance?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Shipping queue > Send to Amazon workflow > Cancel shipments"
surface_verified: false
symptom_keywords: ["cancel open FBA shipments", "shipments never sent", "cancel FBA shipment performance impact", "working shipments created by mistake", "does cancelling shipment affect account health"]
error_text: []
asked_as: ["Several FBA shipments stayed open because the stock was never sent; they had been created by mistake."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0128"
---

## Question

Several FBA shipments stayed open because the stock was never sent; they had been created by mistake. Can they be cancelled, and does cancelling affect account performance?

## Answer

Cancel FBA shipments that never left the warehouse instead of leaving them open; cancelling an unshipped shipment does not hurt account health. Confirm with the owner that nothing was handed to a carrier, then cancel and create new shipments when stock is ready. Avoid habitual create-and-cancel cycles.

## Cause

Shipments that were created but never handed to a carrier stay open in the shipping queue. Cancelling a shipment that has not shipped moves it to Canceled status and, per the agency answer and the MAG SOP, does not harm account health; the SOP adds that frequent create-and-cancel cycles may look unusual.

## Fix

1. List the open shipments and confirm with the owner that none of them left the warehouse (no tracking, no carrier pickup).
2. Get the owner's approval to cancel the exact shipment list.
3. Open the shipment's Send to Amazon workflow and click 'Cancel shipments' at the bottom of the page; this cancels every shipment created in that workflow, so check that the workflow holds only shipments on the approved list.
4. If partnered-carrier labels were bought, cancel within the void window (24 hours for small parcel, one hour for pallets) or ask Seller Support to refund unused labels.
5. Create fresh shipments when the stock is actually ready to ship.

## Verify

The cancelled shipments show Canceled status in the shipping queue and no new inbound defect appears for them.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms from a live case the MAG SOP statement that cancelling unshipped FBA shipments does not hurt account health; no first-party capture states it.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
