---
id: KC-0173
title: "FBM offer keeps taking orders even though the same ASIN has plenty of FBA stock: raise the FBM price or set FBM quantity to zero, including bundle SKUs"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Manage All Inventory"
surface_verified: false
symptom_keywords: ["FBM orders despite FBA stock", "merchant fulfilled offer winning Buy Box over FBA", "stop FBM offer selling", "make FBM out of stock", "FBM and FBA offer on same ASIN"]
error_text: []
asked_as: ["The client noticed seller-fulfilled orders on an ASIN that had a high FBA stock level and asked why the FBM offer was selling; on another product the client asked to make the FBM offer and every bundl"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md", "MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0173"
---

## Question

The client noticed seller-fulfilled orders on an ASIN that had a high FBA stock level and asked why the FBM offer was selling; on another product the client asked to make the FBM offer and every bundle containing it out of stock urgently after FBA was replenished.

## Answer

If an ASIN with both FBA and FBM offers keeps taking FBM orders while FBA stock is healthy, Amazon is featuring the FBM offer for some shoppers; the trigger was not established, and delivery speed and price are the likely factors. Raise the FBM price above the FBA offer to keep it as a backup, or set the FBM quantity to 0 to stop it. Repeat the change on every bundle SKU that ships the same item, because each one has its own FBM quantity. Before zeroing FBM, check that FBA available and inbound units cover demand, or the ASIN can go out of stock.

## Cause

When one ASIN carries both an FBA and an FBM offer from the same seller, Amazon can feature the FBM offer for some shoppers. The agency guessed the FBM offer's shipment date was the reason and raised the FBM price; the thread does not establish the featured-offer logic or confirm that the price change stopped the FBM orders. Bundle SKUs that contain the same item have their own FBM offers and quantities, so zeroing only the single-item SKU leaves them sellable.

## Fix

1. In Manage All Inventory, find both offers for the ASIN and confirm the FBA offer has available units.
2. To keep the FBM offer as a backup, raise its price above the FBA offer so the FBA offer is more likely to be featured; watch the next orders to confirm.
3. To stop FBM sales completely, set the FBM offer quantity to 0.
4. Search for every bundle or multipack SKU that contains the item and set their FBM quantities to 0 as well.
5. Have a second person check that each FBM SKU shows 0 available, and check that FBA available plus inbound units cover the coming demand; if they do not, expect a stockout until the inbound units arrive.

## Verify

New orders for the ASIN arrive as Amazon-fulfilled; every FBM SKU for the item and its bundles shows 0 available or a price above the FBA offer.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Also in: `MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The covering pages explain dual FBM and FBA offers and FBM deactivation, not how to stop a featured FBM offer from taking orders while FBA has stock, including bundle SKUs.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`).
