---
id: KC-0022
title: "Seller-fulfilled return requests are approved automatically, even for items that come back used: can the seller stop it?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-communications, amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Orders > Manage Returns"
surface_verified: false
symptom_keywords: ["Amazon auto approved returns FBM", "stop automatic return authorization", "FBM returns come back used", "seller fulfilled return requests approved without me", "can I deny return request"]
error_text: []
asked_as: ["The client saw that Amazon had approved return requests on seller-fulfilled orders automatically and that many items came back used, and asked what could be done about these return requests."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md", "Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md"]
supersedes: []
contradicts: []
observed: 2025-02
review_by: 2027-10
provenance: "ledger:KC-0022"
---

## Question

The client saw that Amazon had approved return requests on seller-fulfilled orders automatically and that many items came back used, and asked what could be done about these return requests.

## Answer

Amazon authorizes in-policy US return requests on seller-fulfilled orders automatically, and a seller cannot turn that off. Put the effort where the seller has a lever: answer out-of-policy requests, apply the restocking-fee guidelines to items that come back used, refund on time, and file a SAFE-T claim when Amazon refunds on your behalf without justification. An insert card asking buyers to contact you first can head off some returns.

## Cause

Amazon automatically authorizes US return requests that fall within its returns policy, including for seller-fulfilled orders, so the seller cannot block an in-policy return. Only out-of-policy requests and some exempt categories go to manual authorization.

## Fix

1. Accept that in-policy US return requests on seller-fulfilled orders are authorized automatically; there is no setting to switch this off.
2. Handle out-of-policy requests yourself in Manage Returns: you may accept or deny them, and explain a denial to the buyer through Buyer-Seller Messaging (a send that needs operator approval).
3. For items returned used or damaged, check the restocking-fee guidelines before refunding, and refund within two business days of receiving the return.
4. If Amazon refunded on your behalf and you believe it was unjustified, check eligibility for a SAFE-T reimbursement claim (a submission that needs operator approval).
5. Reduce avoidable returns with an in-package card that invites buyers to contact the seller before returning.

## Verify

Out-of-policy requests are answered within 24 hours, refunds are issued within two business days of receipt, and any SAFE-T claims are tracked.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`
- First-party: `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`
- Also in: `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Answers the client-facing question that auto-authorization of in-policy seller-fulfilled returns cannot be switched off and points to the levers that remain.
- Existing coverage: full (`Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`, `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`).
