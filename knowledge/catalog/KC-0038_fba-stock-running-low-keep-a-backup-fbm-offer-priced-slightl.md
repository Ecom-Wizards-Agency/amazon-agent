---
id: KC-0038
title: "FBA stock running low: keep a backup FBM offer priced slightly above FBA"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["FBM backup offer", "FBA about to stock out", "switch buy box to FBM", "dual FBA FBM offers", "keep listing live during stockout"]
error_text: []
asked_as: ["The client asked to close extra merchant-fulfilled offers to sell through FBA stock, but keep one merchant-fulfilled offer active as a stock-out backup during a sales event."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md", "MAG SOPs/catalog/factors-that-affect-a-seller-s-chance-to-win-the-buy-box.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0038"
---

## Question

The client asked to close extra merchant-fulfilled offers to sell through FBA stock, but keep one merchant-fulfilled offer active as a stock-out backup during a sales event.

## Answer

Keep a backup merchant-fulfilled offer on key ASINs and price it slightly above the FBA offer, so FBA normally wins the Buy Box. Switch to the backup only when FBA is about to stock out, then switch back promptly, because the faster FBA delivery promise lifts conversion.

## Cause

Not a fault. A merchant-fulfilled offer on the same ASIN keeps the listing buyable if FBA runs out, and pricing it slightly above the FBA offer keeps the FBA offer winning the Buy Box. In a sibling thread, the team switched the Buy Box to the merchant-fulfilled offer when FBA was nearly out, then switched back because FBA delivery was faster and converted better.

## Fix

1. Close merchant-fulfilled offers you do not need so orders draw on FBA stock.
2. Keep one merchant-fulfilled offer active on the ASIN as a backup, priced slightly above the FBA offer so FBA keeps the Buy Box.
3. Monitor FBA available units, especially before and during sales events.
4. If FBA is about to run out, make the merchant-fulfilled offer the Buy Box winner (for example by adjusting its price).
5. Switch back to FBA as soon as FBA stock is safe, because the faster FBA delivery promise converts better.

## Verify

The product page shows the FBA offer in the Buy Box with the merchant-fulfilled offer listed as another seller option, and stock never reaches zero on the listing.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Also in: `MAG SOPs/catalog/factors-that-affect-a-seller-s-chance-to-win-the-buy-box.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the backup-offer pricing pattern (FBM priced slightly above FBA) and when to switch the Buy Box between them around a stock-out.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
