---
id: KC-0197
title: "Listing claim removals submitted by bulk file never went live, so flagged claims stayed in the catalog after the appeal"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-regulated-product-appeals, amazon-communications]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["bulk file update did not go through", "claims still live after appeal", "flat file change not applied", "proof corrected content submitted", "listing still shows removed claims"]
error_text: []
asked_as: ["During a compliance appeal, an outside consultant noted that the previous appeal said flagged claims had been removed but the live catalog still showed them, and asked where the claims still appeared "]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: case
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-listing-partial-update-flat-file.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0197"
---

## Question

During a compliance appeal, an outside consultant noted that the previous appeal said flagged claims had been removed but the live catalog still showed them, and asked where the claims still appeared and whether a case record could prove corrected content was submitted.

## Answer

Never tell Amazon or a client that claims were removed until you have checked the live listing and backend values after a bulk upload, because a flat-file change can fail to reach the catalog. When it does not apply, request the change through a Seller Support case and keep the case ID; it records that corrected content was submitted and can be cited in a later appeal.

## Cause

The content correction was uploaded by bulk file but did not apply to the live listing. Why it failed is not established in the thread; the change was then made through a Seller Support case.

## Fix

1. After any bulk file correction, check the processing report and the live detail page for every changed field instead of assuming the upload applied.
2. If the change did not apply, open a Seller Support case asking Amazon to update the named attributes (operator approval required before submitting).
3. Keep the case ID as the record that corrected content was submitted, and cite it in any later appeal.
4. Remove borderline images while the appeal is open if they are close to non-compliant.

## Verify

The live detail page and backend attributes no longer show the flagged claims, and the case shows the requested change. The thread does not show whether the change applied or whether the appeal reviewer accepted the case as proof.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-listing-partial-update-flat-file.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: A bulk-file claim removal can silently fail to reach the live listing, and a Seller Support case both applies the change and serves as appeal proof.
- Existing coverage: full (`MAG SOPs/README.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `Amazon Seller Help/articles/055-amazon-s-a-to-z-guarantee-claims-G27951.md`).
