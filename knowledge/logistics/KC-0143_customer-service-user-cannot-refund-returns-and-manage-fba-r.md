---
id: KC-0143
title: "Customer service user cannot refund returns and Manage FBA Returns permission only offers View"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Settings > User Permissions; Orders > Manage Returns"
surface_verified: false
symptom_keywords: ["Manage FBA Returns only view", "CX team cannot refund Amazon", "refund page keeps loading", "user permission refund access", "who refunds FBA returns"]
error_text: []
asked_as: ["A customer service agent's refund page kept loading when refunding a return, and when the account admin tried to grant the Manage FBA Returns permission, the highest level available was View."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0143"
---

## Question

A customer service agent's refund page kept loading when refunding a return, and when the account admin tried to grant the Manage FBA Returns permission, the highest level available was View.

## Answer

Do not grant customer service agents FBA return rights so they can process refunds; Amazon refunds FBA returns itself, which is why that permission offers only View. Agents need refund and order rights for seller-fulfilled returns, which they refund within two business days of the returned item arriving and being inspected. Treat any manual refund on an FBA order as an owner decision.

## Cause

Amazon processes FBA returns and their refunds itself, so the Manage FBA Returns permission has no edit level and the team does not need it. Seller-fulfilled returns enrolled in prepaid return labels are authorized automatically, and the seller refunds after the item reaches its warehouse; that needs refund rights. Why the refund page hung for the agent was not established in the thread.

## Fix

1. Do not try to refund FBA returns manually; Amazon issues those refunds.
2. Give agents who handle seller-fulfilled returns the refund and order management permissions.
3. For seller-fulfilled returns with prepaid labels, refund in full or in part within two business days of the returned item reaching the warehouse, based on its condition. Otherwise Amazon may refund the buyer on the seller's behalf and charge the account.
4. Treat any manual refund on an FBA order as an account-owner decision (approval required). Never tie a refund to a buyer's review.
5. If the refund page still hangs for a seller-fulfilled order, retest with the agent once the permissions have saved, and capture the screen.

## Verify

Agents can open and complete a refund on a seller-fulfilled return, and FBA returns show Amazon-issued refunds without seller action.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`
- Also in: `MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The Manage FBA Returns permission only offers View because Amazon refunds FBA returns itself; agents need refund rights only for seller-fulfilled returns.
- Existing coverage: partial (`Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`, `MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`).
