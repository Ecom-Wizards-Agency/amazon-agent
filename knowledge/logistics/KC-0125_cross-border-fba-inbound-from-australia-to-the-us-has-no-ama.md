---
id: KC-0125
title: "Cross-border FBA inbound from Australia to the US has no Amazon-partnered carrier: book your own forwarder or ship from a warehouse in the destination country"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US, AU]
marketplace_inferred: false
surface: "Seller Central (US) > Send to Amazon > Ship from address and shipping mode / carrier selection"
surface_verified: false
symptom_keywords: ["Amazon carrier from Australia to US", "cross-border FBA inbound partnered carrier", "international shipment to FBA own forwarder", "partnered carrier not available international", "ship FBA from another country"]
error_text: []
asked_as: ["The agency prepared a US FBA shipment plan with stock shipped by air from the brand's Australian warehouse."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0125"
---

## Question

The agency prepared a US FBA shipment plan with stock shipped by air from the brand's Australian warehouse. The client objected that the plan listed its own freight forwarder and asked for an Amazon carrier to move the goods from Australia to the US, because its Australian logistics partner only delivers to Amazon in Australia.

## Answer

Do not expect a partnered-carrier option for a cross-border FBA inbound. For an origin that Amazon's own cross-border services (Amazon Global Logistics, SEND, currently described for China) do not cover, book your own courier or forwarder for the international leg. If the brand already holds stock in a warehouse in the destination country, ship from there and use the partnered carrier for the domestic leg. Agree on the ship-from address before creating labels, because it is fixed after confirmation.

## Cause

Send to Amazon offered no Amazon-partnered carrier for the international leg from Australia to the US, so that leg had to be booked with an express courier or freight forwarder outside Seller Central. The AU partnered-carrier program covers pickups in eligible AU postcodes to Amazon fulfillment centers. Amazon does run cross-border inbound services, Amazon Global Logistics and SEND, but the captured pages describe them for shipments from China only.

## Fix

1. When the ship-from address is in a different country from the destination marketplace, plan the international leg with your own courier or freight forwarder; do not expect a partnered-carrier option.
2. If the brand already holds stock in a warehouse inside the destination country, create the FBA shipment from that address instead and select the Amazon-partnered carrier there (operator approval before confirming the shipment).
3. Split shipments by the date each batch is ready at the domestic warehouse, and create labels for each batch separately.
4. Recreate or correct labels if the ship-from address changes; it cannot be edited after the shipment is confirmed.

## Verify

The new shipment shows a ship-from address in the destination country with a partnered-carrier option offered, or the international leg is booked with the forwarder and carrier tracking is entered on the shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOP explains partnered versus non-partnered carriers but does not say that partnered carriers cannot move cross-border inbound or that shipping from a destination-country warehouse restores the partnered option.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
