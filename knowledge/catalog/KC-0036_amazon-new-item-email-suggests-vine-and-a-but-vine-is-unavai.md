---
id: KC-0036
title: "Amazon new-item email suggests Vine and A+ but Vine is unavailable without an FBA offer"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Advertising > Vine; Amazon new-item recommendation email"
surface_verified: false
symptom_keywords: ["Vine not available FBM", "can I use Vine without FBA", "grow new item sales email", "Vine eligibility"]
error_text: ["Take these actions today to grow new item sales!"]
asked_as: ["Amazon emailed recommended actions to grow new-item sales; the agency noted the brand already had Premium A+ and that Vine only works with FBA."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-vine-setup.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0036"
---

## Question

Amazon emailed recommended actions to grow new-item sales; the agency noted the brand already had Premium A+ and that Vine only works with FBA.

## Answer

Treat Amazon's new-item recommendation emails as a checklist to compare with current status, not as new tasks. Vine needs an active FBA listing, a Brand Registry role and fewer than 30 reviews, so a merchant-fulfilled-only product cannot enroll until it has an FBA offer.

## Cause

Vine eligibility requires an active FBA listing, so a merchant-fulfilled-only product cannot be enrolled; the A+ recommendation was already met by the existing Premium A+ content.

## Fix

1. Check each recommended action against current status (existing A+ or Premium A+ content already satisfies the A+ suggestion).
2. Before enrolling in Vine, confirm the product has an active FBA offer, fewer than 30 reviews and a Brand Registry role.
3. If the product is merchant-fulfilled only, create an FBA offer first or skip Vine.

## Verify

The Vine enrollment page lists the product as eligible.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md`
- Also in: `MAG SOPs/catalog/catalog-sop-vine-setup.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links Amazon new-item recommendation emails to the Vine FBA prerequisite so a merchant-fulfilled product is not chased for Vine.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-vine-setup.md`, `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`, `Amazon Seller Help/articles/087-the-new-seller-guide-program-and-benefits-GFG4VRQK7CQLGRTM.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-errors-in-the-vine-program-on-seller-central.md`, `Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md`).
