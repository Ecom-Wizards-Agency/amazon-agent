---
id: KC-0008
title: "Dispute invalid FBA inbound 'Labeling required' defects: one case per shipment, escalate disagreements to SAS, triage by defect type"
kind: diagnosis
topic: support-cases
status: draft
skills: [amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > FBA > Inbound Performance dashboard; Seller Support cases; Help > Strategic Account Services Support (self-service, Issue Assistance); Reports > Payments > Transaction view"
surface_verified: false
symptom_keywords: ["labeling required inbound defect", "dispute inbound performance defect", "escalate to SAS issue assistance", "manufacturer barcode flagged labeling", "relabeling fee dispute"]
error_text: ["Labeling required"]
resolution_status: resolved
fix_source: agency
evidence_location: case
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-download-an-inbound-performance-report.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-05
provenance: "ledger:KC-0008"
---

## Question

The client saw several inbound shipments flagged with 'Labeling required' defects on the Inbound Performance dashboard and asked what happens to unlabelled units, whether Amazon can be pushed for an answer, and whether to involve SAS.

## Answer

Do not accept FBA 'Labeling required' inbound defects at face value. Request FC images, check whether the SKU is set to the manufacturer barcode, and confirm with the prep warehouse what was labelled. File one case per shipment and escalate disagreements through SAS Issue Assistance with the earlier case linked, before the escalation window closes. Group shipments by defect type, because a precedent only carries over to the same defect, and shipping-plan mismatches are a separate, often non-reimbursable category. Check the transaction view for relabelling fees and dispute any that should not apply.

## Cause

Mixed causes. Some defects were invalid: the SKUs were set to use the manufacturer barcode and Amazon's own images showed the UPC matched only that ASIN. The 3PL also left some units unlabelled through operator error. One shipment had a different defect, unexpected items against the shipping plan, which Amazon would not reimburse.

## Fix

1. Pull the defect list from the Inbound Performance dashboard and ask Amazon for the FC receiving images that show what 'labeling' means (missing, unscannable or wrong label).
2. Check with the prep warehouse or 3PL whether labelling was done and which barcode type (manufacturer barcode or FNSKU) each SKU is set to use.
3. Note that a loss investigation can open only after the shipment closes, but a defect dispute can start earlier.
4. Open one case per shipment; SAS will not handle several shipments in one case. Case sends need operator approval.
5. When Seller Support stalls or gives an answer you disagree with, escalate through the Strategic Account Services self-service page (sellercentral.amazon.com/gc/strategic-account-services/self-service) as an Issue Assistance case linking the earlier case.
6. Use a won case as precedent only for shipments with the same defect type. Amazon said the Inbound Performance report updates within 24 hours of revoking a defect.
7. Triage remaining shipments by defect type before filing. A shipping-plan discrepancy (unexpected items) is not a labelling defect and the precedent does not apply.
8. Check Reports > Payments > Transaction view (service and FBA fee lines, Fee Explainer) for relabelling charges and dispute any that should not apply. The agency stated that US FBA Prep and Labeling services ended on 01.01.2026; not verified against a first-party page.
9. A closed case reportedly cannot be escalated after a 10-day window, so open a new case referencing the defect and the earlier case; a case filed in the wrong support channel is rejected (relayed by an SAS manager, not seen in Amazon documentation).

## Verify

Amazon's message revoking an invalid 'Labeling required' defect is quoted in the thread, a second case was approved, and the flagged shipments left the dashboard except one that got a new case. The shipping-plan-discrepancy units were not reimbursed.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-download-an-inbound-performance-report.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source covers disputing 'Labeling required' inbound defects, the one-case-per-shipment SAS rule or escalation through SAS Issue Assistance.
- Existing coverage: none.
