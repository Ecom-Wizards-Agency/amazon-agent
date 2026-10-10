---
id: KC-0223
title: "Launching with FBM before stock reaches Amazon: create both an FBM and an FBA offer on the same ASIN"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central listing creation (category flat file or Add a Product), offer fulfillment channel"
surface_verified: false
symptom_keywords: ["launch FBM then FBA", "two offers one ASIN FBA FBM", "do we need to send stock for FBA offer", "create FBM and FBA offer", "dual fulfillment new listing"]
error_text: []
asked_as: ["Before listing new products, the client asked whether the launch was still planned as FBM or whether stock had to be sent to Amazon for FBA offers to go live."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0223"
---

## Question

Before listing new products, the client asked whether the launch was still planned as FBM or whether stock had to be sent to Amazon for FBA offers to go live.

## Answer

You do not have to choose between FBM and FBA at launch: one ASIN can carry an FBM offer and an FBA offer under separate SKUs. Create the first offer, wait for the ASIN, then add the second offer to it so no duplicate ASIN is created. Sell FBM until the FBA stock is received.

## Cause

Not a fault. One ASIN can carry two offers under separate SKUs, one fulfilled by the merchant and one by Amazon, so the launch does not have to choose one channel.

## Fix

1. Collect product weight and dimensions, barcode (EAN), SKUs, images and A+ content from the client.
2. Create the first offer (FBM or FBA) and let the ASIN generate; do not create both offers at the same time, or two ASINs may be created with the same barcode.
3. Create the second offer with its own SKU, using the generated ASIN as the product ID; in the flat file set the fulfillment center ID to AMAZON_NA (or the regional equivalent) for FBA and DEFAULT for FBM.
4. Verify both offers in Manage All Inventory, and sell through the FBM offer until the FBA stock is received.

## Verify

Manage All Inventory shows two SKUs on the same ASIN, one fulfilled by the merchant and one by Amazon, and no duplicate ASIN with the same barcode.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Mostly covered by the multiple-offers SOP; adds the launch use of selling FBM until FBA stock arrives.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/compliance/KC-0001_fba-hazmat-review-blocks-a-battery-powered-kit-with-a-cosmet.md`, `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`).
