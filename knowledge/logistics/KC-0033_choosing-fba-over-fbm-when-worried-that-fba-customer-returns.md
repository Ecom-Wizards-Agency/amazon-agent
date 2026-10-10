---
id: KC-0033
title: "Choosing FBA over FBM when worried that FBA customer returns are not restocked"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Reports > Fulfillment > Customer returns; Inventory > Removal orders"
surface_verified: false
symptom_keywords: ["FBA returns not put back into stock", "FBM more control over returns", "unsellable FBA returns", "FBA vs FBM returns"]
error_text: []
asked_as: ["The client preferred FBM because FBA returns go back to an Amazon warehouse and may not be restocked, while FBM lets them inspect and restock returns themselves."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md", "MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0033"
---

## Question

The client preferred FBM because FBA returns go back to an Amazon warehouse and may not be restocked, while FBM lets them inspect and restock returns themselves.

## Answer

Return handling alone is a weak reason to choose FBM over FBA. Unsellable FBA returns stay visible in reports, and a removal order brings them back for inspection, repackaging and resale through FBM. FBA usually wins on conversion, Prime eligibility and on-time delivery, so compare the removal cost with that gain before deciding.

## Cause

FBA grades each customer return; units judged unsellable stay as unfulfillable inventory instead of returning to stock, but they remain visible in reports and can be removed to the seller.

## Fix

1. Track FBA returns and their disposition in the customer returns report.
2. Create a removal order for unsellable returns to the seller's own address or warehouse.
3. Inspect and repackage removed units, then resell them via FBM or send them back into FBA.
4. Weigh the removal cost against FBA's conversion, Prime badge and on-time delivery benefits before choosing FBM for return control.

## Verify

Unsellable returned units appear in the removal order and arrive at the seller's address for inspection.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a decision aid that FBA return handling is not a reason to prefer FBM, because unsellable returns can be removed and resold.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`, `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`).
