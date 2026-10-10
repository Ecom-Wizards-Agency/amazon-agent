---
id: KC-0082
title: "Account owner cannot find where to confirm the tax address or KYC request Amazon is asking for"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central > Performance > Performance Notifications"
surface_verified: false
symptom_keywords: ["where do I confirm the tax address", "tax address confirmation Seller Central", "KYC reminder Amazon link", "cannot find verification request", "performance notification direct link"]
error_text: []
asked_as: ["The agency told the account owner that Amazon required a tax address confirmation."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md"]
related_sops: [sop-drafts/2026-06-07_daily-amazon-account-health-check.md]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0082"
---

## Question

The agency told the account owner that Amazon required a tax address confirmation. The owner replied they could not find where in Seller Central to confirm it and asked for a link. A later KYC verification reminder on the same account followed the same pattern.

## Answer

When Amazon asks for a tax address confirmation or KYC verification, send the account owner the direct link to the Performance Notification rather than describing where to click. Owners rarely open Performance Notifications, and identity and business verification has to come from the primary contact or business owner. Ask for a reply when done and check that the request has cleared.

## Cause

The request arrives as a Performance Notification, which account owners rarely open, so the owner could not find where to act on it. Amazon's verification page says the primary contact person or business owner must provide the identity and business documents, which is why the request was routed to the owner; the thread does not show whether an agency user could have completed the tax address confirmation.

## Fix

1. Open Performance > Performance Notifications in the correct account and marketplace and find the message asking for the tax address or KYC verification.
2. Copy the direct URL of that notification (it opens the message itself, under /performance/notifications/<id>).
3. Send that link to the account owner with a one-line description of what Amazon is asking for; the owner enters the tax or identity details.
4. Ask the owner to reply when done, then check the notification or Account Health page for the request to clear.

## Verify

The owner confirms the submission and the verification request no longer shows as open in Performance Notifications or on the Account Health page.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- Also in: `sop-drafts/2026-06-07_daily-amazon-account-health-check.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The verification page covers what documents Amazon wants, not that the request arrives as a Performance Notification whose direct link is the fastest way to route it to the account owner.
- Existing coverage: full (`Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/184-registration-requirements-by-store-G201468460.md`, `sop-drafts/2026-06-07_daily-amazon-account-health-check.md`, `Amazon Seller Help/articles/037-canada-digital-tax-reporting-G6JPYHKCN4YG943H.md`).
