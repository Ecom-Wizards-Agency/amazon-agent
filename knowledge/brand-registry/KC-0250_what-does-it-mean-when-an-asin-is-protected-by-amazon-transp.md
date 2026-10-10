---
id: KC-0250
title: "What does it mean when an ASIN is protected by Amazon Transparency, for the brand and for other sellers?"
kind: reference
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: "Transparency program"
surface_verified: false
symptom_keywords: ["what is amazon transparency", "transparency codes required", "stop other sellers using our ASIN", "transparency protected ASIN"]
error_text: []
asked_as: ["A client asked about the Transparency program; the agency explained that the enrolled products were already protected and no one could sell on those ASINs without a Transparency code."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md"]
supersedes: []
contradicts: []
observed: 2024-11
review_by: 2027-10
provenance: "ledger:KC-0250"
---

## Question

A client asked about the Transparency program; the agency explained that the enrolled products were already protected and no one could sell on those ASINs without a Transparency code. The original question is not in the record.

## Answer

Transparency protects an ASIN by requiring a unique code on every unit, whoever sells or fulfils it. Once an ASIN is protected, other sellers cannot sell on it without codes from the brand, which makes it a strong anti-hijacker measure. The brand must label all of its own units as well, or Amazon sets them aside.

## Cause

Products enrolled in Transparency carry unique serial codes; Amazon blocks any unit without a valid code, so no seller can sell on an enrolled ASIN unless it can supply codes from the brand.

## Fix

1. Identify which ASINs are enrolled in Transparency for the brand.
2. Explain that every unit sold on those ASINs, FBA or seller-fulfilled, needs a valid Transparency code.
3. Make sure the brand's own production and FBA prep apply codes to every unit before shipping, otherwise its own inventory is put aside too.

## Verify

The ASIN shows as protected in the Transparency portal and unauthorized offers can no longer ship without a code.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the practical reading of a Transparency enrollment email: protected ASINs lock out codeless sellers, including the brand's own uncoded units.
- Existing coverage: full (`Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`, `Advertising Help After Login/articles/219-amazon-dsp-inventory-policies-GUYW2GE498ANTH8Y.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`).
