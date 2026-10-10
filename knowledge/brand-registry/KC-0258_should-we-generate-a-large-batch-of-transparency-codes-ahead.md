---
id: KC-0258
title: "Should we generate a large batch of Transparency codes ahead of production, or request them only as needed?"
kind: decision-aid
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Transparency portal > Code Requests"
surface_verified: false
symptom_keywords: ["how many Transparency codes to order", "Transparency codes unused", "do Transparency codes expire", "Transparency code cost", "request more Transparency codes"]
error_text: []
asked_as: ["The brand's logistics contact asked for a large new batch of Transparency codes for an upcoming production run."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0258"
---

## Question

The brand's logistics contact asked for a large new batch of Transparency codes for an upcoming production run. The agency lead questioned it because a large stock of previously issued codes was still unused.

## Answer

Request Transparency codes for the next production run only, not far ahead of it. In the agency's experience each code carries a fee and codes do not expire, and new codes can be requested within about half an hour, so ordering early ties up cost for no benefit. Use up unused codes first and never print the same code on two units.

## Cause

Each Transparency code carries a per-code fee in the agency's account experience, and the thread states that codes do not expire. The Transparency MAG SOP says codes can be requested up to 100,000 per ASIN, with a ready email in about 30 minutes. Generating codes far ahead of the units they will label ties up cost for no benefit. Neither the fee nor the no-expiry claim appears in the local first-party capture.

## Fix

1. Count the codes already issued and not yet printed on units before requesting a new batch.
2. Use the unused stock first, and make sure no code is printed twice; every unit needs its own unique code.
3. Request new codes in the Transparency portal under Code Requests only when the unused stock will not cover the next production run.
4. Agree who requests codes for the brand, so production asks that person instead of ordering batches on its own.

## Verify

Before the next print run, the number of unused unique codes on hand covers the planned unit count, and no code appears twice in the print files.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The MAG SOP covers how to request codes and the one-code-per-unit rule but not the per-code fee or the decision to request only per production run.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`).
