---
id: KC-0105
title: "Who handles refunds, returns and replacements: FBA versus FBM orders"
kind: rule
topic: support-cases
status: reviewed
skills: [amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: "Manage Orders / Manage Returns"
surface_verified: false
symptom_keywords: ["who refunded this order", "automatic refund FBA", "FBA vs FBM returns handling", "customer replacement FBA", "do we handle FBA refunds"]
error_text: []
asked_as: ["A client support agent saw refunds on orders and asked how to see who processed a refund, why orders are refunded automatically, and whether the team must handle replacements."]
synonyms: []
resolution_status: partial
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md", "Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0105"
---

## Question

A client support agent saw refunds on orders and asked how to see who processed a refund, why orders are refunded automatically, and whether the team must handle replacements.

## Answer

For FBA orders Amazon provides customer service and decides on and processes returns, refunds and replacements, so the seller team does not act on those requests. Amazon can still charge the seller back where it finds the seller responsible, and refunds where the item never came back need a reimbursement check. For FBM orders the seller handles all of it. Check the order's fulfillment channel before acting on a refund or replacement request.

## Cause

For FBA orders Amazon is responsible for customer service, returns, refunds, adjustments and replacements, and decides whether a customer gets a refund or replacement (FBA Service Terms F-8.2 in the Business Solutions Agreement), so refunds can appear without any action from the seller team. Amazon charges the seller back where it finds the seller responsible. For FBM orders, and for Multi-Channel Fulfillment units (F-6.1), the seller handles customer service, returns and refunds.

## Fix

1. Check the fulfillment channel of the order in Manage Orders.
2. FBA order: do not process the return, refund or replacement yourself; Amazon decides and processes it.
3. FBA order refunded but item not returned: check the FBA customer returns and refund reports and open a reimbursement case where needed (see the FBA customer returns reimbursement SOP); case submission needs operator approval.
4. FBM order: the seller team handles customer contact, returns and refunds.
5. To see who issued a refund on an order, check the order detail; the thread did not establish where this is shown.

## Verify

Refunds on FBA orders appear without seller action; FBM return and refund requests are handled by the seller team.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md`
- First-party: `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`
- Also in: `MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Gives support staff a one-line FBA versus FBM split for who handles refunds, returns and replacements.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
