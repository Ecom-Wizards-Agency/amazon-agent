---
id: KC-0187
title: "Restricted FBA units disposed automatically even though automated removal was set to return them"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > Create removal order (Total inventory not available for removal); Settings > Fulfillment by Amazon > Automated removal settings"
surface_verified: false
symptom_keywords: ["amazon disposed restricted inventory", "automatic return setting ignored disposal", "units not available for removal disposed", "cannot recover disposed fba units", "blocked asin inventory destroyed"]
error_text: []
asked_as: ["FBA units of a blocked product were disposed of by Amazon although automated removals were set to return units."]
synonyms: []
resolution_status: diagnosis-only
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/065-fba-inventory-G201074410.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fba-removal-order.md", sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md, knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0187"
---

## Question

FBA units of a blocked product were disposed of by Amazon although automated removals were set to return units. The agency had also tried to remove the stock to save storage fees but could not select all units. The seller asked whether anything could be recovered and why the disposal notice emails arrived so late.

## Answer

Do not count on the automated-removal return setting to protect restricted FBA units, because units that are not available for removal can still be disposed of by Amazon. When a product is blocked, remove all available units at once and ask Seller Support in writing to return the restricted units instead of disposing of them. Track the disposal notice dates, since a started disposal cannot be undone.

## Cause

Not stated by Amazon; inferred from the outcome. Units of the blocked product were shown as not available for removal, so the removal order covered only part of the stock. The automated-removal return setting did not protect the remaining restricted units, and Amazon disposed of them. Seller Support said nothing could be recovered once disposal had run. The disposal-prevention draft notes that return settings may not override required or recall-generated removals, which fits but was not confirmed for this case.

## Fix

1. As soon as a product is blocked with FBA stock, open Create removal order and check 'Total inventory not available for removal' and its reason legend for restricted units.
2. Remove every unit that is available at once, with a return address on file.
3. For restricted units that cannot be selected, open a Seller Support case asking for a return removal and asking Amazon to hold disposal; do not rely on the automated-removal return setting (case send needs operator approval).
4. Watch notification emails and the removal-orders page (Order type, Order source) for an Amazon-initiated disposal and escalate it the same day, following KC-0007.
5. If disposal has already run, expect that the units cannot be recovered.

## Verify

No Amazon-initiated disposal order appears for the restricted units, and a return removal order covers them.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/065-fba-inventory-G201074410.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Also in: `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`
- Also in: `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: KC-0007 covers stranded-inventory disposal during an appeal; this adds that restricted units unavailable for removal were disposed despite a return preference and could not be recovered.
- Existing coverage: full (`knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`).
