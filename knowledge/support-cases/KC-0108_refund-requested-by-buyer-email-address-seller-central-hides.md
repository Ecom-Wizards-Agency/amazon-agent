---
id: KC-0108
title: "Refund requested by buyer email address: Seller Central hides buyer emails, and Pending orders cannot be cancelled or refunded by the seller"
kind: diagnosis
topic: support-cases
status: reviewed
skills: [amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Orders > Manage Orders"
surface_verified: false
symptom_keywords: ["refund test order", "find order by buyer email", "buyer email hidden seller central", "cannot refund pending order", "pending order cancelled no refund"]
error_text: [Pending]
asked_as: ["The client asked the agency to refund test purchases, identifying them only by buyer name and email address."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/047-pending-orders-G40571.md", "Amazon Seller Help/articles/053-issue-refunds-and-concessions-for-seller-fulfilled-orders-GU7K5N5GUP67M4X9.md", "Amazon Seller Help/articles/043-communicate-with-buyers-using-buyer-seller-messages-G200389080.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-customer-service-buyer-messages-refund-and-replacement.md"]
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0108"
---

## Question

The client asked the agency to refund test purchases, identifying them only by buyer name and email address.

## Answer

Ask for the order ID whenever someone requests a refund, because Seller Central does not show buyer email addresses. Check the status first: a Pending order is still in payment verification, and the seller cannot cancel or refund it. If Amazon cancels it while Pending, there is nothing to refund.

## Cause

Seller Central does not show buyer email addresses (Buyer-Seller Messaging uses encrypted addresses), so orders cannot be found by email; the order ID is needed. The orders were also in Pending status, where Amazon is still verifying payment and the seller cannot confirm or cancel; Amazon later cancelled them, leaving nothing to refund in Seller Central.

## Fix

1. Ask the requester for the order ID; buyer email does not find orders in Manage Orders.
2. Look the order up in Manage Orders and check its status.
3. If the order is Pending, do not ship, cancel or refund; wait until it leaves Pending.
4. If Amazon cancels it while Pending, there is nothing to refund in Seller Central; tell the requester.
5. Once it leaves Pending, cancel or refund it through the order (operator approval needed).

## Verify

Manage Orders shows the order as cancelled, or the refund shows on the order after approval.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/047-pending-orders-G40571.md`
- First-party: `Amazon Seller Help/articles/053-issue-refunds-and-concessions-for-seller-fulfilled-orders-GU7K5N5GUP67M4X9.md`
- First-party: `Amazon Seller Help/articles/043-communicate-with-buyers-using-buyer-seller-messages-G200389080.md`
- Also in: `MAG SOPs/catalog/catalog-sop-customer-service-buyer-messages-refund-and-replacement.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The first-party pages cover pending orders and refunds separately; the order-ID requirement because buyer email is masked is net new.
- Existing coverage: full (`Amazon Seller Help/articles/049-manage-orders-faq-G69124.md`, `Amazon Seller Help/articles/053-issue-refunds-and-concessions-for-seller-fulfilled-orders-GU7K5N5GUP67M4X9.md`, `MAG SOPs/catalog/catalog-sop-customer-service-buyer-messages-refund-and-replacement.md`, `Amazon Seller Help/articles/047-pending-orders-G40571.md`, `Amazon Seller Help/articles/041-the-order-process-G200200040.md`).
