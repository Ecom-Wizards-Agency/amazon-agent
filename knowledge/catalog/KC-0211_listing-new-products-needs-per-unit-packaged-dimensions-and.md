---
id: KC-0211
title: "Listing new products needs per-unit packaged dimensions and weight, not master carton values"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central Add a Product / listing upload (package dimensions and weight)"
surface_verified: false
symptom_keywords: ["package dimensions for new listing", "unit dimensions vs master carton", "what weight to enter for listing", "supplier sent carton dimensions", "GTIN and dimensions for new product"]
error_text: []
asked_as: ["The client asked for GTINs for new products and sent a sheet with SKUs, noting the products differ in box size and weight."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-package-dimensions-and-weight-update.md", "MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0211"
---

## Question

The client asked for GTINs for new products and sent a sheet with SKUs, noting the products differ in box size and weight. The agency needed dimensions and weight to list them for FBM and FBA and create a shipping plan.

## Answer

When onboarding new products, ask the supplier for the packaged dimensions and weight of one sellable unit per variant, and say explicitly that you do not want the master carton. Collect carton size and units per carton separately for the shipping plan. You can list with provisional values and correct them when the packaging changes. FBA fees are calculated from the item package values, so carton figures on a listing produce wrong fees.

## Cause

The supplier's sheet did not make clear which values belonged to the sellable unit. A listing needs the package dimensions and weight of one sellable unit including its own packaging. Carton dimensions and units per carton are only used later for the shipment boxes. FBA fees are based on the item package weight and dimensions.

## Fix

1. Assign GTINs to each new SKU and share the barcode files.
2. Ask the supplier for each variant: length, width and height of the packaged sellable unit and its total packaged weight, in cm and grams, stating clearly that this is not the master carton.
3. Ask whether the values are identical across designs that share packaging, so one set can cover them.
4. Separately collect units per carton and carton dimensions for the shipping plan.
5. Create the listings for FBM and FBA; update dimensions later if packaging contents change.

## Verify

Each listing shows package dimensions and weight that match one packaged unit, and FBA fee previews look plausible for that size tier.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-package-dimensions-and-weight-update.md`
- Also in: `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that new listings need per-unit packaged dimensions and weight in metric, collected separately from master carton data.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-package-dimensions-and-weight-update.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`).
