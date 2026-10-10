---
id: KC-0148
title: "Lost inbound FBA claim: Amazon asks for proof of delivery and pays less than the estimated amount"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: "FBA inbound shipment reconciliation / reimbursement"
surface_verified: false
symptom_keywords: ["proof of delivery lost inbound", "POD request FBA shipment", "reimbursement lower than estimated", "inbound shipment missing units claim", "carrier POD for Amazon"]
error_text: []
asked_as: ["For a lost-inbound reconciliation, Amazon asked for proof of delivery on a carrier shipment, and the reimbursement estimate shown looked higher than what would be paid."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md", "MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0148"
---

## Question

For a lost-inbound reconciliation, Amazon asked for proof of delivery on a carrier shipment, and the reimbursement estimate shown looked higher than what would be paid.

## Answer

When Amazon asks for proof of delivery on a lost inbound shipment, pull a POD from the carrier for every tracking ID and submit them with a summary sheet. Expect the reimbursement to follow the manufacturing cost on file, not the estimated amount shown, so keep cost of goods uploaded and backed by invoices before the claim.

## Cause

Amazon asked for proof of delivery on a lost inbound shipment; the request itself was only in a screenshot, and the thread did not establish whether a POD is required for every tracking ID. Under the reimbursement policy effective March 2025, Amazon reimburses lost or damaged FBA inventory at manufacturing cost and excludes shipping, handling and Amazon fees (MAG SOP), so the payout can fall below the estimated amount shown.

## Fix

1. Collect every tracking ID in the inbound shipment.
2. Download the proof of delivery PDF for each tracking ID from the carrier.
3. Compile a summary sheet of tracking IDs and delivery status and bundle the PDFs.
4. Submit them with the inbound claim through the Reconcile tab in the Shipping Queue (operator approval required before submission).
5. Make sure the cost of goods for the SKU is uploaded and backed by invoices so the reimbursement uses the correct manufacturing cost.

## Verify

The reconciliation shows the proof of delivery accepted and the reimbursement posts at the cost-of-goods value.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md`
- Also in: `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the carrier proof-of-delivery bundle for lost inbound claims and links the lower-than-estimated payout to the cost-of-goods reimbursement rule.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md`, `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`).
