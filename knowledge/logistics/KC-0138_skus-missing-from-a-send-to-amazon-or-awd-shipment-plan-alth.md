---
id: KC-0138
title: "SKUs missing from a Send to Amazon or AWD shipment plan although they exist in All Listings: the offers are merchant-fulfilled"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > All Listings report (fulfillment-channel); Send to Amazon"
surface_verified: false
symptom_keywords: ["SKUs not showing in Send to Amazon", "AWD shipment missing SKUs", "FBM listing cannot be sent to FBA", "fulfillment channel DEFAULT", "create -FBA SKU for existing ASIN"]
error_text: [DEFAULT, AMAZON_NA]
asked_as: ["A shipment meant to stock an account moving from merchant fulfilment to FBA and AWD covered only part of the SKUs the brand had sent to its 3PL."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md", "MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0138"
---

## Question

A shipment meant to stock an account moving from merchant fulfilment to FBA and AWD covered only part of the SKUs the brand had sent to its 3PL. The account lead asked why the other SKUs were not in the FBA/AWD plan.

## Answer

When SKUs that exist in the catalog do not appear in a Send to Amazon or AWD plan, check the fulfillment channel in the All Listings report first. Merchant-fulfilled offers (DEFAULT) cannot be shipped in. Convert them to FBA, or add a separate FBA SKU on the same ASIN, for every SKU in the physical stock, then rebuild the plan. How to split the rebuilt plan between FBA and AWD is a stock decision, not part of the fix.

## Cause

The SKUs existed, but the All Listings report showed most of them with fulfillment-channel DEFAULT (merchant-fulfilled); only a few were AMAZON_NA. The listings had been created for FBA and later switched to FBM, and an FBA counterpart had been created only for some. Send to Amazon only offers SKUs with an Amazon-fulfilled offer, so the rest could not be added.

## Fix

1. Download the All Listings report and check the fulfillment-channel column for every SKU intended for the shipment: DEFAULT means merchant-fulfilled, and AMAZON_NA (or the regional AMAZON_ value) means FBA. 2. For each SKU without an Amazon-fulfilled offer, either convert the offer to FBA (Convert to Fulfilled by Amazon in Manage Inventory) or, to keep the FBM offer live, create a second SKU on the same ASIN with an -FBA suffix as an FBA offer. 3. Create FBA counterparts for every SKU physically in the inbound stock, not only the ones in the first request. 4. Rebuild the shipment once the new FBA SKUs show in Send to Amazon (operator approval before confirming). One option the agency used is one carton per SKU direct to FBA, so each ASIN goes live, with the remainder to AWD. 5. Per the agency logistics operator, keep mixed-SKU cartons out of the AWD leg; the AWD shipping requirements page is not captured locally, so confirm it live.

## Verify

Every intended SKU appears with an Amazon fulfillment channel in All Listings and is selectable in Send to Amazon; the rebuilt plan lists all SKUs.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOPs explain creating FBA or dual MFN/FBA offers, but not the diagnosis that missing shipment SKUs are merchant-fulfilled offers visible as DEFAULT in the All Listings fulfillment-channel column.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
