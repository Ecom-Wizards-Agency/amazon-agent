---
id: KC-0007
title: "Cancel an Amazon-initiated disposal of stranded FBA inventory through Seller Support and harden automated removal settings"
kind: procedure
topic: support-cases
status: draft
skills: [amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Removal orders (removal-order detail); Fulfillment by Amazon settings > Automated removal settings; Seller Support chat"
surface_verified: false
symptom_keywords: ["amazon started disposal order", "cancel disposal stranded inventory", "automated removal settings", "stop amazon destroying inventory during appeal", "disposal order while appeal pending"]
error_text: []
asked_as: ["The client saw that Amazon had started a disposal order for their inventory and asked whether Amazon would go through with it while their appeal was open, and how to stop it."]
synonyms: ["Entsorgung", "disposal order", "stranded inventory"]
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md", "MAG SOPs/catalog/catalog-sop-fba-removal-order.md", "MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md", "sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0007"
---

## Question

The client saw that Amazon had started a disposal order for their inventory and asked whether Amazon would go through with it while their appeal was open, and how to stop it.

## Answer

A pending appeal does not stop FBA from disposing of stranded units. When a listing is blocked, set a return address and the longest automated-removal delay at once, before Amazon creates a disposal order. If a disposal order already exists and the seller-side Cancel button is not available, ask Seller Support to cancel it, keep the removal-order page as proof, and recheck regularly, because Amazon may start a new one without warning.

## Cause

The listings were blocked and under appeal, so the units were stranded. Amazon's automated removal then created a disposal order. The account had no return address and no automated-removal preference set to return units instead of disposing of them.

## Fix

1. Treat the open appeal as no protection: it does not pause automated removal or disposal of stranded inventory.
2. Set a return address and the 'Full name' field (brand or company name) in the removal and return settings so a future automated removal ships back instead of being destroyed. Settings changes need operator approval.
3. Set automated removal to the longest available wait: 60 days for account-status issues and 30 days for listing or inventory issues (labels seen on one account; the extra 30-day delay option was not offered there).
4. Before asking Support, open the order in Reports > Fulfillment > Removal Order Detail and read Order type and Order source. An order source naming the Automated Recalled Units Removal System, or a product-safety, recall or required-removal notice in Account Health, marks a required or recall removal. The seller cannot cancel a required removal, so ask Support for a hold and escalation instead of a plain cancellation. An order tied only to the stranded listing and the automated-removal settings is the case this unit covers.
5. Contact Seller Support by chat and ask them to cancel the Amazon-initiated disposal order. Keep the removal-order detail page as proof of cancellation.
6. Ask how much grace time remains; Support would not commit to one and said to come back if a new order starts.
7. Monitor for a new removal order. If one starts and cannot be cancelled, it now goes to the return address.
8. Confirm that the cancelled units return to sellable or stranded inventory.

## Verify

The disposal order showed as cancelled on the removal-order detail page and the units were reported as returning to inventory. No later stock count appears in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`
- Also in: `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md` (draft; informed step 4: order source, order type and recall detection)
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source covers an Amazon-initiated disposal of stranded inventory, asking Seller Support to cancel it, or setting the return address and automated-removal delays first.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`).
- The cancel-removal SOP says Required Removals cannot be cancelled but not how to recognise one. The recall order-source label comes from a draft checked live on 03.08.2026; the exact Order source label of an automated stranded-inventory removal is not captured.
