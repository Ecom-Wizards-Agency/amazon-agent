---
id: KC-0218
title: "Cannot A/B test a new main image because the ASIN is not eligible in Manage Your Experiments: use a paid shopper poll and match the pack size shown"
kind: decision-aid
topic: catalog
status: reviewed
skills: [amazon-listing-images, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Brands > Manage Your Experiments; external shopper-poll tools"
surface_verified: false
symptom_keywords: ["main image A/B test low sales", "ASIN not eligible Manage Your Experiments", "test main image without MYE", "shopper poll main image", "main image shows wrong pack size"]
error_text: []
asked_as: ["The team made new main-image variants and wanted to A/B test them, but the products had too few sales to run an experiment on Amazon."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md", "Amazon Seller Help/articles/153-product-image-guide-G1881.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md"]
supersedes: []
contradicts: []
observed: 2025-09
review_by: 2027-10
provenance: "ledger:KC-0218"
---

## Question

The team made new main-image variants and wanted to A/B test them, but the products had too few sales to run an experiment on Amazon. The client also questioned the square format and noticed that one variant showed a multi-pack although the product is sold as a single unit.

## Answer

When an ASIN has too little traffic for Manage Your Experiments, compare main-image variants with a paid external shopper poll, or drive more traffic to the ASIN first. Start with the variant that sells most, and make sure every candidate image shows the same quantity the offer sells, because the main image must show the real quantity of the product. A poll measures stated preference, not live conversion, so confirm with sales data after publishing.

## Cause

Manage Your Experiments only accepts high-traffic ASINs owned by the brand, so low-sales ASINs cannot be tested on Amazon. Separately, a main image that shows more units than the offer contains misrepresents the product.

## Fix

1. Check the ASIN's eligibility in Manage Your Experiments. Low-traffic ASINs may not appear at all.
2. If it is not eligible, either drive more traffic to it first (the route Amazon's page suggests) or run a paid shopper poll with an external panel to compare the variants.
3. Prefer testing on the variant with the most traffic and sales so results arrive faster, then roll the winning style out to the other variants.
4. Before testing, check that every main-image variant shows exactly the quantity the offer sells.
5. Settle the image format before testing so that every candidate uses the same one.

## Verify

The poll returns a winner, and the published main image shows the same unit count as the offer.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- First-party: `Amazon Seller Help/articles/153-product-image-guide-G1881.md`
- Also in: `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Low-traffic ASINs that Manage Your Experiments rejects can be compared with a paid external shopper poll, starting on the best-selling variant and checking each image shows the offer's pack size.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `Amazon Seller Help/articles/153-product-image-guide-G1881.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-a-content.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
