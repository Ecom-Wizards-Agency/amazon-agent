---
id: KC-0020
title: "Fragrance product cannot be sent to FBA because of its dangerous goods classification: upload a Safety Data Sheet instead of the exemption sheet"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-logistics, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > FBA compliance dashboard (Upload and track the status of your safety data sheets (SDS) and exemption sheets); Send to Amazon"
surface_verified: false
symptom_keywords: ["cannot send fragrance to FBA hazmat", "exemption sheet rejected perfume", "dangerous goods review blocks shipment", "upload SDS instead of exemption sheet", "change category to clear hazmat"]
error_text: []
asked_as: ["A fragrance product could not be added to an FBA shipment because of its dangerous goods review."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md", knowledge/compliance/KC-0001_fba-hazmat-review-blocks-a-battery-powered-kit-with-a-cosmet.md]
supersedes: []
contradicts: []
observed: 2025-04
review_by: 2027-10
provenance: "ledger:KC-0020"
---

## Question

A fragrance product could not be added to an FBA shipment because of its dangerous goods review. The team had considered moving the product to another category to get around it.

## Answer

If a fragrance, cosmetic or other chemical-containing product cannot be sent to FBA, check whether an exemption sheet was submitted instead of an SDS. Exemption sheets only work for battery products and products without harmful chemicals; anything else needs a complete Safety Data Sheet that matches the listing. Upload the SDS rather than recategorising the product to dodge the review.

## Cause

An exemption sheet had been submitted for the product, but exemption sheets are accepted only for battery products and products without harmful chemicals, so a fragrance needs a Safety Data Sheet. Once the SDS was uploaded instead, the product could be shipped without changing its category.

## Fix

1. Open Upload and track the status of your safety data sheets (SDS) and exemption sheets in the FBA compliance dashboard.
2. Check which document was submitted for the ASIN. If it is an exemption sheet and the product is not a battery product or a product without harmful chemicals, replace it.
3. Upload a Safety Data Sheet that has all 16 sections, is less than five years old and shows the same product and brand name as the detail page.
4. Do not change the product category to avoid the review; the agency lead fixed it without that.
5. Once the classification clears, create the shipment in Send to Amazon.

## Verify

The ASIN can be added to a Send to Amazon shipment without a dangerous goods block, and the compliance dashboard shows the SDS accepted.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`
- Also in: `knowledge/compliance/KC-0001_fba-hazmat-review-blocks-a-battery-powered-kit-with-a-cosmet.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SDS SOP already states the exemption-sheet limit; the card adds a confirmed case where swapping the exemption sheet for an SDS cleared a fragrance without recategorising.
- Existing coverage: full (`knowledge/compliance/KC-0001_fba-hazmat-review-blocks-a-battery-powered-kit-with-a-cosmet.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`).
