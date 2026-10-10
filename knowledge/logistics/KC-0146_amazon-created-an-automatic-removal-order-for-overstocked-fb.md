---
id: KC-0146
title: "Amazon created an automatic removal order for overstocked FBA inventory: stop it or let it run?"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Removal order detail"
surface_verified: false
symptom_keywords: ["automatic removal order overstock", "Amazon removing excess inventory", "cancel pending removal order", "sell overstock or return it", "removal order not created by me"]
error_text: []
asked_as: ["The account manager found a removal order that Amazon had created automatically because too much stock was in the warehouse, and had to decide whether to stop it or let the units come back."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md", "MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0146"
---

## Question

The account manager found a removal order that Amazon had created automatically because too much stock was in the warehouse, and had to decide whether to stop it or let the units come back.

## Answer

When an automatic removal starts pulling excess FBA stock, open the order and cancel pending units before they ship if you still want to sell them. Compare the removal and return cost with the extra storage fees of selling through, and price the overstock to move when selling is cheaper. Confirm the return address for units already in transit, and review the automatic removal setting so the order does not return.

## Cause

The removal came from Amazon's automatic removal. The thread names overstock as the trigger and does not show the setting. Automatic removals are a seller setting in Fulfillment by Amazon settings that can cover unfulfillable inventory, inventory subject to long-term storage fees, or both. Removal orders still in Pending or Planning status can usually be cancelled before they ship. Required removals cannot be cancelled by the seller.

## Fix

1. Open the removal order detail and confirm whether units are being returned or disposed, and that the order is not a required removal. 2. Cancel the pending quantities that have not shipped yet (operator approval required), and recheck later because a cancel request is not guaranteed. 3. Check the return address on any units already sent so they arrive at the right location. 4. Decide per SKU whether selling through, even with higher storage fees, costs less than removal plus re-handling. If so, lower the price to clear the overstock (operator approval for price changes). 5. Review the automatic removal setting under Fulfillment by Amazon settings so a new order is not created (operator approval for settings changes).

## Verify

The removal order detail shows the remaining quantities as cancelled and the units stay available in Manage FBA Inventory.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the sell-through versus removal cost decision for an Amazon-created excess-stock removal, beyond the existing cancel procedure.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`).
