---
id: KC-0131
title: "Cannot change the delivery window on an FBA shipment: edit it at the final tracking-details step instead of recreating the shipment"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Send to Amazon > shipment > tracking details step (estimated delivery window)"
surface_verified: false
symptom_keywords: ["cannot change delivery window", "delivery window error FBA shipment", "update estimated delivery window", "shipment delayed past delivery window", "support says recreate shipment"]
error_text: []
asked_as: ["A supplier's FBA shipment from overseas was delayed by several weeks after labels had already been printed and applied."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md", "Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", "MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0131"
---

## Question

A supplier's FBA shipment from overseas was delayed by several weeks after labels had already been printed and applied. The agency could not change the shipment's delivery window, an error showed for a week, and Seller Support recommended cancelling and recreating the shipment, which would have meant relabelling every carton.

## Answer

When a shipment's delivery window will not change, open the tracking-details step at the end of the shipment workflow and edit the window there before accepting advice to cancel and recreate. Recreating a shipment invalidates labels already on the cartons. Amazon asks for an accurate delivery window and lets you update it before it starts, because shipments arriving outside the window may face receiving delays.

## Cause

Not fully established in the thread. The delivery window could not be edited on the shipment screen where the agency tried, but the client's operations contact changed it at the last step of the workflow, where tracking details are entered, without entering tracking yet.

## Fix

1. ["1. Open the shipment in Send to Amazon and go to the final step where tracking details are entered.", "2. Change the estimated delivery window there; in this case tracking IDs were not needed to save the new window.", "3. If the field still errors, retry later before cancelling, since recreating the shipment forces new box labels.", "4. Only if the window cannot be updated and the delay is long, weigh cancelling and recreating the shipment against relabelling cost and the appointment and receiving delays Amazon says shipments outside their window may face (operator approval before cancelling)."]

## Verify

The shipment shows the new estimated delivery window after saving.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party playbooks say to update the delivery window in the tracking details step, but nothing covers the case where the summary screen errors and support advises recreating the shipment.
- Existing coverage: full (`Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
