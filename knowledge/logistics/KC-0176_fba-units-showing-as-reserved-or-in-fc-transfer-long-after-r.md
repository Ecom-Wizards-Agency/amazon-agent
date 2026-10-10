---
id: KC-0176
title: "FBA units showing as reserved or in FC transfer long after receipt: transfer between fulfillment centers, not lost"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > FBA Inventory (Reserved / FC transfer)"
surface_verified: false
symptom_keywords: ["units stuck in reserved", "FC transfer taking weeks", "reserved inventory after AGL shipment", "cannot create bundle reserved units"]
error_text: []
asked_as: ["After a slow inbound, many units of an ASIN showed as reserved weeks later and the client asked whether they were lost or sellable."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md", "MAG SOPs/general/supplemental-article-reviving-sales-on-amazon-strategies-for-overcoming-common-seller-challenges.md"]
supersedes: []
contradicts: []
observed: 2024-07
review_by: 2027-10
provenance: "ledger:KC-0176"
---

## Question

After a slow inbound, many units of an ASIN showed as reserved weeks later and the client asked whether they were lost or sellable.

## Answer

FBA units that look reserved long after receipt are usually in FC transfer between fulfillment centers, not lost. They stay buyable, though shoppers may see a later ship date or lose the Prime badge. Wait out the transfer window, about three to four weeks per one account manager, then request an investigation if units still have not arrived. In the US Inventory Overview, FC transfer units now count under On-hand, while reports were due to follow by mid-2026, so check which view you are reading.

## Cause

The units had been received and were in FC transfer between fulfillment centers. The MAG SOP states that FC transfer units are customer-purchasable; shoppers may see a later ship date, and a MAG supplemental article notes that the Prime badge can drop. Per the thread, transfers can take about 22 to 25 days and sometimes longer, after which an investigation can be requested; no local first-party capture confirms that window.

## Fix

1. Open the inventory breakdown for the ASIN and confirm the units are in FC transfer rather than FC processing or customer orders. In the US Inventory Overview, FC transfer now sits under On-hand, not Reserved.
2. Confirm the listing stays buyable and check the ship date and Prime badge shoppers see.
3. Note the date after which a transfer investigation can be requested, and open a case then if units have not arrived (operator approval).
4. Plan bundle creation after the transfer, because the thread reports that bundles could not be created on those ASINs while units were in transfer.

## Verify

Units move from FC transfer to available or on-hand, or an investigation case is opened after the eligibility date.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`
- Also in: `MAG SOPs/general/supplemental-article-reviving-sales-on-amazon-strategies-for-overcoming-common-seller-challenges.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the FC transfer timing window, buyability and post-window investigation step for units that look stuck in reserved status.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`, `MAG SOPs/catalog/logistics-sop-remove-inventory-from-a-fulfillment-center.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
