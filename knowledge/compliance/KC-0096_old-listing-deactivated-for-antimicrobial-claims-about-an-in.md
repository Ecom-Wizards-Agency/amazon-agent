---
id: KC-0096
title: "Old listing deactivated for antimicrobial claims about an ingredient that an active listing also contains: review the active listing's copy"
kind: procedure
topic: compliance
status: reviewed
skills: [amazon-seo, amazon-regulated-product-appeals]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Account Health policy notice; listing copy"
surface_verified: true
symptom_keywords: ["listing deactivated antimicrobial claims", "antimicrobial claim ingredient", "pesticide claim ingredient other listings", "old listing removed claims check main listing"]
error_text: []
asked_as: ["An old, long-inactive listing was deactivated for antimicrobial claims."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md", "MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0096"
---

## Question

An old, long-inactive listing was deactivated for antimicrobial claims. The ingredient named in the notice is also in one of the brand's main active products, and the brand owner asked whether that listing needed review.

## Answer

When any listing is removed for antimicrobial claims, treat the named ingredient as a trigger and audit every active listing that contains it. Remove antimicrobial, antibacterial and antifungal wording from all fields, including backend terms, before Amazon flags the active listing too.

## Cause

Amazon treats antimicrobial, antibacterial and antifungal wording as a pesticidal claim (MAG SOP on pesticide yanks). The removal notice pointed at an ingredient, so any active listing that names the same ingredient with similar wording is exposed to the same enforcement.

## Fix

1. Read the deactivation notice and note the claim type and the ingredient it names.
2. Search all active listings for that ingredient and for antimicrobial, antibacterial, antifungal or other pest-related wording.
3. Remove those claims from title, bullets, description, backend search terms, intended-use and other attributes, and from image infographics and A+ (listing changes need operator approval).
4. Confirm each field actually changed after the update.
5. Leave the old inactive listing alone unless it is needed again.

## Verify

Not observed in the thread beyond the agency declaring the active listing clean. Done when every active listing containing the ingredient carries no antimicrobial-type claim in any field or image and no new policy notice appears.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`
- Also in: `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The pesticide SOP covers fixing a flagged listing; this adds auditing other active listings that contain the ingredient named in an antimicrobial-claim removal before they are flagged.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-mental-health-disorder-and-sleep-disorder-claims.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`, `knowledge/compliance/KC-0002_cosmetic-applicator-listing-removed-as-an-uncleared-medical.md`, `Amazon Seller Help/articles/149-enhance-listings-G88AQCL62ED7WDGA.md`).
