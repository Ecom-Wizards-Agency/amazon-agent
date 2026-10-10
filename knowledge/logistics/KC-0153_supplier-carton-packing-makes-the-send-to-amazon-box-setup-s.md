---
id: KC-0153
title: "Supplier carton packing makes the Send to Amazon box setup slow: ask for one SKU per carton and one carton spec"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Packing details (Case packs vs Individual units)"
surface_verified: false
symptom_keywords: ["how to ask supplier to pack cartons for FBA", "case pack one SKU per carton", "same units per carton Send to Amazon", "master carton spec for shipment plan", "box contents for many sizes"]
error_text: []
asked_as: ["Before creating an FBA shipment for a multi-size product, the agency asked the supplier to pack master cartons so the shipment plan would be simple to build in Seller Central."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0153"
---

## Question

Before creating an FBA shipment for a multi-size product, the agency asked the supplier to pack master cartons so the shipment plan would be simple to build in Seller Central.

## Answer

Before creating an FBA shipment, ask the supplier to pack one SKU per carton with the same number of units in every carton and one carton size within Amazon's box size and weight limits. You can then set each SKU as a case pack in Send to Amazon with one spec and a carton count, instead of entering mixed boxes one by one. Collect the carton count per SKU and confirm unit barcodes are applied before you build the plan.

## Cause

Send to Amazon treats boxes with one SKU and a fixed quantity as case packs, which need one box size, weight and units-per-box entry per SKU. Mixed-SKU or uneven cartons must be entered box by box as individual units, which is slower and more error-prone.

## Fix

1. Ask the supplier or warehouse to pack exactly one SKU (one size or colour) per carton.
2. Ask for the same number of units in every carton and one carton size within Amazon's box limits (standard-size multi-unit boxes no more than 25 inches on any side and 50 lb); slight weight differences are acceptable.
3. Request the carton specs (dimensions, weight, units per carton), the number of cartons per SKU, and confirmation that unit barcodes are applied.
4. In Send to Amazon, set each SKU as a case pack with those specs and the carton count.
5. Send the generated box labels back to the supplier to apply to each carton before pickup.

## Verify

Every SKU in the shipment plan is set as a case pack, the total carton count matches the supplier list and each carton has its own box label.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The Send to Amazon SOP explains case packs versus individual units but not how to brief a supplier to pack one SKU and one carton spec per carton for a fast shipment plan.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`).
