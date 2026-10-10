---
id: KC-0189
title: "FBA inventory report shows far fewer units than were shipped and the units are marked stickerless"
kind: reference
topic: logistics
status: reviewed
skills: [amazon-fba-inventory-planning, amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory; Reports > Restock Inventory"
surface_verified: true
symptom_keywords: ["stock report shows fewer units than shipped", "what does stickerless mean", "where to see stock per SKU daily", "inbound units not in available", "restock report inbound transfer"]
error_text: []
asked_as: ["A client heard a large FBA shipment had arrived and selling had resumed, but the stock report showed only a small number of available units for the SKU, marked stickerless."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-restock-report-stand-alone.md", "MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0189"
---

## Question

A client heard a large FBA shipment had arrived and selling had resumed, but the stock report showed only a small number of available units for the SKU, marked stickerless. They asked whether the shipment was received and where to pull daily stock per SKU.

## Answer

The available column in FBA inventory reports counts only received, sellable units, so a shipment still being received or moved between fulfillment centers looks like missing stock. Use the Manage All Inventory breakdown and the Restock Inventory report to see available, inbound and transfer quantities per SKU. A stickerless label only means the units use the manufacturer barcode instead of an Amazon FNSKU.

## Cause

Not all of the shipment had been received yet. The available column counts only received, sellable units, so units still inbound or moving between fulfillment centers do not show there. "Stickerless" refers to units tracked by their manufacturer barcode (such as a UPC) instead of an Amazon barcode label. It is a tracking setting on the same SKU, not a separate stock.

## Fix

1. Open Manage All Inventory and check the SKU inventory breakdown (available, inbound, reserved or in transfer).
2. For per-SKU stock including what has arrived and what is moving between fulfillment centers, download the Restock Inventory report (Reports > Restock Inventory).
3. Treat a "stickerless" flag as the manufacturer barcode tracking setting, not as a separate stock.
4. Check the shipment status in the shipping queue to see how much of the shipment is still being received.

## Verify

The shipment in the shipping queue shows received units matching the units sent. The Manage All Inventory breakdown or the Restock Inventory report accounts for those units as available, reserved, inbound or in transfer, after subtracting units sold since selling resumed.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-restock-report-stand-alone.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The local library has the Restock report SOP but no unit tying a low available count to inbound or transfer units and explaining that stickerless means manufacturer-barcode tracking.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `Amazon Seller Help/articles/146-custom-report-builder-GEQ8JEWH5KJC5QCG.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`).
