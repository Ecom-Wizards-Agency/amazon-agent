---
id: KC-0140
title: "When to send inventory to AWD instead of FBA, and does AWD need an onboarding call?"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon (upstream storage option) > Shipments"
surface_verified: false
symptom_keywords: ["AWD or FBA", "do I need a call to use AWD", "how to send to AWD", "FBA capacity full backup stock", "check past AWD shipments"]
error_text: []
asked_as: ["A client founder asked whether the account had ever used AWD, when it should be used, and why Amazon was asking them to book a call before setting it up."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md", knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0140"
---

## Question

A client founder asked whether the account had ever used AWD, when it should be used, and why Amazon was asking them to book a call before setting it up.

## Answer

AWD needs no onboarding call. A primary user is enrolled by opening the AWD program page, and other users need the AWD permission. Create the shipment from Send inventory to AWD or with the upstream storage option in Send to Amazon. As a rule of thumb (agency practice, not an Amazon rule), send quantities that fit FBA capacity straight to FBA, and use AWD as backup storage when FBA capacity keeps running out and stockouts are a risk.

## Cause

Not a fault. AWD is self-serve: per the AWD help page, users with primary access are enrolled automatically when they visit the AWD program page, and other users need the AWD permission granted under User permissions. In the thread, the shipment was created in Send to Amazon with the upstream storage (AWD) option and needed no call. Why Amazon offered the client a call was not established.

## Fix

1. Decide the destination. As agency practice, send to FBA when the quantity fits current FBA capacity, and send overflow or backup stock to AWD when capacity is regularly maxed out.
2. Open the AWD program page (a primary user is enrolled on the first visit), or have the primary user grant AWD permission under User permissions.
3. Create the shipment from Send inventory to AWD, or pick the upstream storage option in Send to Amazon.
4. Complete packing, box labels and carrier as usual. No onboarding call is needed.
5. To see whether AWD was used before, filter Shipments for AWD shipments.

## Verify

The AWD shipment appears under Shipments with an AWD destination, and the AWD inventory page shows the stock after receipt.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Also in: `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that AWD needs no onboarding call and gives a simple rule: small quantities to FBA, capacity-overflow backup to AWD.
- Existing coverage: full (`knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
