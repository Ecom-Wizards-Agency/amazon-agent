---
id: KC-0029
title: "Lost inbound units: a tracking number alone does not prove how many units were sent"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: "FBA shipment reconciliation / lost inbound reimbursement claim"
surface_verified: false
symptom_keywords: ["lost inbound reimbursement proof", "Amazon received fewer units than shipped", "what document proves units sent to FBA", "shipment shortage claim evidence", "tracking number not enough for FBA claim"]
error_text: []
asked_as: ["Amazon received fewer units than the shipment declared, and a reimbursement claim needed supporting documents."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md", "MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0029"
---

## Question

Amazon received fewer units than the shipment declared, and a reimbursement claim needed supporting documents. The brand contact asked what to request from its fulfilment partner and whether a screenshot of the tracking number would do; no photos of the box contents had been taken before shipping.

## Answer

When FBA receives fewer units than you shipped, prove the quantity, not just the delivery: a tracking number only shows that the boxes arrived. Submit the supplier or factory invoice and a packing list for that shipment, plus carrier proof of delivery with box counts or weights. Photograph packed cartons on future shipments so the next shortfall is easy to prove.

## Cause

The claim disputes a quantity, not a delivery: a tracking number or proof of delivery shows that boxes arrived, but not how many units were inside. Amazon needs a document that ties the declared unit count to the shipment.

## Fix

1. Confirm the gap in the shipment's Contents tab: units shipped versus units received.
2. Collect evidence of quantity: the supplier or factory invoice for the goods in that shipment, a signed packing slip or packing list, and for future shipments, photos of packed cartons.
3. Add proof of delivery: carrier receipts showing box count and weight for small parcel, or an Amazon-stamped bill of lading for LTL/FTL.
4. Upload the documents to the reconciliation claim or reimbursement tool (operator approval required before submitting).
5. For future shipments, photograph carton contents and keep packing lists per box so a shortfall can be proven.

## Verify

The shipment's received count is adjusted or a reimbursement for the missing units appears in the reimbursements report.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`
- Also in: `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The reconciliation SOP already lists the accepted documents; the card adds the distinction that tracking proves delivery but not quantity, and the fallback to the factory invoice when no carton photos exist.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`).
