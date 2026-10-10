---
id: KC-0244
title: "Clicking the brand name on a product page opens search results instead of a brand page"
kind: diagnosis
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Product detail page byline"
surface_verified: false
symptom_keywords: ["brand link goes to search page", "brand name link not opening brand store", "byline goes to search results", "visit the store link missing", "brand byline not working"]
error_text: []
asked_as: ["A client clicked the brand name on its product listings and landed on a search results page instead of a brand page, even after setting a US delivery address."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/214-stores-byline-GUDC6TPJBUFSGVFG.md"]
related_sops: ["MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0244"
---

## Question

A client clicked the brand name on its product listings and landed on a search results page instead of a brand page, even after setting a US delivery address.

## Answer

If the brand name on a product page opens search results, check first whether the brand has a live, approved Brand Store; without one, the byline has no store to link to. Once the store is live and approved, Amazon creates the byline within 4 to 7 days. If a store exists and the byline still misroutes, check that the ASIN's brand name and brand ID match the Brand Registry record.

## Cause

The brand had no live Brand Store, so the byline had no store to link to and opened a brand search. That fallback was the agency's explanation; the help page states only that the byline is created after the store is live and approved and the brand is enrolled in Brand Registry.

## Fix

1. Set a local delivery address for the marketplace and re-check, to rule out a location effect.
2. Check in Seller Central whether a Brand Store exists and is live and approved.
3. If none exists, plan and publish a Brand Store; the byline is created automatically 4 to 7 days after the store is approved.
4. If a store exists but the byline still points elsewhere, follow the byline fix procedure.

## Verify

The product page shows a "Visit the ... Store" byline that opens the brand's store.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/214-stores-byline-GUDC6TPJBUFSGVFG.md`
- Also in: `MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Confirms that a missing Brand Store, not the delivery location, makes the byline fall back to search results.
- Existing coverage: full (`MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md`, `Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md`, `Advertising Help After Login/articles/200-brand-store-all-deals-page-GN8ENNYBFQQUTG7K.md`, `Advertising Help After Login/articles/214-stores-byline-GUDC6TPJBUFSGVFG.md`, `Advertising Help After Login/articles/205-add-the-live-shopping-tile-to-your-brand-store-and-create-a-livestream-beta-GQTCJ84S424G6EJ5.md`).
