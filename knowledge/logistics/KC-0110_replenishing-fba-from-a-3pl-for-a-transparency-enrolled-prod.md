---
id: KC-0110
title: "Replenishing FBA from a 3PL for a Transparency-enrolled product: hold the shipment until every unit carries a Transparency code"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Brand Registry > Transparency (code generation); Seller Central > Send to Amazon"
surface_verified: false
symptom_keywords: ["transparency codes 3PL shipment", "FBA replenishment transparency", "units without transparency code", "3PL to FBA transfer transparency", "hold shipment transparency labels"]
error_text: []
asked_as: ["A 3PL created a replenishment shipment to FBA to cut its storage cost, but the products are enrolled in Transparency and the stock at the 3PL had no codes."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", "MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0110"
---

## Question

A 3PL created a replenishment shipment to FBA to cut its storage cost, but the products are enrolled in Transparency and the stock at the 3PL had no codes. Should the shipment go out?

## Answer

Do not ship Transparency-enrolled products to FBA until every unit carries a valid Transparency code; units without one are set aside. Get the exact quantity from the 3PL, generate codes for it, and rebuild the shipment around the coded units only. Count the labelling cost when you decide whether moving stock from a 3PL into FBA saves money.

## Cause

Products enrolled in Transparency cannot be sold without a valid code on every unit; units without one are set aside for investigation. Stock held at a 3PL without codes therefore cannot go to FBA as is, and the 3PL labelling work adds cost to the transfer.

## Fix

1. ["1. Before approving a 3PL-to-FBA shipment, check whether any SKU in it is enrolled in Transparency.", "2. Hold the shipment until codes are on every unit, or replenish from stock you have confirmed already carries codes.", "3. Ask the 3PL for the exact unit quantity per SKU it will send.", "4. Generate Transparency codes for that quantity and send them to the 3PL to apply.", "5. Cancel or replace the original shipment with one that contains only the coded units (operator approval before cancelling).", "6. Share the box labels with the 3PL and collect tracking.", "7. Include the labelling cost when comparing 3PL storage against moving stock into FBA."]

## Verify

Every unit in the new shipment carries a Transparency code, and the shipment receives without units set aside for missing codes.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No matched unit or SOP covers holding a 3PL-to-FBA replenishment until Transparency codes are applied; the coverage matches were on generic words.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/README.md`).
