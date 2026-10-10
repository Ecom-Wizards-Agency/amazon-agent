---
id: KC-0113
title: "Inbound shipment delivery window is out of date: update it before the window starts"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Tracking details > Delivery window"
surface_verified: false
symptom_keywords: ["update delivery window FBA shipment", "shipment arriving outside delivery window", "inbound appointment delays", "change estimated delivery window"]
error_text: ["Delivery Window is a calendar week when you expect your shipments to arrive at Amazon. Shipments arriving within their scheduled windows will receive priority processing, while shipments arriving outside of their scheduled delivery windows may face appointment and receive delays."]
asked_as: ["A brand was told accurate delivery dates matter and asked the agency to update the delivery window on its inbound shipment."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0113"
---

## Question

A brand was told accurate delivery dates matter and asked the agency to update the delivery window on its inbound shipment.

## Answer

Keep the estimated delivery window on a non-partnered inbound shipment accurate, and update it when you expect the arrival date to move. Shipments that arrive inside their window get priority processing; those outside it may face appointment and receiving delays. Amazon lets you update the window before it starts.

## Cause

The thread does not say why the window was out of date: the client asked for it to be updated, and the agency changed it. The rule behind it is first-party: on a shipment with a non-partnered carrier, the estimated delivery window in the tracking details step should be accurate. Shipments that arrive inside their window get priority processing; those outside it may face appointment and receiving delays.

## Fix

1. Open the shipment in Send to Amazon and go to the tracking details.
2. Change the delivery window to the calendar week the shipment is now expected to arrive, before the current window starts.

## Verify

The shipment shows the new delivery window.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Pulls the delivery-window rule out of the seasonal readiness playbooks into a standalone answer for updating an inbound shipment whose arrival date moved.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
