---
id: KC-0318
title: "Need to drop a near-expiry SKU from an FBA shipment confirmed more than a day ago: rebuild it, or keep the shipment and labels and leave the item out"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [FR]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon > Shipping queue"
surface_verified: false
symptom_keywords: ["remove a product from a confirmed FBA shipment", "cancel shipment after 24 hours charge", "leave SKU out of Send to Amazon shipment", "short-dated stock exclude from FBA inbound", "new labels needed after dropping an item"]
error_text: []
asked_as: ["After the agency created a Send to Amazon shipment and shared the packing list and labels, the client decided not to send two near-expiry products, to avoid customer returns of short-dated stock, and "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md", "MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0318"
---

## Question

After the agency created a Send to Amazon shipment and shared the packing list and labels, the client decided not to send two near-expiry products, to avoid customer returns of short-dated stock, and asked for a new packing list and shipping labels without them.

## Answer

Before cancelling a Send to Amazon shipment to drop a product, check whether the partnered-carrier void window has passed. Inside it, cancel or rebuild the shipment for a full refund. Outside it, either rebuild and ask Seller Support to refund the unused labels, or keep the existing labels and leave the excluded units out. Record what was left out so the receiving shortage is expected, and plan the item into a later shipment.

## Cause

The agency judged that cancelling and recreating the shipment would still be charged because more than 24 hours had passed since confirmation. The MAG SOP gives the Amazon-partnered carrier void windows as 24 hours for small parcel and one hour for pallets after charges are accepted. It adds that after the window a seller can still cancel and ask Seller Support to refund unused labels. The thread does not establish whether this shipment used a partnered carrier, or whether short-shipping a confirmed shipment brings a fee or defect. The items were held back by choice to avoid returns of short-dated product, not because of an Amazon rule.

## Fix

1. Check how long ago the shipment's partnered-carrier charges were accepted: small parcel can be voided for a full refund within 24 hours, pallets within one hour. 2. Inside the void window, cancel or rebuild the shipment without the excluded SKUs. 3. Outside the window, weigh rebuilding the shipment and asking Seller Support to refund the unused labels (needs operator approval) against keeping the existing shipment and leaving the excluded units out; the thread chose to keep it. 4. If you keep the shipment, check whether the box contents declared in Send to Amazon still include the excluded units. Record the excluded SKUs and quantities so the shortage is expected at receiving, and plan them into a later shipment.

## Verify

The shipment closes with the excluded SKUs short and no unexpected carrier, cancellation or receiving fee for it; the excluded SKUs are planned into a later shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SOPs give the void windows but not the decision to keep an over-window shipment and short-ship the excluded SKUs instead of cancelling.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`).
