---
id: KC-0028
title: "Stranded inventory still showing after a removal order: Amazon cancelled part of the removal"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["stranded inventory after removal order", "removal order units cancelled", "units not included in removal", "stranded units still showing", "removal order partially cancelled"]
error_text: []
asked_as: ["Seller Central still showed a large quantity of stranded inventory after a removal back to the 3PL; the client asked whether units were left out or Amazon was delayed."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md", "MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0028"
---

## Question

Seller Central still showed a large quantity of stranded inventory after a removal back to the 3PL; the client asked whether units were left out or Amazon was delayed.

## Answer

When stranded inventory remains after a removal order, compare it with the units Amazon cancelled from that order before suspecting a glitch. Create a new removal order for the cancelled units, and leave the rest alone while it is within the normal processing window. Check the removable quantity first, because some units can be temporarily unavailable.

## Cause

The stranded quantity almost exactly matched the units Amazon had cancelled from the removal order. The rest of the removal was still within the normal processing window.

## Fix

1. About a week after creating the removal order, compare the stranded inventory report with the removal order detail.
2. If the stranded units match units cancelled from the removal order, create a new removal order for them.
3. Check how many units Amazon currently allows to be removed; some may be temporarily unavailable and need a later removal.
4. Leave the uncancelled part alone while it is still within the normal removal window.

## Verify

The new removal order shows the units as pending or in progress, and the stranded quantity falls as removals complete.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Stranded units left after a removal can match units Amazon cancelled from the removal order, fixed by a new removal order.
- Existing coverage: partial (`knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`).
