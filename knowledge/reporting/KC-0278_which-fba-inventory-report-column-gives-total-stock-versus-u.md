---
id: KC-0278
title: "Which FBA inventory report column gives total stock versus units available to sell"
kind: reference
topic: reporting
status: reviewed
skills: [amazon-reporting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Reports > Fulfillment > Manage FBA Inventory (FBA_MYI_UNSUPPRESSED_INVENTORY); Restock Inventory; Inventory > Manage FBA inventory"
surface_verified: false
symptom_keywords: ["how to export available FBA stock daily", "afn-total-quantity vs fulfillable", "inventory report totals do not match", "inbound vs reserved stock"]
error_text: [FBA_MYI_UNSUPPRESSED_INVENTORY, afn-total-quantity, afn-fulfillable-quantity, afn-onhand-buyable-quantity]
asked_as: ["A client wanted a daily export showing stock available for sale now and stock still to arrive, and was confused by different totals in the Restock report, the FBA inventory page and the inventory repo"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0278"
---

## Question

A client wanted a daily export showing stock available for sale now and stock still to arrive, and was confused by different totals in the Restock report, the FBA inventory page and the inventory report.

## Answer

For daily stock tracking, pull the Manage FBA Inventory report. Read afn-total-quantity for everything Amazon counts, including inbound, and afn-fulfillable-quantity for what can sell now. Do not add the Restock report or inbound figures on top, because the total already contains them. Total minus fulfillable also contains unfulfillable and researching units, so it overstates stock still to arrive.

## Cause

The reports count different buckets: afn-total-quantity includes inbound, reserved, unfulfillable and researching units; the Restock export total excludes unfulfillable and researching; inbound units become reserved once booked in before turning fulfillable.

## Fix

1. ["1. Request the Manage FBA Inventory report (FBA_MYI_UNSUPPRESSED_INVENTORY) as CSV daily.", "2. Use afn-total-quantity as the full total; inbound is already included, so do not add Restock or other report figures.", "3. Use afn-fulfillable-quantity for units available to sell now, and afn-onhand-buyable-quantity for available plus FC transfers.", "4. Total minus fulfillable gives units not sellable yet. That remainder holds inbound and reserved units plus any unfulfillable or researching units, which may never become sellable, so subtract the unsellable and researching columns if you want only stock still to arrive."]

## Verify

The daily total, available and not-yet-available figures reconcile with the Inventory column on the Manage FBA inventory page.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Maps the exact Manage FBA Inventory columns to total, available and not-yet-available stock and warns against adding the Restock or inbound figures on top.
- Existing coverage: partial.
