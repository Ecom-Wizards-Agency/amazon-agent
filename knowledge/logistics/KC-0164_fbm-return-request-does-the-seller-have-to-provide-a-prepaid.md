---
id: KC-0164
title: "FBM return request: does the seller have to provide a prepaid return label, and how does that differ from FBA?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Orders > Manage Seller Fulfilled Returns"
surface_verified: false
symptom_keywords: ["FBM prepaid return label", "who pays return shipping FBM", "merchant fulfilled return label", "free returns seller fulfilled", "prepaid returns exemption"]
error_text: []
asked_as: ["A support teammate handling a seller-fulfilled return request asked whether the seller provides a prepaid return label or whether the buyer pays for the return label, as they assumed was standard for "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md", "Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md"]
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0164"
---

## Question

A support teammate handling a seller-fulfilled return request asked whether the seller provides a prepaid return label or whether the buyer pays for the return label, as they assumed was standard for FBM.

## Answer

Before telling a buyer to pay for a US seller-fulfilled return, check the return request: Amazon enrolls US sellers in prepaid returns automatically and issues the buyer a prepaid label unless the SKU has an approved exemption. For exempt SKUs, upload a seller-paid label with tracking or apply your return policy, and refund within two business days of receiving the item. FBA returns are handled by Amazon.

## Cause

For US seller-fulfilled orders, Amazon enrolls sellers automatically in prepaid returns and gives the buyer a prepaid return label through Buy Shipping. A seller can request an exemption per SKU, and for exempt SKUs the seller may upload its own prepaid label. The thread answered that FBM sellers decide on return labels themselves; the captured page is stricter and wins. The thread also said FBA returns always come with an Amazon prepaid label; no local capture was checked for that.

## Fix

1. Open Manage Seller Fulfilled Returns and check whether Amazon already issued a prepaid label for the return request.
2. If the SKU is not exempt from prepaid returns, let the Amazon prepaid label stand; do not ask the buyer to buy a label.
3. If the SKU is exempt, upload a seller-paid prepaid label with tracking on Manage Seller Fulfilled Returns, or handle the return under the seller return policy.
4. For a non-US return address, provide a prepaid label within 2 days of the request, a returnless refund, or a valid US return address in Return settings.
5. Issue the refund within two business days of receiving the return (refunds and buyer messages need operator approval).

## Verify

The return request on Manage Seller Fulfilled Returns shows a prepaid label or an authorized status, and the refund is issued within two business days of receipt.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`
- First-party: `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Records that the team told an FBM support teammate the seller decides on return labels, which conflicts with the captured auto-enrollment rule for US prepaid returns, so the unit must correct that belief.
- Existing coverage: full (`Amazon Seller Help/articles/052-manage-seller-fulfilled-returns-G200708210.md`, `Amazon Seller Help/articles/007-seller-fulfilled-returns-refunds-cancellations-and-claims-G69126.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/055-amazon-s-a-to-z-guarantee-claims-G27951.md`).
