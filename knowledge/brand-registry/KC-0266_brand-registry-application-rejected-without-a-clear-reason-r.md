---
id: KC-0266
title: "Brand Registry application rejected without a clear reason; resubmitting got it approved, then connect the selling account"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Brand Registry > Selling benefits > Manage selling roles"
surface_verified: false
symptom_keywords: ["brand registry application rejected", "resubmit brand registry", "brand representative only shows other account", "connect seller account to brand registry", "brand registry selling role"]
error_text: []
asked_as: ["The client's Brand Registry application was rejected; they resubmitted, it was approved, and the agency then wanted the seller account connected to the brand as Brand Representative, but the role form"]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/214-brand-registry-application-process-GN2GYQVPR7R4VMPB.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md", "Amazon Seller Help/articles/216-manage-brand-registry-application-issues-GJPGY8BRDAQUQV4V.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0266"
---

## Question

The client's Brand Registry application was rejected; they resubmitted, it was approved, and the agency then wanted the seller account connected to the brand as Brand Representative, but the role form only offered "Other account".

## Answer

After a Brand Registry application is approved, have the Administrator connect the seller account to the brand as Brand Representative so brand benefits apply. If the role form offers only "Other account", check the Connected tab before inviting by merchant token, because the account may already be linked. For a rejection, read the stated reason, then copy and correct the application; a resubmission without changes was approved once here, which is not a documented rule.

## Cause

The thread does not state the rejection reason. A plain resubmission was approved, and the agency lead attributed the different outcome to individual reviewers, which no help page states. The selling-role form showed only "Other account"; the agency then confirmed from the merchant token that the seller account was already connected to the brand.

## Fix

1. Read the rejection reason on the Brand applications page (click the case ID). If details need correcting, use Copy, correct them and submit. A resubmission without changes was approved once in this thread, but it is not a documented route.
2. After approval, the brand owner invites the agency user to Brand Registry, and the agency accepts.
3. The Administrator goes to Manage > Manage selling roles > Connect a selling partner account, chooses Seller Central and Brand Representative, then selects the seller account and the brand.
4. If only "Other account" is offered, check the Connected tab of Manage selling roles. The seller account may already be connected, in which case nothing more is needed.

## Verify

The Connected tab of Manage selling roles lists the seller account as Brand Representative for the brand.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/214-brand-registry-application-process-GN2GYQVPR7R4VMPB.md`
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- First-party: `Amazon Seller Help/articles/216-manage-brand-registry-application-issues-GJPGY8BRDAQUQV4V.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that an "Other account" only role form usually means the seller account is already connected, and that a plain resubmission can turn a rejection into approval.
- Existing coverage: partial (`Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/215-brand-registry-application-step-by-step-guide-GRWHD3TXWAVKUT86.md`).
