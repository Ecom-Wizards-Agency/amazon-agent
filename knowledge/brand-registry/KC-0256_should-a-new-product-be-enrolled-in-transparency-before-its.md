---
id: KC-0256
title: "Should a new product be enrolled in Transparency before its first shipment, and can non-enrolled units ship with only the FNSKU?"
kind: decision-aid
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US, CA]
marketplace_inferred: false
surface: "Transparency portal; FBA inbound labeling"
surface_verified: false
symptom_keywords: ["do we need Transparency codes", "ship units with FNSKU only no Transparency", "should we deactivate Transparency", "Transparency activation time", "Transparency for new products"]
error_text: []
asked_as: ["The brand owner had units at an overseas supplier labeled only with FNSKU and no Transparency codes, and asked whether they could ship to the US and Canada, whether Transparency codes were needed, who"]
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
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0256"
---

## Question

The brand owner had units at an overseas supplier labeled only with FNSKU and no Transparency codes, and asked whether they could ship to the US and Canada, whether Transparency codes were needed, who would apply them and at what cost. A second participant proposed deactivating Transparency because it added logistics complications.

## Answer

Only ASINs enrolled in Transparency need a Transparency code on every unit; non-enrolled ASINs ship with the FNSKU alone. Keep Transparency on best sellers and products you are scaling, because a single hijacker costs Buy Box time and enforcement effort. New, low-traction products can launch without it, but enroll them when a hijacker appears or before you drive external traffic. Plan for activation lead time, which was about 30 to 40 days in the agency's experience (not an Amazon figure).

## Cause

Transparency codes are required only for ASINs actually enrolled in Transparency; units of non-enrolled ASINs ship with the FNSKU alone. The confusion came from mixing up enrolled best-seller ASINs with new, not-yet-enrolled ASINs.

## Fix

1. Check which ASINs in the shipment are enrolled in Transparency (Transparency portal, product management).
2. For ASINs not enrolled, ship with the FNSKU label only; no Transparency code is needed.
3. For enrolled ASINs, have the supplier or prep partner apply a unique Transparency code to every unit before it ships, since that is usually the cheapest point to label.
4. Decide per product whether to enroll: keep Transparency on best sellers and products being scaled; new products with little traction can start without it.
5. Enroll a new product once a hijacker appears or before pushing external traffic to it, and plan for the activation lead time (about 30 to 40 days in the agency's experience) during which existing hijacker stock can still sell.

## Verify

Inbound units of non-enrolled ASINs are received without Transparency holds; enrolled ASINs show valid codes on every unit.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The sources explain enrollment, but not when to enroll per product stage or that non-enrolled ASINs ship with FNSKU only.
- Existing coverage: full (`Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`).
