---
id: KC-0046
title: "Do FBM units of a Transparency-enrolled product need Transparency codes too, or only FBA units?"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Brand Registry > Transparency; FBM order fulfilment"
surface_verified: false
symptom_keywords: ["Transparency codes FBM", "merchant fulfilled Transparency", "do I need Transparency for self-fulfilled orders", "Transparency only FBA", "Transparency code seller fulfilled"]
error_text: []
asked_as: ["While getting Brand Registry access to manage Transparency codes for a new listing, the brand asked whether codes had to go on its FBM stock, which it ships from the same pool as its own web shop."]
synonyms: []
resolution_status: diagnosis-only
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
observed: 2025-03
review_by: 2027-10
provenance: "ledger:KC-0046"
---

## Question

While getting Brand Registry access to manage Transparency codes for a new listing, the brand asked whether codes had to go on its FBM stock, which it ships from the same pool as its own web shop. The thread concluded that codes were used only for FBA units and that FBM therefore did not matter.

## Answer

Transparency covers every unit of an enrolled product sold on Amazon, whether it ships through FBA or from your own warehouse. Do not assume codes only matter for FBA; FBM units shipped from a shared stock pool need unique codes too. Keep coded Amazon stock separate or code it before it ships to Amazon buyers.

## Cause

Amazon's Transparency page says products enrolled in Transparency cannot be sold in Amazon stores without a valid code, whether they are fulfilled by Amazon or shipped directly by the seller. The thread's conclusion that FBM units need no codes contradicts that page; it was never checked against it.

## Fix

1. Check whether the ASIN is enrolled in Transparency in Brand Registry > Transparency.
2. If it is enrolled, plan codes for every unit sold through Amazon, including FBM orders, not only FBA shipments.
3. Keep Amazon FBM stock separate from shared web-shop stock, or label it with unique codes before it ships to Amazon buyers.
4. For units shipped from your own warehouse (FBM), report the Transparency codes of the shipped units through the code upload in Seller Central, which is how the agency handles FBM orders; the units still carry their code label as Amazon's Transparency page requires.
5. Give the person who requests codes Brand Registry access to Transparency so codes can be ordered for both channels.

## Verify

FBM orders for the enrolled ASIN ship with a valid unique Transparency code on each unit, matching what the Transparency portal expects.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The first-party page already states the rule; the card adds the common misconception that FBM stock from a shared pool is exempt.
- Existing coverage: full (`Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`).
