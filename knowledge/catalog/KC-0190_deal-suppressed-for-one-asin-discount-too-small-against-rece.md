---
id: KC-0190
title: "Deal suppressed for one ASIN: discount too small against recent price history"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Advertising > Deals"
surface_verified: false
symptom_keywords: ["deal suppressed", "ASIN suppressed from deal", "deal price not low enough", "minimum discount not met", "Prime Day deal ineligible"]
error_text: []
asked_as: ["Ahead of a major deal event, an external deals contact warned that the single-unit ASIN was flagged and suppressed from its deal, while the multipack ASIN in the same deal was fine."]
synonyms: []
resolution_status: resolved
fix_source: amazon-support
evidence_location: email
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md", "MAG SOPs/catalog/catalog-sop-managing-suppressed-lightning-deals.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0190"
---

## Question

Ahead of a major deal event, an external deals contact warned that the single-unit ASIN was flagged and suppressed from its deal, while the multipack ASIN in the same deal was fine. The single unit had a single-digit percent discount.

## Answer

When one ASIN in a deal is suppressed while the others pass, compare its deal price with its own price history and reference price. The current US peak playbook requires event deals to sit at or below the lowest sales price of the past 60 days, at least 5% under the lowest of the past 30 days, and at the deal type's minimum discount off the reference price. Lower the deal price to clear all three, confirm the live thresholds for your marketplace and event, and re-check every deal price shortly before the event.

## Cause

Amazon checks the deal price against the ASIN's recent pricing history and a minimum discount off the reference price. The current US peak readiness playbook lists the event-deal requirements: at or below the lowest sales price of the past 60 days, at least 5% off the lowest sales price of the past 30 days, and a minimum 15% (Best Deal, Prime Exclusive Discount) or 20% (Lightning Deal) off the reference price. The message relayed in the thread cited the 60-day history check and a minimum discount, and the single-unit deal price did not clear them.

## Fix

1. Open the deal and read the suppression or eligibility reason for each ASIN.
2. Find the lowest sales price of the past 60 and 30 days and the deal type's minimum discount off the reference price.
3. Lower the deal price to the highest price that meets all checks (requires approval of the price change).
4. Re-check deal prices again shortly before the event, because a recent lower price moves the threshold.

## Verify

The ASIN no longer shows as suppressed in the deal and its status returns to approved or scheduled.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/090-price-discounts-G7F8CQ4EJ5YA4272.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`
- Also in: `MAG SOPs/catalog/catalog-sop-managing-suppressed-lightning-deals.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties a deal suppression on one ASIN of a deal to the 60-day and 30-day price-history checks and adds a pre-event re-check; the MAG suppressed-deals SOP and peak playbook already state most of the rule.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-managing-suppressed-lightning-deals.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/catalog/catalog-sop-how-to-create-deals-lightning-and-best.md`, `MAG SOPs/README.md`).
