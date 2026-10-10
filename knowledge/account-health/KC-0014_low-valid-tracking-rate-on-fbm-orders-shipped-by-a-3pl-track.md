---
id: KC-0014
title: "Low valid tracking rate on FBM orders shipped by a 3PL: tracking uses the 3PL as carrier"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["low VTR", "valid tracking rate low 3PL", "invalid tracking FBM", "carrier not recognized", "3PL tracking number not valid"]
error_text: []
asked_as: ["The valid tracking rate stayed low although the 3PL had shipped the merchant-fulfilled orders; the team asked whether to fix it manually."]
synonyms: []
resolution_status: partial
fix_source: client
evidence_location: email
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0014"
---

## Question

The valid tracking rate stayed low although the 3PL had shipped the merchant-fulfilled orders; the team asked whether to fix it manually.

## Answer

When the valid tracking rate drops on 3PL-shipped orders, check whether the 3PL confirmed them with its own tracking IDs instead of the last-mile carrier. Amazon does not recognise a 3PL as a carrier, so those orders count as invalid. Update the affected orders with the real carrier and tracking, and fix the 3PL integration so it confirms with recognised carriers only.

## Cause

The 3PL confirmed orders with its own internal tracking numbers and named itself as carrier. Amazon does not recognise the 3PL as a carrier, so those tracking IDs counted as invalid.

## Fix

1. Pull the merchant-fulfilled orders behind the low valid tracking rate and check the carrier and tracking number on each.
2. Ask the 3PL for the real last-mile carrier and tracking number for every order confirmed with its internal tracking ID.
3. Update the tracking on those orders in Seller Central (Manage Orders > Edit shipment) with the actual carrier.
4. Have the 3PL change its Amazon integration so it confirms shipments only with Amazon-recognised carriers.
5. If the rate needs review, contact the account manager or Seller Support with the corrected list (approval required before sending).

## Verify

New merchant-fulfilled orders show a recognised carrier and tracking ID, and the valid tracking rate recovers in Account Health.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: A low valid tracking rate can come from a 3PL confirming orders with its own tracking IDs instead of the last-mile carrier.
- Existing coverage: none (`knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
