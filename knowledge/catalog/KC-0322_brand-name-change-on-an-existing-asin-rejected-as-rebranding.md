---
id: KC-0322
title: "Brand name change on an existing ASIN rejected as rebranding by Selling Partner Support"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-communications]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["brand name change rejected", "rebrand existing ASIN", "change brand on ASIN", "Brand Name Policy rebranding", "new ASIN for new brand"]
error_text: ["We are unable to approve this change, as it does not comply with our Amazon Brand Name Policy. We do not allow changes to the brand name on existing ASINs when those changes constitute rebranding, as this can lead to customer confusion. If you wish to sell your product under a new brand name, we recommend creating a new ASIN for the rebranded product.", "Please note that minor corrections: such as fixing typos, adjusting capitalization, or addressing issues with legal abbreviations: are permitted. Any changes beyond such minor corrections are considered rebranding and will not be approved."]
asked_as: ["The agency requested a brand name update on an existing ASIN to a new brand name; Amazon declined."]
synonyms: []
resolution_status: diagnosis-only
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md"]
related_sops: ["MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md"]
supersedes: []
contradicts: ["MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md"]
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0322"
---

## Question

The agency requested a brand name update on an existing ASIN to a new brand name; Amazon declined.

## Answer

Do not try to rename the brand on an existing ASIN as part of a rebrand; Selling Partner Support rejected it under the Brand Name Policy and recommended creating a new ASIN. Only minor corrections such as typos, capitalization or legal abbreviations go through the brand update issue type. Plan a rebrand as new ASINs, and note that the MAG SOP rebrand path conflicts with this reply until a human resolves it.

## Cause

Amazon Brand Name Policy does not allow changing the brand on an existing ASIN when the change is a rebrand, because it can confuse customers. Only minor corrections (typos, capitalization, legal abbreviations) are approved.

## Fix

1. Decide whether the change is a minor correction (typo, capitalization, legal abbreviation) or a rebrand.
2. For a minor correction, contact Selling Partner Support, choose the brand update issue type, complete the form and submit, or use Seller Assistant (operator approval required).
3. For a rebrand, create a new ASIN for the product under the new brand rather than editing the existing one.

## Verify

Not established in the thread. The agency was still asking an Amazon contact for another option when the thread ended; no minor-correction request or new-ASIN launch is recorded.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md`
- Also in: `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Verbatim support reply that rebranding an existing ASIN is refused under the Brand Name Policy, which conflicts with the MAG SOP rebrand path.
- Existing coverage: full (`Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md`, `MAG SOPs/catalog/brand-registry-sop-how-to-update-brand-name.md`).
