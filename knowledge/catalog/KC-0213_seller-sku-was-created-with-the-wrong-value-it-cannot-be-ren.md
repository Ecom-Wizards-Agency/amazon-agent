---
id: KC-0213
title: "Seller SKU was created with the wrong value: it cannot be renamed, so create a new SKU on the same ASIN"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [DE]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["change seller SKU", "rename SKU Seller Central", "wrong SKU EAN instead of MPN", "edit SKU name"]
error_text: []
asked_as: ["While building an FBA shipment, the client found early SKUs had been created with the EAN as SKU, while its warehouse invoices use the MPN, and asked whether the SKU could be changed."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0213"
---

## Question

While building an FBA shipment, the client found early SKUs had been created with the EAN as SKU, while its warehouse invoices use the MPN, and asked whether the SKU could be changed.

## Answer

You cannot rename a seller SKU in normal Seller Central. Create a new SKU on the same ASIN with the value your warehouse uses, map old to new, and retire the old SKU once it holds no stock. Settle the SKU convention before the first shipment.

## Cause

A seller SKU cannot be changed once the listing is created (stated by the agency and by the MAG SOP on creating multiple offers). The agency said only premium seller support might change it; that was not verified. A new SKU can be created on the same ASIN instead.

## Fix

1. Ask the client for a mapping of old SKU to correct new SKU.
2. Create each new SKU as an offer on the existing ASIN (operator approval required).
3. Use the new SKUs in shipments; retire the old SKUs only once they hold no inventory or open shipments (approval required for deletion).

## Verify

The new SKUs appear under the same ASIN in Manage All Inventory and can be added to Send to Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: States that a seller SKU cannot be renamed and gives the new-SKU-on-same-ASIN workaround; no captured page covers it.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-editing-a-lightning-deal-in-seller-central.md`, `sop-drafts/2026-05-25_seller-support-case-troubleshooting-and-escalation.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-errors-in-the-vine-program-on-seller-central.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`).
