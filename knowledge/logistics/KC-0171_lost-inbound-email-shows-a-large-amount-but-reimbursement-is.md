---
id: KC-0171
title: "Lost inbound email shows a large amount but reimbursement is based on cost of goods"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon email about lost inbound units; FBA reimbursements"
surface_verified: false
symptom_keywords: ["lost inbound needs your attention", "lost inbound reimbursement amount", "reimbursed at cost not sales price", "lost inventory claim documents"]
error_text: ["in lost inbound needs your attention"]
asked_as: ["An Amazon email announced a large lost-inbound amount needing attention and the client asked whether anything had to be done."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md", "MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0171"
---

## Question

An Amazon email announced a large lost-inbound amount needing attention and the client asked whether anything had to be done.

## Answer

Do not plan around the dollar figure in a lost-inbound email; Amazon reimburses lost FBA units at cost of goods, not sales price. Keep cost of goods current in Seller Central and file the claim with supplier invoices and the shipment packing list.

## Cause

Since the reimbursement policy update effective 10.03.2025, Amazon reimburses lost and damaged FBA inventory based on the product's cost of goods (sourcing cost), not its sales price. The agency read the lost-inbound email's headline figure as a sales-value number that overstates the payout; the thread does not show the final reimbursement amount. A claim still needs supporting documents.

## Fix

1. Treat the email amount as a headline, not the expected reimbursement.
2. Check that the cost of goods per SKU is correct under Manage Sourcing Cost (Inventory > FBA Inventory > Inventory Defect and Reimbursement); a large increase needs a manufacturer or wholesaler invoice.
3. Collect the supplier invoices and, if asked, the shipment packing list for the affected inbound.
4. Submit them through Amazon's lost-inbound claim path, or pass them to the reimbursement service you use (operator approval before any submission).

## Verify

The reimbursement posts in Payments at the cost-of-goods value for the lost units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md`
- Also in: `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that the lost-inbound email headline is sales value while payment follows cost of goods, and names the documents a claim needs.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/README.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`).
