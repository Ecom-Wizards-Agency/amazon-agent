---
id: KC-0149
title: "New FBM listings are not live and have no active product page"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Manage All Inventory / FBM offer quantity"
surface_verified: false
symptom_keywords: ["new FBM listing not active", "FBM SKU no product page", "listing inactive no stock", "FBM offer out of stock new SKU"]
error_text: []
asked_as: ["After new FBM SKUs were created, the team could not find an active product page and asked whether the listings were live."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/099-common-reasons-you-cannot-find-your-handmade-listings-GRCWJ4KHBNQ3SNTB.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0149"
---

## Question

After new FBM SKUs were created, the team could not find an active product page and asked whether the listings were live.

## Answer

New FBM offers stay inactive and have no live product page until they carry stock quantity. Connect the 3PL, add or sync the quantity, then confirm the offer is active before adding the SKUs to ads.

## Cause

An FBM offer created without a quantity has zero available stock and shows as inactive (out of stock), so shoppers cannot buy it. It stays inactive until a quantity is entered in Seller Central or synced from the fulfilment integration.

## Fix

1. Confirm the 3PL is connected and holds stock for the new SKUs.
2. Add the FBM quantity in Seller Central or let the 3PL integration sync it.
3. Check that the offers turn active and the product pages load.
4. Add the new SKUs to the advertising campaigns once they are active.

## Verify

The SKUs show Active in Manage All Inventory with an available quantity above zero, and the product page loads and is buyable. Allow a few hours after the quantity is saved or synced before concluding the listing is still not live.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/099-common-reasons-you-cannot-find-your-handmade-listings-GRCWJ4KHBNQ3SNTB.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Names zero quantity as the reason new FBM offers have no live page, a different cause from the vacation-mode unit.
- Existing coverage: partial (`knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
