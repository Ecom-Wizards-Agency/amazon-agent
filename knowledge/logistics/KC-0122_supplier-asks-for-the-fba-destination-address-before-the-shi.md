---
id: KC-0122
title: "Supplier asks for the FBA destination address before the shipment exists: units per carton come first, the destination is known only after the shipment is created"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon (packing information, placement)"
surface_verified: false
symptom_keywords: ["supplier needs FBA address", "which fulfillment center address", "when do we get the FBA address", "units per box before shipping labels", "first FBA shipment new listing"]
error_text: []
asked_as: ["After new listings went live, the client asked its supplier to ship the first FBA stock."]
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
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0122"
---

## Question

After new listings went live, the client asked its supplier to ship the first FBA stock. The supplier proposed a fulfillment-center address it had found itself, and the client asked when the real address and labels would be available.

## Answer

Do not let a supplier pick a fulfillment-center address. Collect units per carton, carton dimensions and weight first, create the shipment in Send to Amazon, and send the supplier only the labels and destination that come from it. After delivery, collect every carton's tracking number and watch for the units to show as received in FBA.

## Cause

Amazon assigns the destination when the shipment is created from the packing information, so there is no address before the units per carton are known. A supplier-sourced address is a guess.

## Fix

1. ["1. Confirm the UPC each pack size must carry and the quantity per SKU.", "2. Get units per carton, carton dimensions and weight from the supplier.", "3. Create the shipment in Send to Amazon; placement assigns the destination, and the box labels come from the shipment.", "4. Send the labels and destination to the supplier and tell them not to use any other address.", "5. After delivery, collect every carton's tracking number and check Seller Central until the units show as received. The thread does not establish when to switch the offer to FBA or raise ad spend."]

## Verify

The shipment was created from the packing data and delivered. The agency switched the offer to FBA on delivery, but the units had not yet shown as received in FBA when the thread ends.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The shipment SOP does not warn against supplier-sourced FC addresses or say to wait for received units before switching the offer to FBA.
- Existing coverage: partial (`sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
