---
id: KC-0224
title: "New listing variant stays blocked while its sibling variant goes live"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog]
marketplaces: [IT]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["new listing blocked", "one variant live other blocked", "real world images supplemental document", "listing blocked supplement", "packaging photos for Amazon review"]
error_text: []
asked_as: ["While creating a new two-size listing for a supplement product, the smaller size went live but the larger size stayed blocked."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md"]
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0224"
---

## Question

While creating a new two-size listing for a supplement product, the smaller size went live but the larger size stayed blocked. The client needed the ASIN and FNSKU for labels before the listing was available.

## Answer

When one variant of a new supplement listing goes live and another stays blocked, raise the blocked variant to Amazon and be ready to submit real-world packaging photos from every side, with the barcode visible, as a supplemental document. Confirm the photos show the exact blocked variant before submitting, because a supplier can send the wrong size. Ship and label the live variant while the blocked one is under review.

## Cause

Not stated by Amazon in the thread. The agency raised the blocked variant to Amazon and supplied real-world packaging photos as a supplemental document, after which both variants went live; the thread does not show which step cleared the block. A MAG SOP notes Amazon often asks for real-world packaging images in claim reviews, which fits but is not confirmed here.

## Fix

1. Collect the inputs a new listing needs before creating it: EAN per size, case pack details if shipping in master cartons, and the compliance fields (regulatory organization name, certification status, compliance certifications) or the official notification to the national health authority.
2. List the variants; send labels for any variant that goes live while another is blocked.
3. Raise the blocked variant to Amazon for activation (operator approval needed for the case).
4. Request real-world photos of the blocked variant's packaging from all sides (top, front, back, sides), preferably showing the EAN barcode, and submit them as a supplemental document.
5. Check the photos show the exact blocked variant before submitting; a supplier can send the wrong size.

## Verify

Both variants show as live in Manage All Inventory and become fully sellable once stock arrives.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Field procedure for a new supplement variant blocked while its sibling is live: real-world packaging photos from all sides as a supplemental document.
- Existing coverage: full (`sop-drafts/2026-06-07_daily-amazon-account-health-check.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-use-new-selection-opportunities-in-explore-brand-selection.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`).
