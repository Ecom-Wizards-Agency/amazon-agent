---
id: KC-0208
title: "How to name seller SKUs so FBA, FBM and per-marketplace offers stay clear"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central inventory / flat files"
surface_verified: false
symptom_keywords: ["SKU naming convention", "seller SKU FBA FBM suffix", "SKU per marketplace", "same ASIN new SKU", "MPN as SKU"]
error_text: []
asked_as: ["A new seller used internal model numbers as seller SKUs and asked why the agency recommended adding fulfillment channel and marketplace suffixes, since the product is the same in every country."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md", "Amazon Seller Help/articles/189-amazon-north-american-and-brazil-stores-G201394090.md", "Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md"]
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0208"
---

## Question

A new seller used internal model numbers as seller SKUs and asked why the agency recommended adding fulfillment channel and marketplace suffixes, since the product is the same in every country.

## Answer

Build seller SKUs from your internal product code plus a fulfillment-channel suffix such as -FBA or -FBM. Amazon needs a separate SKU per channel on the same ASIN and suggests a suffix to tell them apart. Add a marketplace suffix only for offers managed store by store: Pan-European FBA needs the same SKU in every EU store and a North America Global SKU is shared, so a country suffix would break them.

## Cause

A seller SKU identifies one offer. Amazon requires a separate SKU for each fulfillment channel on the same ASIN and suggests adding -FBA to tell them apart. Across marketplaces it depends on the program: Pan-European FBA requires the same SKU in the EU stores, and a North America Global SKU is shared across stores, while a store-specific SKU can differ. The thread's advice to append a marketplace code to every SKU does not account for this.

## Fix

1. Keep the internal model or MPN code as the SKU stem.
2. Append the fulfillment channel (FBA or FBM); Amazon requires a separate SKU per channel on the same ASIN.
3. Add a marketplace suffix only for offers managed store by store; leave it off for products that will use Pan-European FBA or a North America Global SKU, which need the same SKU across stores.
4. Use these SKUs consistently in flat files and spreadsheets to reduce bulk-edit errors.

## Verify

An inventory export shows each SKU's stem and channel suffix, no SKU is shared between an FBA and an FBM offer, and SKUs intended for Pan-European FBA are identical across the EU stores.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/009-get-started-with-fulfillment-by-amazon-fba-G53921.md`
- First-party: `Amazon Seller Help/articles/189-amazon-north-american-and-brazil-stores-G201394090.md`
- First-party: `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds an agency SKU naming convention with fulfillment channel and marketplace suffixes.
- Existing coverage: partial.
