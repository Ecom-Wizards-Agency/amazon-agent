---
id: KC-0336
title: "Listing title or Item Highlights look rewritten by Amazon AI: check whether the text is in your own seller contribution first"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog, amazon-flatfilepro, amazon-seo]
marketplaces: [US]
marketplace_inferred: false
surface: "FlatFilePro connector live reads (getListingsItem, getCatalogItem); Seller Central > Manage All Inventory"
surface_verified: false
symptom_keywords: ["amazon ai changed our title", "title shows features the product does not have", "displayed title differs from what we submitted", "brand name moved to the front of the title", "item highlights wrong", "who changed the listing title"]
error_text: ["Value for 'Item Highlight' is longer than the allowed maximum (125 characters)."]
asked_as: ["The client says Amazon AI is messing up our titles: the listing claims accessories the product does not include. Did Amazon do this or did we?"]
synonyms: ["Item Highlights / title_differentiation", "item name / title", "seller contribution / listing data", "catalog data / detail page data", "Titel / Artikelname"]
resolution_status: diagnosis-only
fix_source: agency
evidence_location: run-note
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md", "Amazon Seller Help/articles/149-enhance-listings-G88AQCL62ED7WDGA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0336"
---

## Question

A client sees wrong words in a title or Item Highlights, for example accessories that are not in the box, and blames Amazon's AI. How do you tell whether Amazon changed it or the text came from our own copy?

## Answer

Compare three texts before you answer: what the seller submits, what Amazon displays, and what our SEO source document proposed. If the seller contribution holds the same words, the copy is ours, even when the client calls it AI. Amazon usually does something narrower: it reorders or shortens the displayed title, keeps an older title in the catalog, or adds catalog attributes nobody on the account submitted.

## Cause

A detail page shows Amazon's merged catalog record, not one seller's submission. Amazon can auto-correct a non-compliant title, can keep an older contributor's value when a newer one conflicts (error 8541), and can fill attributes from other sources. Amazon's Enhance Listings tool generates AI suggestions, but they reach the listing only when a seller user accepts them. Keyword-led rewrites have their own failure mode: a high-volume term that is not true of the product (accessories, features, "set", "kit") gets into the copy because it scores well.

## Fix

1. Read the seller contribution per SKU: FlatFilePro `flatfilepro_get_listings_item_from_amazon`, fields `attributes.item_name`, `attributes.title_differentiation`, `attributes.bullet_point` and `issues`.
2. Read the ASIN view: `flatfilepro_get_catalog_item_from_amazon`. `summaries[0].itemName` is the displayed title; compare its `title_differentiation` and `bullet_point` with the seller values.
3. Find the source document (keyword workbook, copy doc) and search it for the exact words. Check the copy history too (earlier Category Listings Report or saved FlatFilePro read).
4. Check product truth for every concrete claim: gallery images (especially unboxing), brand site, label.
5. Classify each difference: identical in contribution and catalog = our copy; displayed differs from every contribution = Amazon display rewrite; attribute present only in the catalog = Amazon or another contributor.
6. Prepare corrected copy for approval. Remove only false or unsupported terms and keep the length limits (title 75, Item Highlights 125 characters).

## Verify

After an approved update, re-run both reads after 24 to 48 hours: the seller contribution and the catalog view must both show the corrected text, and `issues` must be free of new errors.

## Stop before

Stop before any listing change, catalog case or client message until the operator approves that exact action. Do not tell the client it was Amazon until the reads prove it.

## Sources

- First-party: `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md` (titles that do not comply "might be automatically corrected"; Item Highlights add 125 characters; updates take 24 to 48 hours). `Amazon Seller Help/articles/149-enhance-listings-G88AQCL62ED7WDGA.md` (AI suggestions apply only when a user accepts them).
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Observed on one US account: Amazon displayed "<entity> by <brand> …" as "<brand> <entity> …" on about one ASIN in six, with no pattern found for which ASINs.
- Error 90225 appeared on Item Highlights of 104 to 125 characters; the cause is unknown.
- Whether Enhance Listings suggestions were ever accepted on an account cannot be read from the API.
