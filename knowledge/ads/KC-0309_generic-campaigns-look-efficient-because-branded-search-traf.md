---
id: KC-0309
title: "Generic campaigns look efficient because branded search traffic is hidden inside them"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-audit, amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: false
surface: "Amazon Ads Console > Sponsored Products > search term report and campaign naming"
surface_verified: false
symptom_keywords: ["branded spend in discovery campaigns", "branded traffic leaking into generic campaigns", "brand negatives on generic ad groups", "generic acos hidden by branded sales", "shield campaign branded spend"]
error_text: []
asked_as: ["A branded-terms analysis of the search term report found that a large share of ad spend went to branded searches, and most of it sat outside the brand-defense (Shield) campaigns."]
synonyms: []
resolution_status: partial
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
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0309"
---

## Question

A branded-terms analysis of the search term report found that a large share of ad spend went to branded searches, and most of it sat outside the brand-defense (Shield) campaigns.

## Answer

Audit branded spend by search term, not by campaign name, because generic campaigns often absorb branded queries through phrase and broad match or through brand terms targeted under a discovery label. Put branded traffic in brand-defense campaigns at the branded ACOS target and exclude own-brand terms from every generic campaign as campaign-level negative phrase. Expect generic ACOS to jump once the branded subsidy is gone; that number is the true cost of non-branded growth, not a regression.

## Cause

Two causes. Campaigns named as non-branded discovery deliberately targeted a brand phrase on phrase and broad match, so branded traffic carried a discovery label and was priced at the discovery ACOS target. Generic phrase and broad keywords also matched branded queries because their ad groups had no brand negatives. The cheap branded sales subsidised the discovery numbers and hid a much higher true generic ACOS. Duplicated campaigns were a minor factor.

## Fix

1. Pull the search term report for the window and tag each search term as branded (contains any own-brand token, including brand-plus-generic phrases) or generic.
2. Sum branded spend by campaign and compare it to the campaign's name and target ACOS.
3. Move or rename campaigns that mainly serve branded traffic into the brand-defense group and price them at the branded ACOS target (operator approval required).
4. Add every verified own-brand term as a campaign-level negative phrase in every generic campaign, per the agency launch guardrail; brand-defense campaigns keep no own-brand negatives (operator approval required before applying).
5. Re-baseline the generic campaigns on their ACOS without branded traffic and expect reported generic ACOS to rise while spend falls.

## Verify

Once the 72-hour buffer for negative keywords has passed, branded spend outside the brand-defense campaigns is close to zero and reappears inside them, and top-of-search share on core brand exact terms holds. The source thread did not report the outcome of this check.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The launch guardrail and sibling cards CARD-2034 and CARD-1529 already state the brand-negative rule; this card adds the search-term audit, the finding that branded traffic subsidises reported generic ACOS, and the re-baseline expectation.
- Existing coverage: partial (`Advertising Help After Login/articles/059-add-negative-keywords-or-negative-products-GTEHPEG5BXY9UX5W.md`).
