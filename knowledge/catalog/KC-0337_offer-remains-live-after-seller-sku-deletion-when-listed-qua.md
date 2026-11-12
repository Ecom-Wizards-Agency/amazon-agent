---
id: KC-0337
title: "Offer remains live after seller SKU deletion when listed quantity was not zeroed"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Help > Stop selling a product > Delete product and listing"
surface_verified: true
symptom_keywords: ["deleted SKU still buyable", "offer remains live after deletion", "All-Offers Display", "zero quantity before delete"]
error_text: []
asked_as: ["Why can an offer remain live after its seller SKU is deleted?"]
synonyms: []
resolution_status: diagnosis-only
fix_source: first-party-doc
evidence_location: run-note
confidence: high
verification: verified
verified_on: "2026-11-08"
verified_how: first-party-capture
amazon_sources: []
related_sops: []
supersedes: []
contradicts: [knowledge/catalog/KC-0227_before-deleting-old-or-duplicate-skus-download-a-reverse-fee.md]
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0337"
---

## Question

Why can an offer remain live after its seller SKU is deleted?

## Answer

For a merchant-fulfilled offer being retired, apply a listed quantity of zero before deleting the seller SKU, then verify that the offer is no longer buyable. Physical FBA stock requires its separate inventory or removal workflow.

## Cause

Amazon treats seller SKU deletion and inventory quantity deletion as separate operations. If the listed quantity is not zeroed, the offer can remain live on the All-Offers Display.

## Fix

1. Confirm the exact account, marketplace, seller SKU, and merchant-fulfilled channel. Back up the listing data before deletion.
2. Obtain approval for the exact quantity change and deletion. In the single-listing UI, save quantity zero before selecting Delete Product and Listing. For a supported bulk inventory-file delete, include quantity zero and Delete for each target SKU.
3. Reconcile every target SKU against the processing results and verify that the seller listing is deleted and its offer is no longer buyable.

## Verify

Check the quantity change and deletion per target SKU, including bulk processing results when applicable. Confirm the offer is absent or unavailable on the All-Offers Display; disappearance from Manage All Inventory alone does not prove offer removal.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: [Stop selling a product](https://sellercentral.amazon.com/help/hub/reference/G200216110), section Delete product and listing, read live on 08.11.2026.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the quantity-zero precondition for retiring a merchant-fulfilled offer. The related backup unit states that SKU deletion removes the offer without this qualification; the current first-party rule takes precedence.
- Existing coverage: partial (`knowledge/catalog/KC-0227_before-deleting-old-or-duplicate-skus-download-a-reverse-fee.md`).
- This diagnosis verifies the documented precondition, not a live deletion result or propagation time.
