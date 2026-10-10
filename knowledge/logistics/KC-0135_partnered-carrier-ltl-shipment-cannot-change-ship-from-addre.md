---
id: KC-0135
title: "Partnered-carrier LTL shipment: cannot change ship-from address, cancel half, or recover a missed pickup without a case"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["LTL pickup refused", "reschedule partnered carrier pickup", "change ship from address shipment", "refund unused shipping labels", "edit BOL SCAC"]
error_text: []
asked_as: ["A seller's warehouse shipped only part of a partnered-carrier LTL shipment set, wanted the rest shipped from a different warehouse on the already-paid labels, wanted unused labels refunded, and later "]
synonyms: []
resolution_status: resolved
fix_source: amazon-support
evidence_location: case
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-05
review_by: 2027-10
provenance: "ledger:KC-0135"
---

## Question

A seller's warehouse shipped only part of a partnered-carrier LTL shipment set, wanted the rest shipped from a different warehouse on the already-paid labels, wanted unused labels refunded, and later had a carrier refuse to collect two shipments at pickup.

## Answer

Partnered-carrier LTL labels belong to the ship-from address confirmed in Send to Amazon, so stock leaving from another warehouse needs a new shipment and a new charge. Void unwanted charges within the void window (one hour for pallets). Once any boxes of a shipment have shipped or are receiving, you cannot cancel the rest or recover the label cost. If the carrier misses or refuses a pickup, have Seller Support reschedule it. If the case says to, hand-edit the BOL date and SCAC code to match the newly assigned carrier.

## Cause

Partnered-carrier charges and the bill of lading are tied to the ship-from address confirmed in Send to Amazon, and that address cannot be changed after confirmation. Pallet charges can be voided for a full refund only within one hour of accepting them (24 hours for small parcel). Once any boxes of a shipment have shipped or are receiving, the shipment cannot be cancelled, so its unused labels are not refunded. The thread never establishes why the carrier refused the pickup. Seller Support rescheduled it and assigned a different carrier, so the printed BOL no longer matched.

## Fix

1. ["1. Do not reuse partnered-carrier labels from a different ship-from address; create a new shipment from the new warehouse and accept that it is charged separately.", "2. Void unwanted partnered-carrier charges inside the void window (one hour after accepting pallet charges, 24 hours for small parcel). After that, a shipment with any boxes shipped or receiving cannot be cancelled and its unused labels are not refunded.", "3. If the carrier refuses or misses a pickup, open a Seller Support case asking to reschedule the pickup for the named shipment IDs (operator approval before submitting).", "4. When Seller Support confirms the new pickup, hand-edit the BOL only as the case instructs: the pickup date at the top and the SCAC code of the newly assigned carrier.", "5. Treat the rescheduled date as an estimate; wait for the confirmation email."]

## Verify

The pickup confirmation email arrives and the shipment moves to in transit with the new carrier.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Partnered LTL labels cannot move to a new ship-from address or be partly refunded, and a missed pickup needs a case plus a hand-edited BOL date and SCAC.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
