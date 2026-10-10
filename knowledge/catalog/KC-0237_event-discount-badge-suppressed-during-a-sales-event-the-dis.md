---
id: KC-0237
title: "Event discount badge suppressed during a sales event: the discounted price was not low enough to qualify"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Advertising > Prime Exclusive Discounts / Price discounts (event deal badge)"
surface_verified: false
symptom_keywords: ["deal badge not showing", "discount suppressed", "BFCM discount not displayed", "strike-through price missing", "prime exclusive discount suppressed"]
error_text: []
asked_as: ["During the first week of a major sales event, a discount set on one product was suppressed and no deal badge showed; the team asked what it took to get the badge back."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0237"
---

## Question

During the first week of a major sales event, a discount set on one product was suppressed and no deal badge showed; the team asked what it took to get the badge back.

## Answer

When an event discount is suppressed or shows no badge, first check the discounted price against the 30-day lowest non-promotional price customers paid and the current price, and against the validated reference price where one exists. Amazon's standing criteria require at least 5% off each, and event criteria shown in the Price Discounts tool can differ. A discount set from the list price can miss if the item sold lower recently; lower the discounted price with approval and recheck the badge.

## Cause

Not fully established in the thread, which names neither the discount type nor a suppression reason. A lower discounted price restored the badge, which fits Amazon's price-discount eligibility criteria: at least 5% off the 30-day lowest non-promotional price bought by customers (across all sellers), at least 5% off the current price and, for products with a validated reference price, at least 5% off that price. Criteria for an event can differ and are shown in the Price Discounts tool.

## Fix

1. Open the discount in Seller Central and read its status and any reason shown.
2. Compare the discounted price against the 30-day lowest non-promotional price customers paid (across all sellers), the current price and, where one exists, the validated reference price; read any event-specific criteria shown in the Price Discounts tool.
3. Lower the discounted price until it meets every criterion (operator approval required before changing a price or promotion).
4. Recheck the detail page and search result after the change for the deal badge and strike-through price.

## Verify

The discount row no longer shows as suppressed and the deal badge or strike-through price appears on the detail page and in search results.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The price-discount page states the 5% thresholds, but nothing local links a suppressed event discount badge to them as a first diagnostic check.
- Existing coverage: full (`Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/074-amazon-outlet-GHLYT4TPVCY2MJE3.md`, `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
