---
id: KC-0174
title: "Send to Amazon splits a sea shipment across several fulfilment centres and customs is charged per address: compare the single-destination placement fee before asking for one destination"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Step 2: Confirm shipping"
surface_verified: false
symptom_keywords: ["shipment split into multiple fulfillment centers", "ship to one FBA warehouse instead of five", "customs cost per destination address", "inbound placement fee single location", "Amazon-optimized split vs minimal split"]
error_text: []
asked_as: ["For a heavy sea shipment, the client asked whether the inventory had to go to several different Amazon addresses or could go to one, because customs costs were paid per destination and would multiply "]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0174"
---

## Question

For a heavy sea shipment, the client asked whether the inventory had to go to several different Amazon addresses or could go to one, because customs costs were paid per destination and would multiply with each address.

## Answer

Do not ask for a single FBA destination just because customs is charged per address. Choosing fewer destinations adds an inbound placement service fee, which can cost more than the extra customs and delivery runs. Price each placement option in Send to Amazon, add the forwarder's per-destination costs, and pick the lowest total.

## Cause

Send to Amazon offers placement options that range from the minimal number of inbound locations to multiple locations. Shipping to fewer locations carries a higher FBA inbound placement service fee, while multiple locations carry a reduced fee or none; the fee reflects the cost of distributing inventory to fulfilment centres close to customers. The agency stated that a single destination would be far more expensive overall; the thread does not show the figures.

## Fix

1. In Send to Amazon, open the placement options for the shipment and note the inbound placement service fee for the Amazon-optimized split and for fewer destinations.
2. Ask the freight forwarder or customs broker for the per-destination customs and delivery cost.
3. Compare total landed cost per option: placement fee plus forwarder and customs cost for each number of destinations, using the total estimated cost shown in Step 2: Confirm shipping.
4. Choose the cheapest option overall and record the comparison with the shipment.

## Verify

The chosen placement option has the lowest total of placement fee plus per-destination freight and customs cost in the written comparison.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Covering pages explain the placement fee and splits but not weighing it against per-destination customs costs for imported sea freight.
- Existing coverage: partial (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`).
