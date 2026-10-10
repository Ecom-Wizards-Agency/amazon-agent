---
id: KC-0210
title: "New brand has no product barcodes: buy GS1 UPCs or list with a GTIN exemption and FNSKU"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: false
surface: "GS1 / Seller Central > Add a product"
surface_verified: false
symptom_keywords: ["no UPC codes for new products", "GS1 or GTIN exemption", "do we need barcodes to sell on Amazon", "FNSKU instead of UPC", "new brand without barcodes"]
error_text: []
asked_as: ["A new brand preparing its first Amazon listings had no product barcodes of any kind and asked which option was easier: buying barcodes or listing without them."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md"]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0210"
---

## Question

A new brand preparing its first Amazon listings had no product barcodes of any kind and asked which option was easier: buying barcodes or listing without them.

## Answer

A brand with no barcodes chooses between licensing GS1 UPCs and requesting a GTIN exemption with Amazon FNSKU labels. GS1 is faster to start and reusable in other retail, while the exemption route is free but waits on brand setup and approval. Pick GS1 when launch speed matters, and never use a barcode that is not licensed to the brand.

## Cause

Amazon needs a product ID to create a listing and a scannable barcode to identify units. Without GS1 barcodes the brand must first create the account and brand and obtain a GTIN exemption, then use Amazon's FNSKU labels, which adds time.

## Fix

1. Option A: license GS1 barcodes, assign one per SKU and print them on the packaging; the same barcodes work for other retail channels later.
2. Option B: set up the seller account and brand, request a GTIN exemption (Catalog > Add products > I'm adding a product not sold on Amazon > I don't have a product ID > Apply to sell), create the listings and label units with Amazon FNSKU barcodes. This costs nothing but waits on setup and approval. The thread estimated about a week extra; the MAG SOP expects an exemption decision within 48 hours.
3. The exemption application needs real photos of the product and packaging, with permanent branding that matches the brand name entered.
4. When launch speed matters, choose GS1.

## Verify

Each SKU has a unique GS1 UPC that matches the listing product ID, or the brand shows an approved GTIN exemption for the category.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Frames GS1 versus GTIN exemption as a speed-versus-cost launch decision for a brand with no barcodes, which the SOPs cover only as separate procedures.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`).
