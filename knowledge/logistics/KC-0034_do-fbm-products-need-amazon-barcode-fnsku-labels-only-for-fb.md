---
id: KC-0034
title: "Do FBM products need Amazon barcode (FNSKU) labels? Only for FBA; a 3PL may set its own identifier"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Settings > Fulfillment by Amazon > FBA Product Barcode Preference"
surface_verified: false
symptom_keywords: ["FNSKU label needed for FBM", "barcode labels merchant fulfilled", "do I need Amazon barcode for 3PL", "FBA labels only", "3PL item identifier"]
error_text: []
asked_as: ["A seller asked whether item barcode labels are needed when the product ships through a 3PL as seller-fulfilled instead of FBA."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md", "MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0034"
---

## Question

A seller asked whether item barcode labels are needed when the product ships through a 3PL as seller-fulfilled instead of FBA.

## Answer

Amazon barcode labels are an FBA requirement, not a seller-fulfilled one. When a 3PL ships seller-fulfilled orders, ask the 3PL which item identifier it needs, because that depends on its own receiving process. Keep FBA labelling decisions under the FBA barcode preference.

## Cause

Amazon barcode labels identify units in Amazon fulfillment centers, so the requirement applies only to FBA inventory. A 3PL fulfilling seller-fulfilled orders may still want its own per-item identifier for receiving and dispatch.

## Fix

1. Label units with the Amazon barcode (FNSKU) or use the manufacturer barcode per the FBA barcode preference only for inventory sent to FBA.
2. For seller-fulfilled stock held by a 3PL, ask the 3PL which identifier it requires (its own SKU label, the manufacturer barcode or none).
3. Record the 3PL requirement in the client profile so later shipments follow it.

## Verify

FBA inbound units carry the barcode the FBA preference requires, and the 3PL confirms it can receive and pick the seller-fulfilled stock with the agreed identifier.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: States that Amazon barcode labels are an FBA-only requirement and that a 3PL shipping seller-fulfilled orders sets its own identifier; local sources cover only the FBA barcode preference.
- Existing coverage: full (`knowledge/logistics/KC-0003_inbound-performance-defects-labeling-required-unscannable-ba.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
