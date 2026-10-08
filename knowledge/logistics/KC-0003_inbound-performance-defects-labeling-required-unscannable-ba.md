---
id: KC-0003
title: "Inbound Performance defects (labeling required, unscannable barcode, wrong quantity) can be disputed and removed; an ASIN mismatch is reimbursed only in part"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Shipments > shipment Problems tab; FBA Inbound Performance dashboard > Defects"
surface_verified: false
symptom_keywords: ["inbound performance defect dispute", "labeling required defect", "barcode cannot be scanned defect", "inaccurate item quantity in box", "is the inbound defect amazon's mistake"]
error_text: ["Barcode cannot be scanned", "Inaccurate item quantity in box", "Labeling required"]
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0003"
---

## Question

The client asked whether three new Inbound Performance defects were Amazon's mistake or something to raise with their 3PL: 'Barcode cannot be scanned', 'Inaccurate item quantity in box' and 'Labeling required' (high priority, on two shipments).

## Answer

Inbound Performance defects are not final. Dispute each labeling or barcode defect from the Inbound Performance dashboard; in this case Amazon withdrew the defect where it had no photos or no units to inspect. An ASIN mismatch, where a sibling variant arrives in place of the expected ASIN, is a real prep error that Amazon reimburses only in part. Reconcile those units separately and fix the variant labeling at the 3PL so the defect does not repeat.

## Cause

Amazon raised the defects at receiving. For two of them it had no evidence: no photos for the labeling defect and no units left to inspect for the barcode defect. The quantity defect was real but different: the FC received units of a sibling variant in place of the expected ASIN, which points to a prep or picking mix-up at the 3PL or supplier.

## Fix

1. Open each shipment's Problems tab and the Inbound Performance Defects view to get the defect type, shipment ID and report date.
2. Dispute each defect from the Inbound Performance dashboard and check it daily.
3. Labeling required: the dispute was approved and the defect removed because Amazon had no photo evidence.
4. Barcode cannot be scanned: removed because Amazon could not verify it (no units to inspect, no photos).
5. Quantity or ASIN mismatch: Amazon confirmed it received a sibling variant in place of the expected ASIN and reimbursed only part of the units. Reconcile the remaining gap separately.
6. Report the result per defect to the client, separating Amazon's errors from the defect that needs a prep or labeling fix at the 3PL.

## Verify

Two defects were removed from the dashboard and part of the mismatched units was reimbursed; the client acknowledged. No later follow-up on the remaining unit gap is in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source explains disputing seller inbound defects or that Amazon withdraws them when it lacks photo or unit evidence.
- Existing coverage: none.
- Confidence is low: one thread, and the cited SOP covers downloading the report, not disputing a defect.
- Overlaps KC-0008, which disputed 'Labeling required' defects with one Seller Support case per shipment, escalated to SAS. A dashboard dispute was enough here because Amazon had no photo or unit evidence; the KC-0008 route applied where Amazon held FC images, Seller Support stalled or disagreed, and several shipments on an account with SAS were affected.
