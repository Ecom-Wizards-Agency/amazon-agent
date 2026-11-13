---
id: KC-0335
title: "Expiration-dated inventory is said to require Amazon barcodes despite Brand Registry eligibility"
kind: decision-aid
topic: logistics
status: draft
skills: [amazon-logistics, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Step 1 > SKU row barcode type and expiration date"
surface_verified: false
symptom_keywords: ["expiration dated manufacturer barcode", "expiry requires FNSKU", "Brand Registry barcode eligibility", "FNSKU equals ASIN"]
error_text: []
asked_as: ["Does having an expiration date mean our inventory cannot use a manufacturer barcode?"]
synonyms: ["expiry dated", "stickerless inventory", "Amazon barcode", "manufacturer barcode"]
resolution_status: diagnosis-only
fix_source: first-party-doc
evidence_location: run-note
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0335"
---

## Question

Does an expiration date automatically make an offer ineligible for manufacturer barcodes, even when the seller represents the registered brand?

## Answer

Do not infer a blanket manufacturer-barcode prohibition from an expiration date. Current US guidance allows manufacturer barcodes when the product is new, has one scannable product identifier matching one ASIN, and is linked to a Brand Registry brand for which the seller is a brand representative. Check the exact offer's barcode type and current eligibility in Send to Amazon before deciding whether it needs an Amazon barcode. Expiry labeling remains a separate requirement.

## Cause

Older expiry guidance and general barcode advice can omit the current brand eligibility rules. An account's default barcode preference, or a displayed FNSKU that matches its ASIN, does not prove that a particular offer is currently accepted with a manufacturer barcode.

## Fix

1. Verify the seller, US marketplace, exact offer and SKU before reading its Send to Amazon row.
2. Read the current Barcode type and any eligibility notice for that offer. A row requiring an expiration date can also show Manufacturer barcode; evaluate both fields independently.
3. If Amazon refuses manufacturer barcodes, capture the exact notice and confirm product-to-brand registration and the seller's Brand Representative selling role. Do not assume that brand enrollment automatically links every product.
4. Separately check expiry attributes and visible expiry labels on the finished saleable packaging. Do not change the expiry classification to bypass a barcode restriction.

## Verify

The exact intended SKU's shipment row shows its barcode type and relevant expiry requirement under the verified account and marketplace. Record any rejection separately. A public product page, an ASIN-shaped FNSKU, or another offer's successful shipment is insufficient proof for this SKU.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: [Use manufacturer barcodes for FBA](https://sellercentral.amazon.com/help/hub/reference/external/200141480/G202061550), web research in 2026-11; no matching local capture yet.
- First-party: [FBA barcode requirements](https://sellercentral.amazon.com/help/hub/reference/external/G201100910), web research in 2026-11.
- First-party: [Expiration dates on FBA products](https://sellercentral.amazon.com/help/hub/reference/external/G201003420), separate expiry and packaging requirements.
- Also in: `skills/amazon-logistics/SKILL.md` and `skills/amazon-troubleshooting/SKILL.md`.
- Evidence: team vault ledger row for this id.

## Gaps

Web research only in this unit; no live browser verification or matching first-party capture has been incorporated. A shipment row's displayed barcode type does not prove that an unsent shipment would pass every later validation. Other marketplaces and inactive offers need their own checks. Human review is pending.
