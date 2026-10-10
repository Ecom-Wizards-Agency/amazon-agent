---
id: KC-0298
title: "Branded search terms leaking into non-branded phrase campaigns, and a campaign named for a different match type"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads Console > Sponsored Products > campaign > search terms"
surface_verified: false
symptom_keywords: ["branded keywords in phrase campaign", "brand defense campaign mislabeled", "separate branded non-branded campaigns", "negate brand terms", "campaign naming mismatch"]
error_text: []
asked_as: ["An agency lead found a phrase campaign whose search terms were almost all branded (pure brand defense) while relevant generic terms had been negated, and another phrase campaign labelled as an exact r"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md", "Advertising Help After Login/articles/056-understand-keyword-match-types-GHTRFDZRJPW6764R.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-10
provenance: "ledger:KC-0298"
---

## Question

An agency lead found a phrase campaign whose search terms were almost all branded (pure brand defense) while relevant generic terms had been negated, and another phrase campaign labelled as an exact ranking campaign.

## Answer

Keep branded and non-branded traffic apart by adding brand terms as negative phrase keywords in non-branded phrase campaigns (a negative phrase keyword holds at most four words). Check that existing negatives do not block relevant generic terms. Make each campaign name match its actual match type and intent, and check this at launch, especially when automation generates the campaigns.

## Cause

Not confirmed in the thread. The PPC specialist guessed that an automated launch applied the naming convention wrongly. The result was a phrase campaign serving almost only branded queries while relevant generic terms were negated, and a phrase campaign named as an exact-match ranking campaign.

## Fix

1. In each non-branded phrase campaign, add the brand terms as negative phrase keywords so branded queries stay in brand-defense campaigns.
2. Review negatives in those campaigns and remove any that block relevant generic terms.
3. Rename or restructure campaigns whose name states a different match type or purpose from their actual targeting.
4. Check every other account for the same pattern.
5. Add a launch check that the campaign name matches match type and branded/non-branded intent.

## Verify

Search term report of non-branded campaigns shows no brand queries; campaign names match their match type and intent.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md`
- First-party: `Advertising Help After Login/articles/056-understand-keyword-match-types-GHTRFDZRJPW6764R.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the internal rule to negate brand terms in non-branded phrase campaigns and to check campaign names against match type at launch.
- Existing coverage: full (`Advertising Help After Login/articles/062-reserve-keywords-in-a-sponsored-brands-campaign-G86SD7HK6NHHRB9B.md`, `Advertising Help After Login/articles/060-branded-keyword-guidelines-and-keyword-suspension-G2QZJUGUT4RGLJ6N.md`, `Advertising Help After Login/articles/229-campaign-goals-for-sponsored-brands-GXXPFXLSVX9VD3U9.md`).
