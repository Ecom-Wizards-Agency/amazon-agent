---
id: KC-0310
title: "Both FBA and FBM offers on the same products: which SKUs should the ads promote?"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads > Campaign manager > Sponsored Products ad groups"
surface_verified: false
symptom_keywords: ["advertise FBA or FBM SKU", "FBM ads low conversion", "switch ads to FBA SKUs", "Prime eligible inventory ads"]
error_text: []
asked_as: ["After most of the FBA inventory became Prime eligible and most orders shifted from FBM to FBA, the ads manager asked whether to advertise the FBA SKUs and pause the FBM ones."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md", "Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0310"
---

## Question

After most of the FBA inventory became Prime eligible and most orders shifted from FBM to FBA, the ads manager asked whether to advertise the FBA SKUs and pause the FBM ones.

## Answer

When a product has both FBA and FBM offers, advertise the SKU whose offer holds the featured offer, because Sponsored Products ads only show for the featured offer. Once the FBA offer is in stock and Prime eligible, that is usually the FBA SKU, so move ads to it and pause the FBM SKU ads. In one account this coincided with higher conversion rate and ROAS the following month. Treat that as a signal to check on your own account, not a guaranteed lift.

## Cause

Sponsored Products ads show only when the advertised product is the featured offer, and Amazon advises choosing products that display it. Once the FBA offer was in stock and Prime eligible, it became the offer shoppers saw and bought. In this account, conversion rate and ROAS rose in the month orders shifted to the FBA SKUs. That is one before-and-after month, not a controlled test.

## Fix

1. Check what share of FBA inventory is Prime eligible and whether most orders now come through the FBA offer.
2. Check which of your own offers holds the featured offer on each ASIN.
3. When the FBA offer is in stock and holds the featured offer, advertise the FBA SKU and pause the duplicate FBM SKU ads (operator approval for the change).
4. Review the FBA offer's price. The thread adjusted pricing alongside the switch but did not state why; competitive pricing helps keep the featured offer.
5. Compare conversion rate and ROAS for the advertised products against the prior period.

## Verify

Conversion rate and ROAS on the advertised products improve against the prior period with FBA SKUs advertised and FBM ad SKUs paused.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md`
- First-party: `Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a decision aid for moving ad spend from FBM to FBA SKUs once FBA stock is Prime eligible, which no covered page states.
- Existing coverage: partial (`Advertising Help After Login/articles/036-sponsored-products-GJUCNANNV3GQVXJZ.md`, `Advertising Help After Login/articles/033-optimize-products-for-advertising-GXAMM4S99TTG2Y57.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
