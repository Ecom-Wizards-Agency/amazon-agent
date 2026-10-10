---
id: KC-0165
title: "Seller-fulfilled return request shows an overseas return address: approve it, what to refund, and where to change the return address"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Orders > Manage Returns; Settings > Return settings"
surface_verified: false
symptom_keywords: ["return request return address wrong country", "fbm return goes to overseas address", "change return address seller central", "approve return request refund amount", "return to 3pl address"]
error_text: []
asked_as: ["A team member saw a seller-fulfilled return request whose return address pointed overseas and asked whether to approve it and whether to refund an additional cost on top of the product price."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md", "Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md", "Amazon Seller Help/articles/053-issue-refunds-and-concessions-for-seller-fulfilled-orders-GU7K5N5GUP67M4X9.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0165"
---

## Question

A team member saw a seller-fulfilled return request whose return address pointed overseas and asked whether to approve it and whether to refund an additional cost on top of the product price.

## Answer

Keep a valid US default return address in Return settings that points at the warehouse that actually receives returns. With a non-US address, Amazon requires a merchant prepaid label within 2 days, a returnless refund or a corrected US address, and returns that cannot be delivered to an outdated address are treated as abandoned. Refund within Amazon's deadline: the captured pages say two business days in one place and four calendar days in another, so use the shorter. Whether to leave any amount beyond the item price out of the refund depends on the return reason; the thread does not settle it.

## Cause

The default return address in Return settings was a non-US address instead of the US warehouse that handles returns, so the return authorization pointed abroad. The thread shows the fix (the agency changed the address in Return settings) but not a screenshot of the old setting.

## Fix

1. Open Orders > Manage Returns and check the request status; Amazon authorizes in-policy US return requests automatically. Authorize it only if it is still pending (an Amazon write: operator approval).
2. For a request already issued with the non-US address, give the buyer a merchant prepaid label through Manage Seller Fulfilled Returns within 2 days, or a returnless refund, as the help page requires.
3. Refund within Amazon's deadline after the return arrives. The agency refunded the item price only and left out the extra amount line; the thread never established what that line was, so check the return reason and the refund rules before leaving any amount out.
4. Once the account owner confirms the warehouse, open Settings > Return settings and set the default return address to the US warehouse that should receive returns, with contact name and phone (settings change: operator approval).

## Verify

New return authorizations show the US warehouse as the return address.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`
- First-party: `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`
- First-party: `Amazon Seller Help/articles/053-issue-refunds-and-concessions-for-seller-fulfilled-orders-GU7K5N5GUP67M4X9.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties an overseas return address on a seller-fulfilled return to the Return settings default address and the approve-then-refund-item-price handling.
- Existing coverage: full (`Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`, `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`, `MAG SOPs/catalog/logistics-sop-fba-customer-returns-reimbursements.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
