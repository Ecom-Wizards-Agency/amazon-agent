---
id: KC-0316
title: "Can Amazon store and ship inventory for a brand that does not sell on Amazon (off-Amazon store orders)?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Multi-Channel Fulfillment (supplychain.amazon.com/mcf); Seller Central inventory; Amazon Warehousing and Distribution"
surface_verified: false
symptom_keywords: ["use FBA for web store orders", "Amazon fulfillment without selling on Amazon", "Multi-Channel Fulfillment non Amazon brand", "store inventory at Amazon without listing", "MCF inactive listing"]
error_text: []
asked_as: ["A contact asked whether Amazon can hold inventory for a brand that does not sell on Amazon, and ship its web-store orders."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0316"
---

## Question

A contact asked whether Amazon can hold inventory for a brand that does not sell on Amazon, and ship its web-store orders.

## Answer

Amazon can fulfill orders for a brand that does not sell on Amazon through Multi-Channel Fulfillment, but you still need a listing so the SKU exists; Amazon lets you list inventory for MCF without making it available for sale. Use AWD for cheaper bulk storage that replenishes FBA. Before you commit stock, confirm the category can go into FBA (not discussed in the thread) and price MCF against a third-party warehouse.

## Cause

Amazon fulfillment works on Seller Central offers, so the product needs a listing (SKU) before inventory can be sent in. The listing does not have to be sold on Amazon: it can stay inactive while Multi-Channel Fulfillment ships orders from other sales channels. Cheaper bulk storage is available through Amazon Warehousing and Distribution, which replenishes the fulfillment network.

## Fix

1. Create the product listing in Seller Central so a SKU exists for FBA inventory.
2. Keep the offer inactive (deactivated) if the brand does not want to sell on Amazon.
3. Send inventory in, using AWD for lower-cost bulk storage if volume is large, and replenish FBA from it.
4. Connect the off-Amazon store to Multi-Channel Fulfillment so its orders are fulfilled from that inventory.
5. Compare MCF fees against a third-party warehouse quote before committing, using the carton and unit sizes.

## Verify

The SKU shows FBA inventory with the offer inactive on Amazon, and a test off-Amazon order is created and shipped through Multi-Channel Fulfillment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit explains that a brand not selling on Amazon can still use MCF by creating a listing, keeping the offer inactive and storing bulk stock in AWD.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md`, `Amazon Seller Help/articles/189-amazon-north-american-and-brazil-stores-G201394090.md`, `MAG SOPs/catalog/merchandising-sop-amazon-listing-creation.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
