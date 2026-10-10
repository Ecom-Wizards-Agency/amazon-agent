---
id: KC-0302
title: "Branded search terms leak into non-branded discovery campaigns: add own-brand terms as campaign-level negative phrase"
kind: rule
topic: ads
status: reviewed
skills: [amazon-sponsored-products-bulk-files, amazon-ppc-weekly-management, amazon-ads-console]
marketplaces: [all]
marketplace_inferred: true
surface: "Ads console / bulk file: campaign negative keywords"
surface_verified: false
symptom_keywords: ["branded keywords in discovery campaigns", "brand negatives non-branded campaigns", "branded revenue inside generic campaigns", "negative exact vs negative phrase for brand terms", "exclude own brand from auto and broad campaigns"]
error_text: []
asked_as: ["A reviewer found newly built discovery campaigns without branded negative keywords and with unclear ad group names; in a later rollout, a teammate began adding brand negatives to non-branded campaigns"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0302"
---

## Question

A reviewer found newly built discovery campaigns without branded negative keywords and with unclear ad group names; in a later rollout, a teammate began adding brand negatives to non-branded campaigns and asked how to set them up while moving the branded spend into dedicated branded campaigns.

## Answer

Exclude your own brand terms from every non-branded discovery campaign as campaign-level negative phrase. Negative exact only blocks the exact query and its close variants, so longer brand-plus-generic queries still get through. Make sure branded campaigns exist to catch that traffic. If a product has no exclusion list yet, build one from an n-gram of the search term report or leave the product out of the discovery build.

## Cause

Discovery campaigns (auto, broad and phrase) can match queries that contain the brand's own name unless brand terms are excluded, so branded traffic and revenue land in non-branded campaigns and distort their ACOS and the branded/non-branded split. The first-party negative keyword page says negative exact only blocks the exact query and close variations, while negative phrase blocks any query containing the complete phrase (up to four words). The agency lead required negative phrase but did not give the reason in the thread. One product had no standard exclusion list to copy from.

## Fix

1. Add every verified own-brand term (brand name, aliases, common misspellings) to each non-branded discovery campaign as a campaign-level negative phrase, not negative exact.
2. Make sure branded traffic still has a home: dedicated branded campaigns must exist or be built alongside, and they must not carry own-brand negatives.
3. If a product has no standard exclusion list, leave it out of the discovery build or run an n-gram of its search term report to build the list first.
4. Name campaigns and ad groups by the agency naming rule so match type and intent are readable before upload.
5. Adding negatives or campaigns is a campaign change and needs operator approval; once it is approved, a bid platform can batch-apply the negatives.

## Verify

The search term reports of non-branded campaigns show no brand queries after the review window, and branded revenue appears in the branded campaigns instead.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The agency's launch guardrails already require own-brand terms as campaign-level Negative Phrase in generic campaigns; the card adds the Sponsored Brands approval wait, the n-gram fallback when no exclusion list exists and the baseline review after 7 and 14 days.
- Existing coverage: full (`Advertising Help After Login/articles/060-branded-keyword-guidelines-and-keyword-suspension-G2QZJUGUT4RGLJ6N.md`).
