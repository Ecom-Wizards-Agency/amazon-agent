---
id: KC-0217
title: "Vine enrollment on a variation family counts against the parent: 30 units maximum across all children"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Advertising > Vine > enroll"
surface_verified: false
symptom_keywords: ["vine parent detected", "vine 30 units max variation", "split vine enrollment children", "vine enrollment per parent asin", "vine units across variations"]
error_text: []
asked_as: ["A specialist enrolling a variation family in Vine found that Amazon detects the parent and allows only 30 units in total, and asked whether to split the enrollment."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-vine-setup.md", "MAG SOPs/catalog/catalog-sop-how-to-fix-errors-in-the-vine-program-on-seller-central.md"]
supersedes: []
contradicts: []
observed: 2024-09
review_by: 2027-10
provenance: "ledger:KC-0217"
---

## Question

A specialist enrolling a variation family in Vine found that Amazon detects the parent and allows only 30 units in total, and asked whether to split the enrollment.

## Answer

Vine treats a variation family as one parent: the fee is charged once per parent ASIN and the family shares one enrollment of at most 30 units, with Vine Voices choosing which child to order. Do not split or delete the parent to get more units.

## Cause

Vine charges its enrollment fee once per parent ASIN (first-party), and the MAG Vine SOP states 1 to 30 units per parent ASIN, so the children of one variation family share one enrollment and one unit cap. Vine Voices choose which child to order.

## Fix

1. Before enrolling, check whether the ASIN sits in a variation family.
2. Expect the enrollment at parent level: at most 30 units for the whole family, with Vine Voices choosing which child to order.
3. Do not delete or break the parent to get a second cap; a child that leaves the family causes a 'Not associated with the enrolled parent' error.
4. Choose the tier and submit the enrollment (operator approval; the fee is charged once per parent after the first Vine review).

## Verify

The enrollment shows the family under one parent with the planned units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md`
- Also in: `MAG SOPs/catalog/catalog-sop-vine-setup.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-errors-in-the-vine-program-on-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains that a variation family enrolls in Vine as one parent, so all children share the 30-unit top tier.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-vine-setup.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-errors-in-the-vine-program-on-seller-central.md`, `Amazon Seller Help/articles/077-amazon-vine-G92T8UV339NZ98TN.md`, `MAG SOPs/README.md`, `Amazon Seller Help/articles/084-new-seller-incentives-GXMJ38VA95GUN5XU.md`).
