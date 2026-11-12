---
id: KC-0325
title: "Pack size names keep reverting to count-based labels after successful updates"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Manage All Inventory > Edit listing > Product Details"
surface_verified: true
symptom_keywords: ["size normalization", "pack names ignored", "count-based labels", "unit count number of items"]
error_text: []
asked_as: ["Why do submitted pack-size names keep displaying as count-based labels?"]
synonyms: []
resolution_status: diagnosis-only
fix_source: first-party-doc
evidence_location: run-note
confidence: medium
verification: verified
verified_on: "2026-11-08"
verified_how: live-ui
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-10
provenance: "ledger:KC-0325"
---

## Question

Why do submitted pack-size names keep displaying as count-based labels?

## Answer

For product types covered by Size normalization, Amazon derives the customer-facing size from designated catalog attributes. A freeform Size contribution does not override that display. Keep factual quantity data accurate and request a support review for a valid display exception.

## Cause

Quantity-based normalization can derive a per-container amount from total Unit Count divided by Number of Items, then display the pack quantity. Some product types also use Total Servings Per Container. Check the current FAQ row for the product type.

The current US FAQ explicitly lists `SKIN_SERUM` as deriving Size from Unit Count and Number of Items. A freeform month-supply name in Size does not override those normalized values.

## Fix

1. Open the current Size normalization FAQ and confirm the product type and its source attributes.
2. Verify the exact seller and marketplace, then inspect Unit Count, Unit Count Type, Number of Items and applicable serving fields in Product Details. Correct only inaccurate factual values under the catalog approval.
3. If factual inputs are already correct, preserve them and prepare a signed support request for any display or unit-price mismatch. A valid naming exception is subject to Amazon review.

## Verify

Compare the saved seller contribution with the live detail-page selector and price per unit at a verified local delivery postcode. Check current price divided by the total consumer units. An accepted feed, saved Size field or integrator reflection status does not by itself prove a correct storefront.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: [Size normalization FAQ](https://sellercentral.amazon.com/help/hub/reference/GZJRCRLWW7WKKDAH), read live on 08.11.2026, including the `SKIN_SERUM` row. No local library capture yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The naming mechanism is verified; propagation timing and exception availability are unverified.
