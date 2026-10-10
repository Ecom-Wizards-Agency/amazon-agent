---
id: KC-0201
title: "Parent title wrong or broken: separate the children, delete the parent and re-import a new parent under a new parent SKU"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Catalog > Add Products via Upload (flat file); Manage All Inventory"
surface_verified: false
symptom_keywords: ["change parent title variation", "rebuild parent ASIN", "delete parent and reparent", "new parent SKU wait 24 hours"]
error_text: []
asked_as: ["A client catalog manager wanted to confirm the steps to fix a parent listing: separate the children, delete the parent, then import a new parent with the children attached."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/144-product-variations-GF4VNS6ZQQPYYGGP.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md", "MAG SOPs/catalog/catalog-sop-parentage-creation.md", "MAG SOPs/catalog/catalog-sop-how-to-remove-a-listing-from-a-parentage.md"]
supersedes: []
contradicts: []
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0201"
---

## Question

A client catalog manager wanted to confirm the steps to fix a parent listing: separate the children, delete the parent, then import a new parent with the children attached.

## Answer

To replace a variation parent, break the family, delete the old parent with a flat file and import a new parent with the children attached. A deleted parent ASIN cannot be reused, so check the new title before uploading. The agency's advice was to give the new parent a different SKU so the re-import can run within an hour or two instead of waiting about a day for the old SKU. The thread did not confirm that timing, and no Amazon page states it.

## Cause

The thread does not say why the parent title could not be edited in place; the team chose to rebuild the parent. The client suspected that a later display problem came from a wrong browse node, and this was not confirmed.

## Fix

1. ["1. Remove the children from the parent (clear parentage on the child rows); deleting the parent also breaks the family, per the break-parentage MAG SOP.", "2. Delete the old parent with a flat file using update_delete = Delete on the parent SKU (operator approval needed).", "3. Import a new parent with a different parent SKU and the corrected title, and attach the children in the same file; check the title before upload because the deleted parent ASIN cannot be reused.", "4. If a display problem remains after the rebuild, check the browse node on the parent and children."]

## Verify

The new parent ASIN shows all children in the variation selector with the corrected title, and the old parent SKU no longer appears in Manage All Inventory.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/144-product-variations-GF4VNS6ZQQPYYGGP.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`
- Also in: `MAG SOPs/catalog/catalog-sop-parentage-creation.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-remove-a-listing-from-a-parentage.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds that using a new parent SKU lets the rebuilt parent be imported within an hour or two instead of waiting for the old SKU to clear.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-breaking-a-phantom-parentage.md`).
