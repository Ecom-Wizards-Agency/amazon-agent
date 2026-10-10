---
id: KC-0117
title: "Cannot change box count or ship-from on a confirmed AWD or Send to Amazon shipment: cancel and recreate it"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > shipment (AWD STAR-... and FBA)"
surface_verified: false
symptom_keywords: ["adjust AWD shipment box count", "change number of boxes after labels", "edit ship from address shipment", "cancel and recreate shipment"]
error_text: []
asked_as: ["After receiving labels, the supplier changed the ship-from address and later the number of cartons on a sea shipment to AWD, and could not find a button to adjust the shipment."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md", "MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0117"
---

## Question

After receiving labels, the supplier changed the ship-from address and later the number of cartons on a sea shipment to AWD, and could not find a button to adjust the shipment.

## Answer

You cannot change the carton count or ship-from address of a confirmed shipment. Cancel it, recreate it with the final numbers, and make sure the supplier destroys the old labels so no carton arrives under the cancelled shipment.

## Cause

Once the packing details and the shipment are confirmed, Send to Amazon does not allow edits to the carton count or the ship-from address; the MAG SOP states both, and the agency confirmed it for an AWD shipment. The only path is to cancel the shipment and create a new one.

## Fix

1. ["1. Cancel the existing shipment so it is not charged or received against.", "2. Recreate it with the corrected ship-from address and carton count, matching the final packing list.", "3. Send the new labels and packing list and tell the supplier to discard the previous labels.", "4. Give the carrier the new shipment ID and its Amazon Reference ID."]

## Verify

Only the recreated shipment is active and its carton count matches the final packing list.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that AWD and Send to Amazon shipments cannot be edited for carton count or ship-from after labels exist, so cancel-and-recreate with label discard is the path.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`).
