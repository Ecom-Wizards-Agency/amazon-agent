---
id: KC-0161
title: "Reimbursement tool shows a large lost-inventory amount: actual FBA reimbursement is now based on manufacturing cost, not sales price"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["lost inventory reimbursement estimate too high", "FBA reimbursement manufacturing cost", "reimbursement based on sales price or cost", "how much will Amazon reimburse lost units", "reimbursement tool estimate"]
error_text: []
asked_as: ["The client saw a large recoverable amount for lost FBA inventory in a third-party reimbursement tool and asked what it meant."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md", "MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md"]
supersedes: []
contradicts: ["MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md"]
observed: 2025-05
review_by: 2027-10
provenance: "ledger:KC-0161"
---

## Question

The client saw a large recoverable amount for lost FBA inventory in a third-party reimbursement tool and asked what it meant.

## Answer

Since March 2025 Amazon reimburses lost and damaged FBA inventory at manufacturing cost, not at sales price. Read third-party reimbursement estimates built on sales price minus fees as an upper bound, and keep sourcing costs and supplier invoices current in Seller Central so the reimbursements are not undervalued.

## Cause

Amazon changed its FBA lost and damaged inventory reimbursement from a sales-price basis to a manufacturing (sourcing) cost basis in March 2025; the MAG SOP gives 10.03.2025 as the effective date, while the third-party tool notice quoted in the thread said 31.03.2025. The third-party reimbursement tool in the thread could not read the manufacturing cost, so it kept estimating with sales price minus Amazon fees, which overstates the amount the seller will actually receive.

## Fix

1. Treat the tool's estimate as an upper bound and subtract the average profit margin for a realistic figure.
2. In Seller Central, review Inventory > FBA Inventory > Inventory Defect and Reimbursement for eligible items.
3. Check and, where available, update the sourcing cost in Manage Sourcing Cost with supplier invoices as evidence.
4. File or let the tool file the eligible claims (filing needs operator approval).

## Verify

Reimbursement entries in the Reimbursements report show amounts in line with sourcing cost rather than sales price.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md`
- Also in: `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that a third-party reimbursement tool may still estimate on sales price minus fees, so its figure overstates what Amazon pays under the manufacturing-cost basis.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/logistics-sop-uploading-cost-of-goods-for-amazon-reimbursement-policy-update-effective-march-10th-2025.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`, `AdLabs Help/articles/003-rpc-bidding-formula-acos-goals.md`, `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`).
