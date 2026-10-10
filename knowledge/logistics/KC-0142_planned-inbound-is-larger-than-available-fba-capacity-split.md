---
id: KC-0142
title: "Planned inbound is larger than available FBA capacity: split by destination or delay label generation"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon; Capacity Monitor; AWD"
surface_verified: false
symptom_keywords: ["shipment bigger than FBA capacity", "not enough FBA space for production run", "split shipment FBA and AWD", "when to create box labels", "capacity frees up as we sell"]
error_text: []
asked_as: ["A production run larger than the remaining FBA capacity was about to ship from the factory before a holiday closure, and the client asked how to send it without paying for two separate freight batches"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md"]
related_sops: [knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0142"
---

## Question

A production run larger than the remaining FBA capacity was about to ship from the factory before a holiday closure, and the client asked how to send it without paying for two separate freight batches.

## Answer

When a production run exceeds FBA capacity, send what fits to FBA and plan the rest for AWD, which can replenish FBA automatically, or request more space through Capacity Manager. If neither is available, generate FBA labels as late as the supplier deadline allows, because sales free capacity over time. Size production orders to what Amazon can absorb rather than ordering ahead of capacity.

## Cause

FBA capacity limits how many units Send to Amazon accepts at once. Capacity frees up daily as units sell, so the room available when labels are generated sets the FBA portion.

## Fix

1. Check remaining capacity in Capacity Monitor and compare it with the production quantity.
2. Plan one freight booking with split destinations: the FBA portion that fits now, and the remainder to AWD, which can replenish FBA automatically. In the thread this split was planned but not executed, because AWD was blocked.
3. If AWD is unavailable, generate FBA box labels as late as the supplier deadline allows, because sold units free more capacity over time. Capacity Manager is another option for extra FBA space.
4. Consider sea freight for the portion that has to wait for capacity anyway.
5. Confirm any extra cost with the client before labels are issued. That the split has no extra cost was not verified against a fee page.

## Verify

The created shipments together cover the full production quantity, and the FBA part is accepted by Send to Amazon without exceeding the limit.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`
- Also in: `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Keep one freight booking with split FBA and AWD destinations, or delay FBA label generation because daily sales free capacity.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
