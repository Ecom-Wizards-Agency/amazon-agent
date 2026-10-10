---
id: KC-0088
title: "Listing copy needs a disease word for ranking but the product cannot substantiate the claim"
kind: rule
topic: compliance
status: reviewed
skills: [amazon-seo, amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: true
surface: "Listing copy (title, bullets, description)"
surface_verified: false
symptom_keywords: ["antifungal claim in listing", "can we use fungus in bullet", "disease claim keyword ranking", "remove disease claim from copy", "condition word in listing copy"]
error_text: []
asked_as: ["An SEO rewrite for a topical care product kept one condition-related root word in one bullet, because the current listing ranked poorly without it."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md"]
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0088"
---

## Question

An SEO rewrite for a topical care product kept one condition-related root word in one bullet, because the current listing ranked poorly without it. The brand side asked whether the word could stay, given that the product works against the condition.

## Answer

Do not keep a disease or condition word in listing copy for ranking value when the product cannot substantiate that claim. One mention in one bullet is enough to get the listing flagged, so remove the word and its stems entirely and describe the benefit without naming the condition. Ask the brand whether accepted documentation exists before writing any treatment claim.

## Cause

Naming a disease or condition the product treats is a disease claim. The brand confirmed the formulation could not be substantiated for that claim under Amazon policy, and stated that any instance of the word would get the listing flagged.

## Fix

1. Search the draft title, bullets, description and backend terms for the condition word and all its stems and adjective or 'anti-' forms.
2. Confirm with the brand whether the product has documentation or testing that Amazon accepts for that claim; without it, treat the claim as unusable.
3. Remove every instance from customer-facing copy and backend terms, and describe the benefit without naming the condition.
4. Have the brand's compliance reviewer approve the revised copy before upload (approval gate).

## Verify

The uploaded listing contains no instance of the condition word or its stems, and no listing policy warning appears for the ASIN after the change.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that a single condition word kept for ranking must go entirely when the brand cannot substantiate the claim, a case the SOPs list but do not frame as a ranking trade-off.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`).
