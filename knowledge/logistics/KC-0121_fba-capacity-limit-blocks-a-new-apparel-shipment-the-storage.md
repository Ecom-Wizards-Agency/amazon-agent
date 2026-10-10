---
id: KC-0121
title: "FBA capacity limit blocks a new apparel shipment: the storage type cannot be switched to use another limit, and limits shown in cubic metres must be requested in cubic feet"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-communications]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Inventory Levels Monitor (Inventory volume section); Shipping Queue; Seller Support case"
surface_verified: false
symptom_keywords: ["FBA capacity limit exceeded apparel", "cannot create shipment capacity", "storage limit increase case", "change apparel to standard size", "cubic feet vs cubic metres capacity"]
error_text: ["[\"Current usage as of <date>, <time> CEST <n>% used (<x> of <y> cubic metres)\", \"Kindly know that Amazon does not grant storage-limit increase requests generally.\", \"We review storage-limit appeals on a case-by-case basis.\"]"]
asked_as: ["The client could not create a new FBA shipment for an apparel product because the apparel capacity was used well beyond its limit."]
synonyms: []
resolution_status: partial
fix_source: amazon-support
evidence_location: case
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md"]
related_sops: [knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md]
supersedes: []
contradicts: []
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0121"
---

## Question

The client could not create a new FBA shipment for an apparel product because the apparel capacity was used well beyond its limit. They asked whether they could switch the product to standard-size to use that larger limit, and how to get more space before the next month.

## Answer

When FBA capacity blocks a shipment, check usage per storage type and do not try to move the product to another storage type to borrow its limit; Amazon assigns the storage type. Request more space through Capacity Manager, and convert cubic metres to cubic feet before you enter any number, because EU screens show cubic metres while requests use cubic feet. A Seller Support appeal is a case-by-case fallback that needs the quarter, storage type, desired and existing limits in cubic feet, a business justification and the impacted FNSKUs.

## Cause

Each storage type has its own capacity limit and Amazon sets the storage type from its own classification, so apparel cannot be moved to standard-size. Inventory volume above the apparel limit blocks new shipments for that storage type.

## Fix

1. ["1. Read current usage and limits per storage type in the Inventory volume section at the bottom of Inventory Levels Monitor or in the Shipping Queue (now Capacity Monitor). The EU interface shows cubic metres; Amazon's requests use cubic feet (1 cubic metre is about 35.3 cubic feet).", "2. Do not change the product's category or storage type to use another limit; Amazon assigns the storage type.", "3. Request more capacity through Capacity Manager first (see the related unit KC-0004 and the capacity help capture).", "4. If you appeal through Seller Support instead (send needs operator approval), the field list Amazon quoted in a 2024 case was: current or next quarter; type of increase (Standard, Oversize, Footwear, Apparel); whether it is a restock-limit increase; desired limit in cubic feet; existing limit in cubic feet; a detailed business justification; the impacted FNSKUs. Amazon reviews these case by case.", "5. Size the request to the planned inbound. The agency's view was that more headroom than needed only adds storage fees and that limits rise as sales grow."]

## Verify

Amazon's reply listed the required fields and the agency drafted the follow-up; the outcome is not in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/067-maximizing-delivery-speed-GA8NP4NDZZ3EJRU5.md`
- Also in: `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the rule that the storage type cannot be switched to borrow another limit and the cubic metres to cubic feet trap. The Seller Support field list is already in the MAG capacity SOP email template, and KC-0004 covers the current Capacity Manager route.
- Existing coverage: partial (`knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
