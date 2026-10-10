---
id: KC-0147
title: "Inbound shipment will arrive outside its delivery window and the window cannot be changed: what happens?"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Send to Amazon > shipment tracking details > estimated delivery window"
surface_verified: false
symptom_keywords: ["change inbound delivery window", "shipment arriving early outside window", "cannot edit delivery date Send to Amazon", "what happens if FBA shipment arrives early", "delivery window wrong date"]
error_text: []
asked_as: ["A seller asked to move an air inbound shipment's delivery window to an earlier week; the account manager said the window could not be changed, and the seller asked what happens if the shipment arrives"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0147"
---

## Question

A seller asked to move an air inbound shipment's delivery window to an earlier week; the account manager said the window could not be changed, and the seller asked what happens if the shipment arrives outside the scheduled window.

## Answer

Set an inbound delivery window from the carrier's real transit estimate, not from the order or production date. A shipment that arrives outside its window is still received, but it is flagged as early or late and may face receive delays, so update the window before it starts whenever you expect a change. When arrival is uncertain, pick the later window: you can still move it earlier until it begins, but an earlier window cannot be changed once it has started.

## Cause

The delivery window was set from the order date plus production time, so it landed weeks after the real arrival. A window can be modified only until it begins. According to the operator, Amazon still receives a shipment that arrives outside its window but flags it as early or late, which can affect seller metrics. The first-party page adds that such shipments may face appointment and receive delays. The thread did not establish why the window could not be edited when first asked.

## Fix

1. Check the carrier tracking to estimate the real arrival week before touching the window.
2. In Send to Amazon, open the shipment and review the estimated delivery window in the tracking details.
3. If the real arrival is uncertain, choose the later window: it can still be moved earlier until it begins, but once an earlier window has started it can no longer be changed.
4. If you expect a change, update the delivery window before the window starts.
5. If the window cannot be edited, let the shipment arrive; it is still received but flagged as early or late and may be received more slowly.

## Verify

After arrival, confirm the shipment shows as received in the shipment's events and check whether it was flagged as arriving outside the window.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the operator observation that an out-of-window arrival is still received but flagged, and that moving a window earlier is easier than later, so pick the later window when unsure.
- Existing coverage: partial (`Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
