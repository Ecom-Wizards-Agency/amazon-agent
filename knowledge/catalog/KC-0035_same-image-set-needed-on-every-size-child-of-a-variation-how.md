---
id: KC-0035
title: "Same image set needed on every size child of a variation: how to avoid uploading images one listing at a time"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Catalog > Upload Images (bulk image upload); category inventory file"
surface_verified: false
symptom_keywords: ["upload same images to all sizes", "bulk image upload ASIN.MAIN PT01", "copy image URLs to other child ASINs flat file", "upload images for many variations at once", "image naming convention bulk upload"]
error_text: []
asked_as: ["A designer had new gallery images for two new colours of a variation with many sizes and wanted a faster way than uploading seven images to every size in the listing editor."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/153-product-image-guide-G1881.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0035"
---

## Question

A designer had new gallery images for two new colours of a variation with many sizes and wanted a faster way than uploading seven images to every size in the listing editor.

## Answer

When a variation has many sizes that share one image set, do not upload the images to each child by hand. Name the files ASIN.MAIN, ASIN.PT01 and so on for each child and load them as one zip in the bulk image uploader, or upload once to one child and copy the hosted image URLs to the siblings through a category inventory file. Check every child after processing.

## Cause

Each size is its own child ASIN with its own image set, so the listing editor needs one upload per child. Two bulk paths avoid that: the bulk image uploader matches images to ASINs by file name, and a category inventory file can point every child at image URLs that Amazon already hosts.

## Fix

1. Option A, bulk image upload: rename each image as ASIN.VARIANT plus extension (for example ASIN.MAIN.jpg, ASIN.PT01.jpg, ASIN.PT02.jpg) for every child ASIN, with no spaces or extra characters.
2. Zip the renamed files and drag the zip into the Bulk Image Upload tool under Upload Images; check the upload status for rejected files.
3. Option B, copy URLs: upload the images to one child per colour in the listing editor and wait until Amazon accepts them.
4. Export that child's listing data, copy its main and other image URLs into the rows of the sibling sizes in a category inventory file, and upload it as a partial update (upload needs operator approval).
5. Check every child's detail page shows the new images in the intended order.

## Verify

Every size of each colour shows the same main and secondary images on its detail page.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/153-product-image-guide-G1881.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the alternative of copying hosted image URLs from one accepted child to its siblings through a category inventory file.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md`).
