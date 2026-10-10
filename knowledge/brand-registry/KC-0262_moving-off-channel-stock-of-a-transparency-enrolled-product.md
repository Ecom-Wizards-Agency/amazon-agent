---
id: KC-0262
title: "Moving off-channel stock of a Transparency-enrolled product into FBA or FBM: does every unit need a Transparency code?"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-logistics, amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["Transparency codes for FBA shipment", "off-channel stock to FBA", "FBM Transparency upload codes", "need Transparency code on each unit", "send unsold stock to Amazon"]
error_text: []
asked_as: ["The brand wanted to move stock it could not sell on another channel into FBA, plus colours not yet listed on Amazon."]
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
contradicts: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0262"
---

## Question

The brand wanted to move stock it could not sell on another channel into FBA, plus colours not yet listed on Amazon. The team asked whether codes had to be applied first.

## Answer

Treat any stock of a Transparency-enrolled product as unsellable on Amazon until each unit carries a valid code, including stock produced for another channel. Apply the codes at a prep location before sending to FBA, and keep variants without a listing out of the shipment. Check the Transparency help pages before relying on code upload without physical labels for seller-fulfilled orders.

## Cause

The product is enrolled in Transparency, and Amazon does not sell enrolled products without a valid Transparency code, whether fulfilled by Amazon or shipped by the seller. Stock made for another channel had no codes. Variants without an Amazon listing cannot be sent until a listing exists.

## Fix

1. Send the stock to a prep location and apply a Transparency code to every unit before creating an FBA shipment.
2. Keep unlisted variants in storage until their listings are created.
3. Selling seller-fulfilled does not remove the requirement: the help page says enrolled products cannot be sold without a valid code whether fulfilled by Amazon or shipped by the seller, and every unit is labelled. The thread's claim that seller-fulfilled codes only need to be uploaded, not applied, conflicts with that page (see contradicts_paths) and should not be relied on.
4. Create any shipment only after operator approval.

## Verify

FBA receiving shows no Transparency-related stranded or unfulfillable units; for seller-fulfilled orders, shipment confirmation accepts the provided codes.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Off-channel stock of a Transparency-enrolled product needs codes on every unit before FBA, with a disputed FBM upload-only claim.
- Existing coverage: full (`MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`, `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-shipment.md`).
