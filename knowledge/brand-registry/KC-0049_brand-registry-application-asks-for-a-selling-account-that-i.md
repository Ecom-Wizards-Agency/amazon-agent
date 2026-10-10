---
id: KC-0049
title: "Brand Registry application asks for a selling account that is still under review: you can enroll the brand without it"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-client-onboarding, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "brandregistry.amazon.com enrollment"
surface_verified: false
symptom_keywords: ["brand registry before seller account approved", "wait for seller account brand registry", "brand registry without seller central", "brand registry seller account pending", "enroll brand neither seller nor vendor"]
error_text: []
asked_as: ["The client had applied for a seller account and asked whether they must wait for its approval before continuing the Brand Registry application."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/215-brand-registry-application-step-by-step-guide-GRWHD3TXWAVKUT86.md", "Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0049"
---

## Question

The client had applied for a seller account and asked whether they must wait for its approval before continuing the Brand Registry application.

## Answer

Do not hold a Brand Registry application until the seller account is approved; the two are separate accounts. Pick "Neither" for the selling relationship if needed, then link the seller account under Manage selling accounts once it is approved.

## Cause

Brand Registry and Seller Central are separate accounts. The enrollment form lets the applicant choose "Neither" for the selling relationship, so the brand can be registered without a connected seller or vendor account.

## Fix

1. Continue the Brand Registry application while the seller account is under review.
2. In the selling-partner question, select Neither if the seller account is not yet usable.
3. After the seller account is approved, connect it to the brand under Manage selling accounts to receive the brand selling benefits.

## Verify

The Brand Registry application status shows submitted or approved, and after seller approval the seller account appears under Manage selling accounts for the brand.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/215-brand-registry-application-step-by-step-guide-GRWHD3TXWAVKUT86.md`
- First-party: `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms the practical answer that a Brand Registry application need not wait for seller account approval; the step-by-step guide already states the Neither option.
- Existing coverage: full (`Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `Amazon Seller Help/articles/215-brand-registry-application-step-by-step-guide-GRWHD3TXWAVKUT86.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`).
