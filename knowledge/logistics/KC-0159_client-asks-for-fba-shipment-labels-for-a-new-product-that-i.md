---
id: KC-0159
title: "Client asks for FBA shipment labels for a new product that is not yet listed: create and approve the listing first"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["shipping labels for new product", "cannot create shipment for new product", "new product listing awaiting approval before shipment", "FBA labels for unlisted product", "launch delayed waiting for listing approval"]
error_text: []
asked_as: ["The client asks the agency for FBA shipment labels for an inbound of a product that has never been listed on Amazon and needs them urgently to ship."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0159"
---

## Question

The client asks the agency for FBA shipment labels for an inbound of a product that has never been listed on Amazon and needs them urgently to ship.

## Answer

Before promising FBA labels for a new product, check that the product already has an accepted listing with an FBA SKU; Send to Amazon cannot build a shipment without one. List the product as soon as the client shares the product information, even without images, and build the listing wait into the launch plan, because it can take days.

## Cause

An FBA shipment is built from existing listings: Send to Amazon only lets you select SKUs that already exist on an ASIN and are set to FBA. The product had no listing yet, so the agency first had to list it from the product information sheet and wait for Amazon to accept the new listing before the shipment and labels could be created. The wait nearly delayed the launch; how long it takes was a single observation, not a rule.

## Fix

1. Collect the product information sheet (title, attributes, identifiers, dimensions); images can follow later if the client does not have them yet.
2. Create the listing in Seller Central as an FBA SKU and wait until Amazon accepts it and the SKU appears in inventory.
3. Create the FBA shipment in Send to Amazon for the new SKU (confirmation needs operator approval).
4. Download the box and unit labels and send them to the client for review.

## Verify

The new SKU appears in Manage All Inventory as an FBA SKU and can be added in Send to Amazon; the client confirms the labels print correctly.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the prerequisite that a new product needs an approved, active listing before any FBA shipment or label request, and that approval time belongs in the launch plan.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `Amazon Seller Help/articles/143-product-detail-page-rules-G200390640.md`).
