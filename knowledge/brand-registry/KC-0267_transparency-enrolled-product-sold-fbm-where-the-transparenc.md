---
id: KC-0267
title: "Transparency-enrolled product sold FBM: where the Transparency codes for seller-fulfilled orders come from"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central Transparency / Manage Orders"
surface_verified: false
symptom_keywords: ["transparency codes for FBM orders", "transparency labels merchant fulfilled", "warehouse needs transparency codes", "print transparency codes seller fulfilled"]
error_text: []
asked_as: ["The brand's warehouse was shipping seller-fulfilled orders of a Transparency-enrolled product and asked which Transparency codes to stick on the packages."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0267"
---

## Question

The brand's warehouse was shipping seller-fulfilled orders of a Transparency-enrolled product and asked which Transparency codes to stick on the packages.

## Answer

Transparency applies to seller-fulfilled orders too, so a warehouse shipping FBM orders of an enrolled product needs unique codes from the brand's Transparency account. Generate a batch, send the warehouse the CSV or PDF and label each unit. Expect to enter the shipped unit's code when you confirm the order in Seller Central. Size the batch to open orders plus a buffer so shipments do not stall.

## Cause

Products enrolled in Transparency cannot be sold without a valid code on every unit, whether Amazon fulfils the order or the seller ships it. The warehouse shipping seller-fulfilled orders therefore needs codes from the brand's Transparency account. The thread's answer was that the shipped unit's code is pasted into Seller Central at shipment confirmation. That answer was tentative ('I think') and shown only in a screenshot, and no local capture confirms the field.

## Fix

1. In Transparency, generate a batch of codes for the enrolled product sized to the open and expected seller-fulfilled orders.
2. Download the batch as CSV (for entering codes as text) or PDF (for printing labels) and send it to the warehouse.
3. The warehouse applies one unique code label per unit shipped.
4. When confirming shipment of each seller-fulfilled order, enter the shipped unit's code in the Transparency code field if Seller Central asks for one. This field was seen only in a screenshot; verify it live before writing it into a procedure.

## Verify

Every shipped unit carries a code from the downloaded batch and the seller-fulfilled orders confirm in Seller Central. The thread did not record a confirmed shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds how seller-fulfilled warehouses get Transparency codes: a downloaded CSV or PDF batch, with the shipped unit's code pasted into Seller Central at shipment confirmation.
- Existing coverage: partial (`Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `MAG SOPs/catalog/catalog-sop-request-a-bin-check-to-amazon.md`, `sop-drafts/2026-06-07_daily-amazon-account-health-check.md`).
