---
id: KC-0120
title: "New product packaging before an FBA shipment: if the printed barcode number matches the listing's manufacturer barcode, the new pack ships without relabelling"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Send to Amazon; offer barcode type (manufacturer barcode)"
surface_verified: false
symptom_keywords: ["rebrand packaging FBA", "new packaging same UPC", "do we need to relabel new packaging", "old and new pack same EAN", "packaging change before shipment"]
error_text: []
asked_as: ["The client held the same product in old and redesigned packaging at its 3PL and asked whether anything had to be done before sending the redesigned pack to FBA ahead of a peak event."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md"]
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0120"
---

## Question

The client held the same product in old and redesigned packaging at its 3PL and asked whether anything had to be done before sending the redesigned pack to FBA ahead of a peak event.

## Answer

Before sending redesigned packaging to FBA, compare its printed barcode number with the manufacturer barcode the offer is tracked under. If they match and the offer is still eligible for manufacturer-barcode tracking (eligibility changed in March 2026, so check the offer before shipping), the fulfillment center scans the new pack as the same product and no relabelling is needed. Prefer the pack with the printed barcode over one that needs labels at the 3PL, and update the listing images to the new packaging.

## Cause

The FBA offer tracks units by the manufacturer barcode (EAN). The redesigned pack prints the same barcode number, so the fulfillment center receives it as the same product; the old pack needed labels added at the 3PL, which cost extra.

## Fix

1. ["1. Get the packaging artwork or photos of both packs and read the barcode number on each.", "2. Compare the numbers with the barcode the FBA offer is tracked under, and confirm the offer is still set to and eligible for manufacturer barcode tracking.", "3. If the numbers match, ship the new pack as is and prefer it over a pack that needs labels at the 3PL.", "4. If they differ, the thread does not cover the fix; resolve it before shipping.", "5. Update listing images to the new packaging if not done yet."]

## Verify

The team confirmed the barcode on the new pack matched the manufacturer barcode on the offer and approved the shipment.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-switch-from-amazon-barcodes-to-manufacturer-barcodes-for-virtual-tracking.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The barcode SOPs explain manufacturer barcodes but not the check that redesigned packaging ships without relabelling when its barcode number matches the offer.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `sop-drafts/2026-08-03_new-client-fba-disposal-prevention-gate.md`).
