---
id: KC-0139
title: "Which Amazon warehouse address to give the freight forwarder before an FBA inbound: the destination is assigned per shipment and can change every time the plan is re-created"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon (shipment placement, box labels, packing list)"
surface_verified: false
symptom_keywords: ["what warehouse address to send FBA shipment", "FBA destination changed after recreating shipment", "forwarder needs Amazon warehouse address", "new shipment different fulfillment center", "first FBA shipment from China address"]
error_text: []
asked_as: ["A brand preparing its first air and sea FBA shipments from overseas asked for the Amazon warehouse address so its forwarder could quote, then asked why the address changed each time the shipment docum"]
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
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0139"
---

## Question

A brand preparing its first air and sea FBA shipments from overseas asked for the Amazon warehouse address so its forwarder could quote, then asked why the address changed each time the shipment documents were regenerated after carton counts were corrected.

## Answer

Do not promise a forwarder a fixed Amazon warehouse address before the shipment exists: Amazon assigns the fulfillment center per shipment, and re-creating the plan can move it. Lock carton counts and dimensions first, build the plan, and only then send the forwarder the shipment ID, destination, box labels and packing list. If the plan must be rebuilt, resend all of them and discard the old labels.

## Cause

Amazon assigns the destination fulfillment center per shipment when the Send to Amazon plan is built. Re-creating a plan (for new carton counts, units per carton or a different mode) triggers a new placement, which may return the same or a different fulfillment center. The agency operator could not get a specific earlier destination back on request after several tries. A past destination is therefore only a guide.

## Fix

1. Collect final carton count, units per carton, carton dimensions and weight, and the transport mode before building the plan, to avoid re-creating it.
2. Build the Send to Amazon plan; give the forwarder a past destination only as a quote estimate.
3. Once placement is confirmed, send the forwarder the shipment ID, Amazon reference ID, ship-to fulfillment center and address, box labels and packing list.
4. If counts change, cancel the old plan and create a new one (operator approval), and tell the forwarder the destination may change; send the new labels and address.
5. Print the box-label PDF and attach one label to the outside of each carton; units still need their own product barcode.

## Verify

The forwarder's booking and the carton labels show the same shipment ID and fulfillment center as the active shipment in Send to Amazon; the cancelled plan's labels are discarded.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/061-ship-products-to-amazon-G200141420.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The local sources describe building and cancelling Send to Amazon shipments but not that each re-creation can change the assigned fulfillment center, so the forwarder must get the address only after the final plan.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-fba-shipment-reconciliation.md`).
