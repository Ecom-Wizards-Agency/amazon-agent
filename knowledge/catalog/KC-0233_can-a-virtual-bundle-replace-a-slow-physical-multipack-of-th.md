---
id: KC-0233
title: "Can a virtual bundle replace a slow physical multipack of the same product? No: virtual bundles need two or more different ASINs"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central virtual bundles; FBA inbound planning"
surface_verified: false
symptom_keywords: ["virtual bundle same ASIN", "multipack as virtual bundle", "pack of 3 separate ASIN stock", "why ship stock for the multipack", "bundle multiple units of one product"]
error_text: []
asked_as: ["A client contact asked why an inbound plan sent a large quantity of a physical 3-pack when the single unit is the same product, and whether the 3-pack should become a virtual bundle instead, since it "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md"]
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0233"
---

## Question

A client contact asked why an inbound plan sent a large quantity of a physical 3-pack when the single unit is the same product, and whether the 3-pack should become a virtual bundle instead, since it sold only a handful of units in 30 days.

## Answer

A physical multipack is a separate ASIN with separate FBA stock, so size its inbound from its own sales, not the single unit's. Do not plan to replace it with a virtual bundle of the same product: virtual bundles need at least two unique ASINs, and several units of one ASIN do not qualify. When a multipack barely sells, send only a small inbound that still fits whole cartons.

## Cause

A physical multipack is its own ASIN with its own FBA inventory, so Amazon does not draw it from the single-unit stock. Virtual bundles cannot fix this because they require at least two unique ASINs; several units of the same ASIN do not qualify.

## Fix

1. Treat the physical multipack as a separate ASIN and plan its FBA inbound from its own sales velocity, not the single unit's.
2. Cut the multipack inbound to what its recent sales support, after checking the case-pack size so the reduced quantity still ships in whole cartons.
3. Do not try to rebuild the multipack as a virtual bundle of one ASIN; a virtual bundle needs two or more different ASINs. Also check that virtual bundles exist in the marketplace at all (the MAG SOP lists them as US only).
4. If a multi-unit offer is still wanted without separate stock, check whether a multipack program is available in the marketplace before planning around it (not established in the thread).

## Verify

The inbound plan quantity for the multipack matches its own recent sales velocity and still ships in whole cartons.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the inbound-planning consequence: a slow physical multipack keeps its own FBA stock and cannot be swapped for a single-ASIN virtual bundle, so its inbound is cut to its own velocity.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-how-to-create-virtual-bundles.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`).
