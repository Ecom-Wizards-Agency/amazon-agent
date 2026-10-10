---
id: KC-0016
title: "FBM late shipment rate jumps above target although packages left the warehouse on time"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Shipping Performance; Orders > Manage Orders"
surface_verified: false
symptom_keywords: ["late shipment rate above 4%", "FBM late shipment rate spike", "orders shipped on time but marked late", "shipment confirmation not sent to Amazon", "automatic ship confirmation failed"]
error_text: []
asked_as: ["The account showed a seller-fulfilled late shipment rate far above the 4% target, putting account health and the ability to keep FBM offers at risk."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/115-amazon-business-metrics-G202141920.md", "Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0016"
---

## Question

The account showed a seller-fulfilled late shipment rate far above the 4% target, putting account health and the ability to keep FBM offers at risk. The account manager asked the brand's fulfillment owner to fix it urgently.

## Answer

When the FBM late shipment rate spikes but the warehouse says it shipped on time, check the ship confirmations, not the trucks. Amazon counts an order as late when the ship confirmation reaches Seller Central after the expected ship date, so a broken 3PL or software confirmation feed makes on-time shipments look late. Confirm the stuck orders manually, have the feed repaired, and watch the rate recover over the rolling window.

## Cause

The packages left the merchant-fulfilled warehouse on time, but the automated shipment confirmation from the warehouse system to Seller Central failed, so the orders were not confirmed as shipped until after the expected ship date. Late shipment rate counts orders whose ship confirmation is completed after the expected ship date, not the physical dispatch date.

## Fix

1. In Orders > Manage Orders, filter seller-fulfilled orders past their ship-by date that are still unshipped and compare them with the warehouse's dispatch log.
2. Confirm shipment (with carrier and tracking) for any order that physically left but is not confirmed in Seller Central.
3. Ask the warehouse or 3PL to repair the automatic shipment confirmation integration and confirm it posts tracking for new orders.
4. Monitor Account Health > Shipping Performance until the rolling late shipment rate falls back under 4%.

## Verify

New seller-fulfilled orders show as Shipped with tracking before their ship-by date, and the late shipment rate in Account Health trends back below the 4% target over the rolling window.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/115-amazon-business-metrics-G202141920.md`
- First-party: `Amazon Seller Help/articles/092-subscribe-and-save-for-sellers-G201620110.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the diagnosis that a broken warehouse/3PL ship-confirmation feed makes on-time FBM shipments count as late; the SOP only covers checking late orders.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`).
