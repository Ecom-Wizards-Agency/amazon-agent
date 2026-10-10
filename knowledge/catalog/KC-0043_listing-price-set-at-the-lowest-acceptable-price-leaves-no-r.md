---
id: KC-0043
title: "Listing price set at the lowest acceptable price leaves no room for event deals"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Pricing; Deals; Prime Exclusive Discounts"
surface_verified: false
symptom_keywords: ["price too low for Prime Day deal", "reference price for deals", "always discounted price no room for promotion", "set base price before Prime Day", "deal price must be lower than recent price"]
error_text: []
asked_as: ["A client operator asked whether to list at the lowest acceptable price all year or start higher and discount to it."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md"]
supersedes: []
contradicts: []
observed: 2024-09
review_by: 2027-10
provenance: "ledger:KC-0043"
---

## Question

A client operator asked whether to list at the lowest acceptable price all year or start higher and discount to it.

## Answer

Do not set the everyday price at the floor you can accept, because deals must undercut recent prices and show a savings against a valid reference price. Set the everyday price between the recommended retail price and the floor, and hold it stable for weeks before an event. Then the event discount lands near the floor instead of below it.

## Cause

Deals and discounts are measured against recent prices: a deal must undercut the recent lowest price and show a savings against a valid reference price. If the everyday price already sits at the floor, an event deal pushes the price below the floor or is not possible. The thread states the event needs the higher price in place for about four weeks ahead and a discount of around 20 percent; those figures are the agency's working rule, not confirmed in a captured page.

## Fix

1. Separate three prices: the brand's recommended retail price, the everyday Amazon price, and the floor price below which an order loses money.
2. Set the everyday Amazon price between the recommended retail price and the floor, not at the floor.
3. Keep that everyday price stable for several weeks before a planned event so the reference and recent lowest price support the deal.
4. Plan the event discount so the deal price lands near the floor; agree with the brand in advance how far below the floor an event may go.

## Verify

The deal or discount is accepted without a price suppression, and the deal price shows a savings against the reference price.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit tells sellers to keep the everyday price between recommended retail and the floor so event deals can undercut recent prices without going below the floor.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`, `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`, `MAG SOPs/catalog/merchandising-sop-amazon-list-price-mrsp.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
