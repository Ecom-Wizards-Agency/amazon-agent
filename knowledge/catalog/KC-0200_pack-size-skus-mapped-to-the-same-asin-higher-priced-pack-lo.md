---
id: KC-0200
title: "Pack-size SKUs mapped to the same ASIN: higher-priced pack loses the Featured Offer and the variation splits"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory; detail page variation selector"
surface_verified: false
symptom_keywords: ["2 pack no buy box pricing error", "variation split single pack shows wrong image", "two SKUs same ASIN different pack size", "pack of 2 title but customer gets 1"]
error_text: ["Out of Stock"]
asked_as: ["After reparenting, a 1-pack and 2-pack variation still looked split on the detail page; the 2-pack had no Buy Box, selecting it showed the 1-pack image and title, and customers ordering a 2-pack riske"]
synonyms: []
resolution_status: resolved
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/137-featured-offer-G37911.md", "Amazon Seller Help/articles/144-product-variations-GF4VNS6ZQQPYYGGP.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0200"
---

## Question

After reparenting, a 1-pack and 2-pack variation still looked split on the detail page; the 2-pack had no Buy Box, selecting it showed the 1-pack image and title, and customers ordering a 2-pack risked receiving a 1-pack.

## Answer

When a multipack loses the Featured Offer with a pricing error and the variation looks split, check whether a SKU of another pack size is attached to the same ASIN. In the source case Seller Support explained that Amazon took the single-pack price as the competitive reference for that ASIN, so the multipack offer looked overpriced. Map each SKU to the ASIN of its own pack size, then confirm that the variation family and the Featured Offer recover.

## Cause

The 1-pack SKU had been linked to the 2-pack ASIN, so SKUs of different pack sizes and prices sat on one ASIN. Amazon used the lower 1-pack price as the competitive reference for that ASIN, judged the 2-pack offer overpriced and withheld the Featured Offer. The real 1-pack ASIN lost its offer, dropped out of the variation family and showed as out of stock.

## Fix

1. ["1. In Manage All Inventory, search by ASIN and list every SKU attached to each pack-size ASIN; flag any ASIN carrying SKUs with different pack sizes or prices.", "2. Move the misattached SKU to the ASIN of its own pack size by deleting that offer and recreating it on the correct ASIN; the product ID of an existing listing is not editable unless it was created with a GTIN exemption, so a flat-file edit alone will not remap it (listing changes need operator approval).", "3. Confirm the corrected child sits under the parent again in the variation family.", "4. Wait for the Featured Offer to return on the higher pack size; in the source case the offer showed before the Buy Box did."]

## Verify

Each pack-size ASIN carries only its own SKUs, both children show in the variation selector with their own image and title, and the higher pack size wins the Featured Offer.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/137-featured-offer-G37911.md`
- First-party: `Amazon Seller Help/articles/144-product-variations-GF4VNS6ZQQPYYGGP.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Names a SKU of another pack size attached to the same ASIN as the cause of a lost Featured Offer and a split variation, which KC-0011 and the SOPs do not cover.
- Existing coverage: partial (`knowledge/account-health/KC-0011_buy-box-featured-offer-lost-to-a-pricing-health-uncompetitiv.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
