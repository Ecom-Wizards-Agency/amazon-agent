---
id: KC-0184
title: "Does a 3PL shipping merchant-fulfilled orders need to put Amazon stickers or labels on the product?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [all]
marketplace_inferred: true
surface: "Merchant-fulfilled (FBM) order fulfillment through a 3PL"
surface_verified: false
symptom_keywords: ["FBM 3PL stickers on product", "do I need FNSKU labels for FBM", "3PL labels merchant fulfilled", "product label before shipping to customer FBM"]
error_text: []
asked_as: ["The brand owner was moving order fulfillment to a 3PL and asked whether the 3PL had to stick anything on the product before shipping it to the customer."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md"]
supersedes: []
contradicts: []
observed: 2025-10
review_by: 2027-10
provenance: "ledger:KC-0184"
---

## Question

The brand owner was moving order fulfillment to a 3PL and asked whether the 3PL had to stick anything on the product before shipping it to the customer.

## Answer

Do not add Amazon product stickers when a 3PL ships merchant-fulfilled orders to customers. Amazon's labeling requirements cover inventory sent into Amazon fulfillment centers, so they apply only when the same product goes into FBA.

## Cause

Amazon's product labeling requirements (FNSKU or barcode labels) apply to inventory shipped into Amazon fulfillment centers. Merchant-fulfilled orders ship straight from the seller's or 3PL's warehouse to the customer, so no Amazon product label is needed.

## Fix

1. Confirm the offer is merchant-fulfilled, not FBA.
2. Tell the 3PL that no Amazon product label (FNSKU sticker) is needed on merchant-fulfilled orders; it ships the parcel with its carrier shipping label.
3. If the same SKU is later sent into FBA, apply the FBA labeling requirements to that inbound inventory.

## Verify

Orders ship and are delivered without labeling complaints; the FBA labeling requirements page lists labeling only for inventory shipped to Amazon fulfillment centers.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit states that merchant-fulfilled orders shipped by a 3PL need no Amazon product labels; the FBA page only implies it.
- Existing coverage: partial (`knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-customer-service-buyer-messages-refund-and-replacement.md`).
