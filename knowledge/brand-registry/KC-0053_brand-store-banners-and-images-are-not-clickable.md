---
id: KC-0053
title: "Brand Store banners and images are not clickable"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: "Brand Store builder (image tiles)"
surface_verified: false
symptom_keywords: ["brand store banners not clickable", "brand store image no link", "link brand store image to product", "brand store broken links", "hyperlink brand store tile to PDP"]
error_text: []
asked_as: ["The client found that no Brand Store banners were clickable on any page, even product-specific ones, and asked to link them to the right product pages."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/148-content-tiles-on-stores-GBX4ZFVHAKXKA5WM.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0053"
---

## Question

The client found that no Brand Store banners were clickable on any page, even product-specific ones, and asked to link them to the right product pages.

## Answer

Link every product-related image tile in a Brand Store to its product detail page, even when the tile only shows features. Shoppers click on banners for products they want, and an unlinked tile is a dead end. Image tiles do not link by default, so check links tile by tile after every store edit.

## Cause

Image tiles in a Brand Store carry no link unless one is set on the tile; some links were also missing or broken.

## Fix

1. Open the Brand Store builder and go through every page.
2. For each image or banner tile that relates to a product, set its link to that product's detail page (or the relevant Store page).
3. Fix any broken or missing links found on the live store.
4. Submit the store for moderation and recheck the live store after it publishes.

## Verify

Clicking each banner on the live Brand Store, on desktop and mobile, opens the intended product detail page.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/148-content-tiles-on-stores-GBX4ZFVHAKXKA5WM.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Turns the image-tile link option into a store QA rule: link every product-related tile to its detail page.
- Existing coverage: full (`MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md`, `Advertising Help After Login/articles/205-add-the-live-shopping-tile-to-your-brand-store-and-create-a-livestream-beta-GQTCJ84S424G6EJ5.md`, `Advertising Help After Login/articles/200-brand-store-all-deals-page-GN8ENNYBFQQUTG7K.md`, `Advertising Help After Login/articles/148-content-tiles-on-stores-GBX4ZFVHAKXKA5WM.md`, `Advertising Help After Login/articles/133-understand-the-ai-experience-on-brand-stores-beta-G7VRGNH27HX7TZFW.md`).
