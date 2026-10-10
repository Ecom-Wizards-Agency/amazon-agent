---
id: KC-0144
title: "3PL says it can make carrier labels but not Amazon box labels for an FBA shipment"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon (box labels and Amazon partnered carrier labels)"
surface_verified: false
symptom_keywords: ["3PL will not create Amazon labels", "FBA box labels from 3PL", "partnered carrier labels 3PL shipment", "UPC or FNSKU on units", "ship before Transparency is active", "shipment labels need to be redone"]
error_text: []
asked_as: ["The seller's 3PL warehouse was asked to forward FBA cartons with UPS."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0144"
---

## Question

The seller's 3PL warehouse was asked to forward FBA cartons with UPS. Its stock count turned out lower than the shipment plan, so the labels had to be redone, and the 3PL said it only creates carrier shipping labels, not the Amazon labels, and asked which barcode the units need and whether Transparency stickers were required.

## Answer

When a 3PL forwards stock to FBA, build the Send to Amazon shipment yourself from the 3PL's confirmed on-hand count and carton dimensions, because the 3PL can create carrier labels but not Amazon box labels. Print partnered-carrier labels so each page carries one box's carrier label and FBA box label, and confirm every unit carries the barcode the listing expects. If the product is enrolled in Transparency, check whether it is active before shipping, since active Transparency units without a code are put aside.

## Cause

The 3PL's role ends at carrier labels: Amazon FBA box labels and Amazon partnered carrier labels come from the Send to Amazon workflow in the seller's account, so the seller or agency must build the shipment from the 3PL's real on-hand count and carton dimensions and weights. The first label set was built before the 3PL count was confirmed. The barcode the 3PL called a UPC was the FNSKU label already used on an earlier shipment.

## Fix

1. Get the 3PL's actual on-hand units and the master-carton dimensions and weight before creating anything.
2. Create the Send to Amazon shipment from those numbers (operator approval required to confirm the shipment), keeping any reserve units out of the plan.
3. Choose the Amazon partnered carrier and print the labels so each PDF page belongs to one numbered box and holds both the carrier label and the Amazon FBA box label.
4. Send the 3PL the PDFs per destination fulfillment center with a short sheet: shipment ID, boxes x units per box, total units; tell them to apply both labels from each page to the matching box and hand the boxes to the carrier.
5. Confirm every unit carries the scannable barcode Amazon expects for the SKU (the FNSKU label when the listing uses Amazon barcodes; a 3PL may call it a UPC).
6. If the product is enrolled in Transparency, check its activation status before shipping: once active, every unit needs a unique Transparency code or it is put aside. The source shipped urgent units before activation, but how Amazon treats uncoded units still inbound or in stock when activation goes live was not established; confirm with Transparency support first.
7. After delivery, compare received versus shipped per shipment ID and open the shipment's problem tab before assuming check-in is still running.

## Verify

Shipment status moves to Delivered and then Receiving/Closed, with received units matching shipped units per shipment ID, and no labeling problems in the shipment's problem tab.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The Send to Amazon SOP covers creating the shipment, but none of the matched pages says the 3PL cannot produce Amazon box labels, that labels must be built from the 3PL's confirmed count and carton data, or that urgent units should ship before Transparency activation.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
