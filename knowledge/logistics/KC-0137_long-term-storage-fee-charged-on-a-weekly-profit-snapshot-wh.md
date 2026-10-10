---
id: KC-0137
title: "Long-term storage fee charged on a weekly profit snapshot: why, and what stops it"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > Reports > Fulfillment > Payments (Aged Inventory Surcharge / long-term storage fee reports)"
surface_verified: false
symptom_keywords: ["long term storage fee charged", "aged inventory surcharge", "storage fee ate profit", "slow moving FBA stock fee", "how to avoid long term storage fees"]
error_text: []
asked_as: ["A brand owner saw a long-term storage fee wipe out a week's profit and asked whether anything could be done to avoid it, and whether it came from slow sales of older products."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0137"
---

## Question

A brand owner saw a long-term storage fee wipe out a week's profit and asked whether anything could be done to avoid it, and whether it came from slow sales of older products.

## Answer

A long-term storage charge means some FBA units have aged past Amazon's storage-age thresholds without selling. Pull the Aged Inventory Surcharge report to see which SKUs and age bands caused it, then clear those units through price, promotion, removal or disposal and cut their replenishment. Read the current age thresholds on Amazon's fee page rather than relying on a remembered window.

## Cause

The agency attributed the charge to units that sat in fulfillment centers without selling enough. The local FBA fees capture confirms that a long-term storage fee is assessed in addition to monthly storage fees but gives no age thresholds; the thread's 90-day window was not checked against a first-party page.

## Fix

1. Download the Aged Inventory Surcharge report (Reports > Fulfillment > Payments) and the Long-Term Storage Fee Charges report to itemise the charge by SKU and inventory age.
2. List the SKUs carrying the charge and their age bands and sell-through.
3. For each aged SKU decide between a price or promotion push, a removal order or a disposal; a removal or disposal order needs operator approval.
4. Lower future replenishment for the slow SKUs so new units do not age into the next band.
5. Check the report again after the next monthly assessment.

## Verify

The next aged inventory or long-term storage assessment shows the charge removed or reduced for the treated SKUs.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links a long-term storage charge to its diagnosis path (Aged Inventory Surcharge report, per-SKU clearance, lower replenishment) and notes that the thread's 90-day explanation was not checked against the published thresholds; existing SOPs only cover pulling the reports.
- Existing coverage: full (`Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`).
