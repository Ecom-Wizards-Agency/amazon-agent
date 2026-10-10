---
id: KC-0112
title: "Inbound shipment to FBA appears that nobody created: AWD automatic replenishment"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > AWD inventory dashboard (FBA Replenishment status: Active / Manual); Shipments"
surface_verified: false
symptom_keywords: ["inbound shipment I did not create", "units pre-selling but we shipped nothing", "who requested this FBA shipment", "AWD replenishment to FBA", "unexpected FBA inbound"]
error_text: []
asked_as: ["The brand owner saw units arriving at FBA and pre-selling, although the team had not shipped anything to Amazon, and asked who requested the shipment."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0112"
---

## Question

The brand owner saw units arriving at FBA and pre-selling, although the team had not shipped anything to Amazon, and asked who requested the shipment.

## Answer

When FBA shows inbound or pre-sellable units that nobody shipped, check AWD first. AWD automatically replenishes inventory into FBA fulfillment centers, so these transfers appear without a seller-created shipment. Tell stakeholders that this is the intended AWD behaviour, and check any AWD stock with a known labelling problem before it moves.

## Cause

The inventory was enrolled in Amazon Warehousing and Distribution (AWD). AWD replenishes FBA fulfillment centers automatically, so Amazon creates the AWD-to-FBA transfer without a seller-created shipment.

## Fix

1. Open the AWD inventory dashboard and check whether the SKU has AWD inventory and automatic replenishment enabled.
2. Match the unexpected inbound quantity to an AWD-to-FBA replenishment transfer rather than a Send to Amazon shipment.
3. If the AWD stock may have a known defect (for example wrong unit barcodes), check those units before they reach FBA and decide whether to pause replenishment for that SKU.

## Verify

The inbound units appear as an AWD replenishment to FBA, and no seller-created Send to Amazon shipment exists for them.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that an unexpected FBA inbound nobody created is AWD automatic replenishment; the AWD help page states replenishment but no unit maps the symptom to it.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`).
