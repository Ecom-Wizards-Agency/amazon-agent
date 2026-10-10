---
id: KC-0032
title: "Send to Amazon blocks a new-SKU shipment with 'Please review SKUs with errors or unconfirmed SKUs' because FBA capacity is used up"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["cannot send shipment SKUs with errors", "unconfirmed SKUs Send to Amazon", "FBA capacity full new shipment", "shipment blocked capacity limit"]
error_text: ["Please review SKUs with errors or unconfirmed SKUs"]
asked_as: ["A team member creating a shipment of new SKUs could not continue; Send to Amazon showed 'Please review SKUs with errors or unconfirmed SKUs'."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md"]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0032"
---

## Question

A team member creating a shipment of new SKUs could not continue; Send to Amazon showed 'Please review SKUs with errors or unconfirmed SKUs'.

## Answer

If Send to Amazon says to review SKUs with errors or unconfirmed SKUs and nothing looks wrong with the SKUs, check the capacity monitor before editing listings. When capacity is exhausted, request extra capacity through Capacity Manager, which costs a fee, or ship less.

## Cause

The account had no remaining FBA capacity for the period, so the SKUs could not be confirmed into the shipment. The generic SKU error hid the capacity limit.

## Fix

1. Open the capacity monitor and check remaining capacity for the storage type.
2. Agree how much extra capacity is needed.
3. Request extra capacity through Capacity Manager, which carries a reservation fee (operator approval required), or reduce the shipment.
4. Retry the SKU confirmation in Send to Amazon.

## Verify

After capacity is granted or the quantity reduced, the SKUs confirm and the workflow moves to packing.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Maps the generic 'Please review SKUs with errors or unconfirmed SKUs' message to an exhausted FBA capacity limit.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-fba-storage-capacity-limits.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
