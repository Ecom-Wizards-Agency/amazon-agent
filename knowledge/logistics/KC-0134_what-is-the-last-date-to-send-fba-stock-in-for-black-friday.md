---
id: KC-0134
title: "What is the last date to send FBA stock in for Black Friday and Q4?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["Q4 inbound cutoff", "last date to send stock for Black Friday", "holiday FBA deadline", "peak season inbound date", "Amazon-optimized shipment split deadline"]
error_text: []
asked_as: ["A brand asked for the latest safe date to send inventory into FBA to stay in stock through Black Friday and the rest of Q4."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md"]
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0134"
---

## Question

A brand asked for the latest safe date to send inventory into FBA to stay in stock through Black Friday and the rest of Q4.

## Answer

Use the arrival dates in the current FBA peak readiness playbook, not a remembered date: each shipment type has its own cutoff, and Amazon-optimized splits have the latest one. Book the delivery appointment at least a week before the cutoff (two weeks for a partnered-carrier pickup) and ship as early as possible, since inbound capacity tightens in October and November. The playbook does not say what happens to stock that arrives after the cutoff, only that it must arrive by then to be ready for the event.

## Cause

Amazon publishes holiday inbound arrival dates in its FBA peak readiness playbook, separate per shipment type: AWD first, then FBA minimal shipment splits, then FBA Amazon-optimized shipment splits. Fulfillment centers shift from receiving to outbound in November and December, so inbound slots and capacity limits tighten after those dates.

## Fix

1. Open the current year's FBA peak readiness playbook in Seller Help and read the arrival dates for the event (Prime Big Deal Days, Black Friday Week and Cyber Monday).
2. Choose the split option for the shipment and use its date: AWD earliest, then minimal shipment splits, then Amazon-optimized shipment splits.
3. Book the delivery appointment at least 7 days before that date, or schedule the Amazon Partnered Carrier pickup 14 days before it, and update the delivery window once dates are final.
4. Ship earlier rather than later; Amazon recommends sending holiday stock in August and September, and inbound slots and capacity limits are lower in October and November.
5. For excess weeks of cover, consider AWD to avoid peak fees, FBA inbound placement fees and capacity limits.

## Verify

The shipment shows as received before the published arrival date for its split type.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Maps the peak playbook's per-split arrival dates to a ship-early decision and flags the thread's inbound-fee claim against the playbook.
- Existing coverage: partial (`Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
