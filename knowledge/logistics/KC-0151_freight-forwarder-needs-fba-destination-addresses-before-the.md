---
id: KC-0151
title: "Freight forwarder needs FBA destination addresses before the shipment exists in Send to Amazon"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon (placement step)"
surface_verified: false
symptom_keywords: ["which fulfillment centers will we ship to", "forwarder needs FBA address for quote", "destination FC before shipment creation", "partnered carrier rates before creating shipment", "sea freight FBA destination unknown"]
error_text: []
asked_as: ["Before a sea shipment from China to US FBA, the client asked which fulfillment centers it would go to, because the courier needed destination addresses to quote, and asked for partnered carrier rates."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0151"
---

## Question

Before a sea shipment from China to US FBA, the client asked which fulfillment centers it would go to, because the courier needed destination addresses to quote, and asked for partnered carrier rates.

## Answer

You cannot know the FBA destination warehouses until you create the shipment in Send to Amazon, so a forwarder quote needs a draft shipment first. Build the draft with real case packs, read the destinations for the chosen placement option and the estimated cost, then get the forwarder quote before confirming.

## Cause

Amazon assigns destination fulfillment centers when the shipment is created in Send to Amazon and a placement option is chosen, so the addresses are not known beforehand. Estimated shipping costs, including partnered-carrier estimates where offered, are shown in the same workflow at Step 2 Confirm shipping. The thread did not establish whether partnered-carrier rates were available for this sea route.

## Fix

1. Agree on the SKU and pack mix first, based on current sales data.
2. Create the shipment in Send to Amazon with real case-pack data to the placement step.
3. Read the destinations and the estimated partnered carrier cost from the placement and confirm-shipping steps.
4. Send the destination addresses to the forwarder for a quote, then choose the carrier.
5. Confirm the shipment only after operator approval.

## Verify

The forwarder quote names the same fulfillment centers shown in the created shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The Send to Amazon SOP shows the placement step but does not say forwarder quotes must wait for a draft shipment because destinations are unknown before it.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`).
