---
id: KC-0323
title: "Inbound Performance summary says resolved while defect rows still require action"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > FBA > Shipments > Inbound Performance; shipment summary > Problems"
surface_verified: true
symptom_keywords: ["inbound summary says all resolved", "outstanding inbound defects", "summary disagrees with defect rows"]
error_text: ["Action required", "Acknowledge defect"]
asked_as: ["Does an Inbound Performance summary saying all defects are resolved mean nothing needs doing?"]
synonyms: ["inbound coaching", "shipment problems"]
resolution_status: diagnosis-only
fix_source: agency
evidence_location: screenshot
confidence: low
verification: verified
verified_on: "2026-10-15"
verified_how: "live-ui"
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0323"
---

## Question

Does an Inbound Performance summary saying all defects are resolved mean nothing needs doing?

## Answer

Check the individual defect groups and shipment Problems tabs before concluding that the account is clear. In a live check, the generated summary said all defects were resolved while the group table still counted outstanding defects and individual rows showed Action required. The shipment Problems tabs also offered Acknowledge. Preserve the disagreement and reconcile supporting evidence before any acknowledgement or dispute.

## Cause

The generated narrative and detailed rows displayed inconsistent states. The technical cause and the correctness of the underlying defects were not established.

## Fix

1. Verify the selected seller, marketplace and displayed performance period.
2. Open View all defect groups and count outstanding defects across every group.
3. Open each affected group and record its individual shipment rows, dates, quantities, fees and status.
4. Cross-check representative rows in shipment summary > Problems. Compare carrier proof, packing records and earlier dispute receipts before deciding which defects are valid.
5. Treat missing tracking quantities as affected boxes, not proof of lost inventory. Keep defect-event counts separate from unique shipments.

## Verify

The group totals reconciled to individual Action required rows; shipment Problems tabs independently showed matching defect types and Acknowledge controls. No acknowledgement or dispute was submitted, and no defect clearance was verified.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

Observed on one account. The summary's source, update timing and reason for the mismatch remain unknown. No general defect-removal, reimbursement or acknowledgement outcome was verified.
