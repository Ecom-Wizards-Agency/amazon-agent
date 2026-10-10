---
id: KC-0304
title: "Which negatives go into Exact, Broad and Auto launch campaigns when keywords are split into high, mid and low search volume tiers"
kind: reference
topic: ads
status: reviewed
skills: [amazon-sponsored-products-bulk-files, amazon-seo]
marketplaces: [all]
marketplace_inferred: true
surface: "Keyword workbook (volume tiers, exclusion list) and Sponsored Products bulk file"
surface_verified: false
symptom_keywords: ["HV MV LV campaign structure", "which negatives for broad campaign", "auto campaign negative exact master list", "launch campaign structure exact broad auto", "never ever list negative phrase"]
error_text: []
asked_as: ["A new teammate building launch campaigns asked whether Exact, Broad and Auto all get high, mid and low volume campaigns, and which negatives each one receives."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/056-understand-keyword-match-types-GHTRFDZRJPW6764R.md", "Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2024-01
review_by: 2027-10
provenance: "ledger:KC-0304"
---

## Question

A new teammate building launch campaigns asked whether Exact, Broad and Auto all get high, mid and low volume campaigns, and which negatives each one receives.

## Answer

Assign high-volume keywords to Exact without negatives, and mid and low volume to Broad with the exclusion list as negative phrase and the high-volume keywords as negative exact. Split Auto into its four targeting groups, with the exclusion list as negative phrase plus the whole master list as negative exact. This keeps the tiers from competing with each other and leaves Auto to discover new queries. Check the current launch guardrails before reuse: they add own-brand negative phrase to generic campaigns and do not describe the volume tiers.

## Cause

Not a fault: the team's launch structure assigns each keyword volume tier to one match type and uses negatives to stop the tiers and the Auto campaigns from bidding against each other. The rules lived in a voice message and a chat line rather than in a written SOP, so the teammate could not find them.

## Fix

1. Split the master keyword list by search volume into high (HV), mid (MV) and low (LV) tiers; mid and low may be combined when the list is short.
2. Exact campaign: target the HV keywords, with no negatives.
3. Broad campaign(s): target the MV and LV keywords; add the standing exclusion list as negative phrase and the HV keywords as negative exact, so Broad does not compete with Exact on those queries.
4. Auto: split into four campaigns (Loose Match, Close Match, Complements, Substitutes); add the exclusion list as negative phrase and the full master keyword list as negative exact so Auto only finds new queries.
5. The current launch guardrails also require own-brand terms as campaign-level negative phrase in every generic campaign, including Broad and Auto; apply them on top of this matrix.

## Verify

In the bulk file, the Exact campaign has no negative rows, each Broad campaign has the exclusion-list negative phrase rows plus HV negative exact rows, and each of the four Auto campaigns has the exclusion list and the full master list as negatives.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/056-understand-keyword-match-types-GHTRFDZRJPW6764R.md`
- First-party: `Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source describes the volume-tier split with its negative matrix (HV negative exact in Broad, full master list negative exact in Auto); internal guardrails cover only the Auto split and the exclusion list.
- Existing coverage: full (`Advertising Help After Login/articles/192-create-a-sponsored-products-campaign-GKLSYGFS2YD33FER.md`).
