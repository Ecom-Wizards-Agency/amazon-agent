---
id: KC-0185
title: "Is there a limit on units per carton for an FBA shipment, or only weight and size limits?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Send to Amazon > box packing information"
surface_verified: false
symptom_keywords: ["max units per carton fba", "carton weight limit amazon", "case pack unit limit", "how many units per box fba", "box dimensions within amazon limits"]
error_text: []
asked_as: ["A client's logistics contact asked whether a carton's weight and dimensions were within Amazon's standard limits and whether Amazon would accept a very large number of units in one carton, or whether "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", "Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0185"
---

## Question

A client's logistics contact asked whether a carton's weight and dimensions were within Amazon's standard limits and whether Amazon would accept a very large number of units in one carton, or whether there is a cap on units per case pack.

## Answer

Check FBA cartons against weight and size first. A carton must stay at or under 50 lb unless it holds one single oversize unit, and a box of several standard-size units must not exceed 25 inches on any side. No hard unit-count cap was found locally, but Amazon recommends at most 25 units per single-SKU box when you use optimised shipment splits, so a very high count per carton can slow distribution even when it is allowed.

## Cause

The agency answered that the binding limit is carton weight, 50 lb at most. The MAG SOP adds a 25-inch maximum per side for boxes with several standard-size units. No local first-party source states a hard cap on units per carton, but Amazon's delivery-speed guidance recommends no more than 25 units per single-SKU box when you use optimised shipment splits.

## Fix

1. Weigh the packed carton: it must not exceed 50 lb unless it holds one single oversize unit.
2. Measure the carton: a box with several standard-size units must not exceed 25 inches on any side.
3. No hard units-per-carton cap was found, but if you send through optimised shipment splits, Amazon recommends no more than 25 units per single-SKU box for faster distribution.
4. Enter the box weight and dimensions accurately in Send to Amazon, especially with a partnered carrier.

## Verify

Send to Amazon accepts the box packing information without a weight or dimension warning.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP lists weight and size limits but does not answer whether a units-per-carton cap exists, which is how teams ask the question.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`).
