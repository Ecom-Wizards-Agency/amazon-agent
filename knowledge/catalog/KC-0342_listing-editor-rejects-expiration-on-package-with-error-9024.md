---
id: KC-0342
title: "Listing editor rejects Expiration On Package with error 90244"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Manage All Inventory > Edit listing > Product Details"
surface_verified: true
symptom_keywords: ["expiration type invalid", "legacy expiration value rejected", "Product Expiration Type error"]
error_text: ["90244", "We can't accept the Expiration On Package you entered for Product Expiration Type."]
asked_as: ["Why does the listing editor reject Expiration On Package, and which current value can clear the validation error?"]
synonyms: ["product_expiration_type", "Expiration Date Required"]
resolution_status: partial
fix_source: agency
evidence_location: screenshot
confidence: low
verification: verified
verified_on: "2026-11-11"
verified_how: "live-ui"
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0342"
---

## Question

Why does an existing listing show error 90244 for Product Expiration Type even though its saved value is Expiration On Package?

## Answer

The current editor can reject a saved expiration-type value that is no longer an approved category choice. In one US check, selecting Expiration Date Required instead of Expiration On Package cleared the editor errors and enabled Submit Edits. Choose a current value that accurately describes the product; validation alone does not prove submission, listing activation or release of FBA inventory.

## Cause

Amazon's error identified the existing value as unacceptable and instructed the seller to select an approved category value. The check did not establish when the allowed values changed or whether this error caused every other listing restriction.

## Fix

1. Verify the account, marketplace and original listing. Open Product Details and capture the exact error and saved Product Expiration Type.
2. Inspect the current field choices. For a product that requires an expiration date, check whether Expiration Date Required is offered and matches the actual packaging and expiration requirements.
3. Stage only that field change and wait for validation. Check the editor's edit count and errors before preparing the exact submission for approval.
4. After an approved submission, read the processing result and reopen the listing to verify persistence. Check inventory and any separate restriction independently.

## Verify

The initial verified checkpoint was one staged edit, Product Expiration Type set to Expiration Date Required, no reported editor errors and Submit Edits available. After the operator saved the change, a fresh editor readback confirmed the value persisted with no edits pending. Later inventory and local-delivery retail checks showed the original offer Active and buyable. This sequence verifies recovery in that case; it does not prove that the expiration value was the only cause of the earlier restriction.

## Stop before

Stop before submitting listing edits or any appeal, case, refund, price change or inventory action unless the operator approved that exact action.

## Sources

- First-party: the Seller Central listing editor, unsaved validation, saved-field readback, inventory status and local-delivery retail availability, read live on 11.11.2026; no help-page capture yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

Only one US listing was checked. The save was performed by the operator, so the agent did not capture its submission receipt. Saved-field persistence and later offer recovery were independently read back; the contribution of separate policy reinstatement or processing delays remains uncertain. Other product types and marketplaces may offer different values. This check does not establish a universal replacement for Expiration On Package.
