---
id: KC-0328
title: "FBA box label expiry is one day earlier than the date entered in Send to Amazon"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Confirmed inventory and Print box labels"
surface_verified: true
symptom_keywords: ["expiration date one day earlier", "box label expiry mismatch", "UTC timezone conversion"]
error_text: []
asked_as: ["Why does the FBA box label show the previous day when the confirmed shipment expiry is correct?"]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: run-note
confidence: medium
verification: verified
verified_on: 2026-10-23
verified_how: live-ui
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0328"
---

## Question

Why does the FBA box label show the previous day when the confirmed shipment expiry is correct?

## Answer

Compare the confirmed Send to Amazon expiry with the physical product date before changing anything. Amazon documents that a box-label date can differ due to UTC time-zone conversion and uses the date entered in Send to Amazon as the expiry of record. Preserve correct shipment and manufacturer dates and retain evidence of the display difference.

## Cause

Amazon stores expiry information in UTC and explicitly warns that time-zone conversion can change the date displayed on the box label.

## Fix

1. Read the confirmed SKU expiration date in the existing workflow.
2. Compare the generated box-label date and the manufacturer expiry.
3. Read the current US help article Expiration dates on FBA products, especially Important and Shipment Creation Requirements.
4. When the entered date is correct and the difference matches the documented time-zone behavior, preserve the expiry of record and original label content and note the display difference for the warehouse.

## Verify

Confirm the SKU date in Send to Amazon matches the physical batch date, inspect the original PDF, and retain the live Amazon help text explaining UTC conversion and the expiry of record.

## Stop before

Do not offset a correct entered expiry merely to make the box-label display match. Stop before changing shipment data, editing barcode content, cancelling or recreating shipments, or sending a support case unless the operator approved that exact action.

## Sources

- First-party: [Expiration dates on FBA products](https://sellercentral.amazon.com/help/hub/reference/G201003420), Important and Shipment Creation Requirements, read in the attended US Seller Central session. No local library capture yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

Only the US workflow and current US guidance were verified. Other marketplaces and differences beyond the documented time-zone conversion need their own check. The unit remains draft pending human review.
