---
id: KC-0044
title: "Detail page shows seller-fulfilled although FBA stock exists: a cheaper FBM offer on the same ASIN wins the Featured Offer"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > Manage All Inventory (offers per ASIN, price and sale price)"
surface_verified: true
symptom_keywords: ["listing shows shipped by seller not Amazon", "FBA stock but FBM offer in buy box", "featured offer goes to my own FBM offer", "one pack ships FBA other pack FBM", "duplicate FBA and FBM offers same ASIN"]
error_text: ["updates can take up to 24 hours"]
asked_as: ["One pack size of a product showed as fulfilled by Amazon while another pack size showed as shipped by the seller, and the requester asked why."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/137-featured-offer-G37911.md"]
related_sops: ["MAG SOPs/catalog/factors-that-affect-a-seller-s-chance-to-win-the-buy-box.md", "MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0044"
---

## Question

One pack size of a product showed as fulfilled by Amazon while another pack size showed as shipped by the seller, and the requester asked why.

## Answer

When a product with FBA stock shows the seller as shipper, check for a second offer on the same ASIN. Your own cheaper FBM offer can win the Featured Offer over your FBA offer. Keep the FBA offer at the lower effective price, or deactivate the FBM offer while FBA stock lasts, then allow up to a day for the page to update.

## Cause

The affected ASIN had both an FBA offer and an FBM offer from the same seller. The FBM offer carried a lower sale price than the FBA regular price, so it won the Featured Offer and the detail page showed the seller as shipper even though FBA units were available.

## Fix

1. In Manage All Inventory, filter by the ASIN and list every offer (FBA and FBM SKUs) with its regular price, sale price and available quantity.
2. Identify which offer currently holds the Featured Offer and compare the effective prices.
3. Move the promotional sale price to the FBA offer and remove it from the FBM offer so the FBA offer is the lower effective price (operator approval needed for price changes).
4. Confirm both price submissions are accepted.
5. Recheck the detail page after processing; Seller Central notes updates can take up to 24 hours.

## Verify

After processing, the detail page Featured Offer shows the FBA offer as shipped by Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/137-featured-offer-G37911.md`
- Also in: `MAG SOPs/catalog/factors-that-affect-a-seller-s-chance-to-win-the-buy-box.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Shows that a seller's own cheaper FBM offer can take the Featured Offer from its FBA offer on the same ASIN and how to swap the sale price, which the multiple-offer SOP does not cover.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
