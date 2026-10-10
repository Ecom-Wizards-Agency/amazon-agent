---
id: KC-0114
title: "Inventory received in AWD: does it still need a manual shipment to FBA?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["AWD to FBA how long", "AWD replenishment", "does AWD send to FBA automatically", "inventory received in AWD", "AWD distribution time"]
error_text: []
asked_as: ["A client whose stock had just been received in Amazon Warehousing and Distribution asked whether it takes long for Amazon to move it on to fulfillment centers."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md", "MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0114"
---

## Question

A client whose stock had just been received in Amazon Warehousing and Distribution asked whether it takes long for Amazon to move it on to fulfillment centers.

## Answer

Once inventory is received in AWD and automatic replenishment is in use, Amazon moves it on to FBA fulfillment centers itself, so the seller does not send a separate FBA shipment. Confirm replenishment is on for the SKU and watch FBA inbound for the transfers; no Amazon timing for the transfer is established.

## Cause

AWD offers automatic replenishment from AWD into Prime-ready fulfillment centers, so when it is in use the seller does not create a separate FBA shipment for stock received in AWD. Neither the thread nor the local captures state how long the replenishment takes.

## Fix

1. Confirm the AWD shipment shows as received.
2. Confirm automatic replenishment to FBA is in use for the SKU (the AWD SOP describes it as an option; the exact settings location is not captured locally).
3. Monitor FBA Inbound and Available for the SKU over the following days instead of creating a new FBA shipment.

## Verify

Replenishment transfers from AWD appear as inbound to FBA for the SKU and Available rises.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Also in: `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Little is new: the AWD help page already states automatic replenishment; the card adds the seller-facing answer that no separate FBA shipment is needed.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`, `MAG SOPs/catalog/supplemental-article-maximizing-efficiency-with-amazon-warehousing-and-distribution-awd.md`, `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
