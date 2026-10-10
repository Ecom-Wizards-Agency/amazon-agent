---
id: KC-0167
title: "AWD inbound pallet shipment shows no tracking progress when a freight forwarder moves it"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > AWD > Inbound shipment > Tracking"
surface_verified: false
symptom_keywords: ["AWD shipment tracking not updating", "track palletized AWD inbound", "AWD inbound BOL number", "where is my AWD shipment", "forwarder pallet shipment to AWD no tracking"]
error_text: []
asked_as: ["The account manager asked whether anyone tracks a palletized inbound shipment to Amazon Warehousing and Distribution, since the tracking page showed no progress."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md", "MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0167"
---

## Question

The account manager asked whether anyone tracks a palletized inbound shipment to Amazon Warehousing and Distribution, since the tracking page showed no progress.

## Answer

When a freight forwarder delivers palletized inventory to AWD, Seller Central shows no transit tracking; it only stores the BOL number you enter. Get the BOL from the forwarder, add it to the AWD shipment, and follow transit with the forwarder. The next Amazon-side update is the pallet check-in at the distribution center.

## Cause

Per the agency logistics operator, when the seller's own freight forwarder moves a palletized AWD inbound (not an Amazon partnered carrier), Seller Central only lets the seller enter the bill of lading (BOL) number. Transit milestones come from the forwarder, and the next status Amazon itself posts is the pallet check-in at the distribution center.

## Fix

1. Get the BOL number from whoever booked the freight (the forwarder or the client).
2. Open the AWD inbound shipment in Seller Central and add the BOL number on its tracking page.
3. Track transit progress with the forwarder directly; do not expect carrier events in Seller Central.
4. Watch the AWD shipment for the check-in status, which is the next update Amazon posts.

## Verify

The AWD shipment shows the BOL number saved, and its status changes to checked in once the pallets arrive at the distribution center.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Also in: `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The AWD SOP covers creating and tracking partnered-carrier shipments but not that forwarder-moved pallets show no transit in Seller Central beyond the BOL and the check-in status.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`, `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
