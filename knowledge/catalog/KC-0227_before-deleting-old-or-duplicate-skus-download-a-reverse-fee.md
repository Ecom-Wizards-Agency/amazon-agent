---
id: KC-0227
title: "Before deleting old or duplicate SKUs, download a reverse feed of their listing data as a backup"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["delete old SKUs", "duplicate SKUs different creation date", "backup before deleting listings", "reverse feed before delete", "category listings report backup"]
error_text: []
asked_as: ["While cleaning up the catalog, a teammate found SKUs with two different creation dates and asked whether to treat the older ones as old SKUs to delete."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-download-category-listings-report.md", "MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md"]
supersedes: []
contradicts: []
observed: 2024-09
review_by: 2027-10
provenance: "ledger:KC-0227"
---

## Question

While cleaning up the catalog, a teammate found SKUs with two different creation dates and asked whether to treat the older ones as old SKUs to delete.

## Answer

Always export the listing data of every SKU you plan to delete before deleting it. A reverse feed or Category Listings Report lets you restore attributes if the wrong SKU goes. Count the rows in the backup against the delete list first.

## Cause

Deleting a SKU removes its offer and listing data from the account. Without an export taken first there is no way to restore the content if the wrong SKU is deleted.

## Fix

1. Agree with the operator which SKUs are old; the thread confirmed different creation dates as the signal but did not explain the rule.
2. Download a reverse feed (Category Listings Report or the listing data for those SKUs) before any delete.
3. Store the file with the run so it can be re-uploaded if needed.
4. Delete the old SKUs only after the operator approves the list.

## Verify

The backup file holds a row for every SKU on the delete list before the deletion runs.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-download-category-listings-report.md`
- Also in: `MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The delete-relist SOP already requires a Category Listings Report backup before deleting a listing; this card extends that backup rule to retiring old or duplicate SKUs.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-file-uploads-delete-relist.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `MAG SOPs/catalog/catalog-sop-download-category-listings-report.md`, `MAG SOPs/catalog/catalog-sop-full-update-flat-file.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`).
