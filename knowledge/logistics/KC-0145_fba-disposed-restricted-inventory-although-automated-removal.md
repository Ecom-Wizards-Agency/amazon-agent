---
id: KC-0145
title: "FBA disposed restricted inventory although automated removals were set to send back to the seller"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-account-health-check, amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: "FBA removal orders (Automated Recalled Units Removal); automated removal settings"
surface_verified: false
symptom_keywords: ["Amazon disposed inventory without asking", "removal settings say return but units disposed", "recalled units removal disposal", "restricted product inventory destroyed", "can we recover disposed FBA units"]
error_text: ["Your Amazon.com Inventory - Action Required", "There is no settings for this recalled units removals."]
asked_as: ["The team found that most of a product's FBA inventory had been disposed even though the automated removal setting was 'Send back to warehouse'; only part of the units came back, and they asked why and"]
synonyms: []
resolution_status: diagnosis-only
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md, knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md, "MAG SOPs/catalog/catalog-sop-fba-removal-order.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0145"
---

## Question

The team found that most of a product's FBA inventory had been disposed even though the automated removal setting was 'Send back to warehouse'; only part of the units came back, and they asked why and whether the stock or its value could be recovered.

## Answer

Return-to-seller settings do not protect inventory from a recall or required removal: when a product becomes restricted and is not reinstated in time, Amazon can dispose of the units, charge the disposal fee and pay no reimbursement. Check Removal Order Detail for the order source, and treat any 'Action Required' inventory email or Account Health policy item as a deadline. Escalate the same day and ask Support for a hold before the disposal date.

## Cause

The product had become restricted and the listing was not reinstated in time, so Amazon created a recalled-units removal. Recall and required removals do not follow the seller's automated removal setting; Amazon Support confirmed there is no setting for them. An 'Action Required' inventory email had arrived about a month earlier and was not acted on.

## Fix

1. Open Reports > Fulfillment > Removal Order Detail and read Order type and Order source; a source naming the recalled-units removal system marks a recall removal that ignores the return setting.
2. Ask Seller Support (operator approval required to send) whether any units are still recoverable; disposed units are not returned, and the disposal fee stands.
3. Book the cost of goods of the disposed units as an expense in the profit tool so margins stay accurate.
4. Search the account's email for 'Action Required' inventory notices and Account Health product-policy items; treat them as deadlines.
5. Going forward, escalate a restricted or recalled listing the same day and request a hold on any recall removal before the disposal date.

## Verify

Removal Order Detail shows the order source and the disposed versus returned counts, and the cost of the disposed units is recorded in the profit tool.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`
- Also in: `knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: KC-0007 and the draft cover recognising and escalating a recall removal; this card adds the after-the-fact outcome (units unrecoverable, disposal fee charged, no reimbursement) and the trigger chain from a restricted listing plus an ignored 'Action Required' email.
- Existing coverage: full (`knowledge/support-cases/KC-0007_cancel-an-amazon-initiated-disposal-of-stranded-fba-inventor.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`, `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
