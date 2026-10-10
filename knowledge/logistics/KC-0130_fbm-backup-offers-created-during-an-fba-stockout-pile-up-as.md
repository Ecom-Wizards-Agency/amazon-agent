---
id: KC-0130
title: "FBM backup offers created during an FBA stockout pile up as unshipped orders: the warehouse system never received them"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [AU]
marketplace_inferred: false
surface: "Seller Central > Orders > Manage Orders > Unshipped (seller-fulfilled)"
surface_verified: true
symptom_keywords: ["FBM orders unshipped", "backup FBM SKU orders not fulfilled", "3PL not receiving merchant fulfilled orders", "FBA out of stock switch to FBM", "FBM orders missing in warehouse system"]
error_text: []
asked_as: ["During an FBA stockout the agency created simple FBM SKUs as a fallback."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md", "MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0130"
---

## Question

During an FBA stockout the agency created simple FBM SKUs as a fallback. Several seller-fulfilled orders then sat in Unshipped because the brand's outside warehouse could not see them in its system; one buyer had already asked for a refund over the delay.

## Answer

Before switching on FBM offers as a stockout fallback, confirm that the warehouse actually receives seller-fulfilled orders, either through an integration or a named person who pulls them daily. Watch the Unshipped tab from the first day, ship the backlog with the fastest option and upload tracking, and switch the FBM offers off as soon as FBA stock is live again.

## Cause

The FBM SKUs were created directly in Seller Central with no connection to the warehouse's order integration. Nobody agreed beforehand who would pull FBM orders and upload tracking, so Amazon received the orders but the warehouse never did.

## Fix

1. Open Orders > Manage Orders and filter Unshipped seller-fulfilled orders.
2. Enter the open orders manually in the warehouse system and request the fastest shipping option.
3. Upload tracking for each order in Seller Central as soon as the warehouse provides it.
4. Turn the FBM offers off (or set quantity to zero) once FBA stock is available again, and check that new orders route to FBA.
5. Before enabling FBM again, agree in writing who receives FBM orders, how they reach the warehouse, and who confirms shipment with tracking.

## Verify

Unshipped seller-fulfilled orders drop to zero, each has valid tracking, and new orders after FBA restock show as fulfilled by Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Existing SOPs cover manual FBM confirmation, but none warns that FBM fallback offers bypass the warehouse order integration and leave orders unshipped.
- Existing coverage: full (`knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
