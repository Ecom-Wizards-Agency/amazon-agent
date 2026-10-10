---
id: KC-0027
title: "Send to Amazon will not create a large inbound shipment because of the FBA capacity limit: split it, request capacity or wait for removals to clear"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon; Capacity Monitor / Capacity Manager; Removal orders; AWD"
surface_verified: false
symptom_keywords: ["cannot create shipment capacity limit", "FBA storage capacity limit blocks inbound", "maximum units allowed to send", "request more FBA capacity", "split shipment because of capacity"]
error_text: []
asked_as: ["The client asked for shipping labels for a large inbound shipment direct from its supplier; the system would not create the shipment because of the storage capacity limit, which allowed only part of t"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0027"
---

## Question

The client asked for shipping labels for a large inbound shipment direct from its supplier; the system would not create the shipment because of the storage capacity limit, which allowed only part of the units.

## Answer

When Send to Amazon caps a shipment because of the FBA capacity limit, ship the part that fits now and plan the rest as a later shipment. Request more capacity in Capacity Manager early and check the upcoming limits, and use AWD only after checking its product restrictions and cost. Space from removal orders counts only once the units have left the fulfillment centers.

## Cause

The planned shipment exceeded the remaining FBA storage capacity limit, so Send to Amazon capped the units that could be sent.

## Fix

1. Check how many units the current capacity limit still allows.
2. Create the shipment for the part that fits (about half in this case) and send the rest later.
3. Submit a capacity increase request in Capacity Manager for the coming period (operator approval; it can commit a fee). The agency said requests are considered in the last five days of the month and granted for the next month; the help page says they are evaluated several times a week.
4. Consider AWD as an alternative, checking category restrictions and the higher cost of large AWD shipments.
5. If removal orders are pending, expect the freed space only after the units have physically left the fulfillment centers.
6. Monitor capacity and send further batches as space opens.

## Verify

Labels were created for the portion that fitted the limit, following the same destination split as the earlier overseas shipment; the remainder was left for a later shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: KC-0004 and the capacity SOP cover requests and AWD, but not splitting a capped shipment, the removal-order timing or the end-of-month review the agency described.
- Existing coverage: partial (a MAG SOP removed on 10.10.2026, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`).
