---
id: KC-0238
title: "Unknown non-buyable \"-Parent\" SKU in inventory: it is the variation parent and should not be deleted"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory / SKU Central"
surface_verified: false
symptom_keywords: ["what is the parent SKU", "can I delete parent SKU", "non-buyable SKU in inventory", "parent ASIN no price", "delete variation parent"]
error_text: []
asked_as: ["A client saw a SKU ending in \"-Parent\" in inventory and asked whether it could be deleted."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md", "MAG SOPs/catalog/catalog-sop-parentage-creation.md"]
supersedes: []
contradicts: []
observed: 2025-11
review_by: 2027-10
provenance: "ledger:KC-0238"
---

## Question

A client saw a SKU ending in "-Parent" in inventory and asked whether it could be deleted.

## Answer

A SKU with no price or stock that ends in "-Parent" is usually the variation parent that ties the child listings together. Keep it while the family should stay together: deleting the parent listing breaks the parentage and the children become separate listings. Delete it only when you mean to dissolve the family, and follow the break-parentage procedure when you do.

## Cause

The SKU is the parent of a variation family; the agency's parent SKU convention adds 'PARENT' to the SKU. The parent holds no stock and is not buyable, but it groups the child listings on one detail page. Deleting the parent listing breaks the whole parentage and the children become individual listings.

## Fix

1. Open the SKU in SKU Central or Manage All Inventory and confirm it is a parent (no price or stock, children listed under it).
2. Keep the parent SKU while the family should stay together.
3. Delete the parent only to dissolve the family on purpose, following the break-parentage procedure (deleting the parent listing is one of its methods; a re-created parent gets a new ASIN).

## Verify

The children still show as one variation family on the live detail page.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`
- Also in: `MAG SOPs/catalog/catalog-sop-parentage-creation.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The parentage SOPs cover creating and breaking families, but none answers a client asking whether an unfamiliar non-buyable parent SKU can be deleted.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`, `MAG SOPs/catalog/catalog-sop-how-to-break-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-parentage-creation.md`, `MAG SOPs/catalog/catalog-sop-how-to-remove-a-listing-from-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-breaking-a-phantom-parentage.md`).
