---
id: KC-0297
title: "Copied campaign advertises every variation instead of the one intended: original ad groups still enabled"
kind: diagnosis
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management]
marketplaces: [all]
marketplace_inferred: true
surface: "Amazon Ads Console > Campaign manager > Campaigns > More > Copy; campaign ad groups list"
surface_verified: false
symptom_keywords: ["copied campaign targets all variations", "duplicated campaign extra ad groups enabled", "campaign copy advertising wrong variation", "why are we targeting every variation"]
error_text: []
asked_as: ["An ads lead saw in the console that a set of new campaigns advertised every variation of a product family, while the plan was to advertise only one variation, and asked why."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/019-copy-a-campaign-GPFGH67KMNLQ5TKU.md", "Advertising Help After Login/articles/193-understand-ad-groups-GKPA6T8WW3AYKV4Q.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0297"
---

## Question

An ads lead saw in the console that a set of new campaigns advertised every variation of a product family, while the plan was to advertise only one variation, and asked why.

## Answer

When you copy a campaign, Amazon copies its ad groups, keywords and bids along with the settings and leaves out only archived ad groups, targets and advertised products, so every non-archived ad group from the original reappears in the copy. Before enabling the copy, check each ad group and advertised product against the plan and pause whatever it should not advertise. If only one variation should be pushed, keep only that variation's ad group enabled.

## Cause

The new campaigns were made by copying existing campaigns. A copy carries over the original's ad groups, so ad groups for the other variations stayed enabled in the copies and kept serving alongside the intended one.

## Fix

1. Open each copied campaign and list its ad groups and advertised products.
2. Compare them with the plan: which variation (or best-performing variations) the campaign is meant to advertise.
3. Pause or archive every ad group and advertised product the plan does not cover; changes on a live account need operator approval.
4. For Sponsored Products, a copy is created paused by default; before enabling it, pause or archive the ad groups and advertised products it should not carry. Archived ad groups, targets and advertised products in the original are not copied.

## Verify

Reopen the copied campaigns and confirm that only the intended variation's ad group and advertised products are enabled and that spend on the other variations stops.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/019-copy-a-campaign-GPFGH67KMNLQ5TKU.md`
- First-party: `Advertising Help After Login/articles/193-understand-ad-groups-GKPA6T8WW3AYKV4Q.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The copy page states ad groups are copied but no source ties that to the symptom of a copied campaign unexpectedly advertising every variation, nor tells you to disable unneeded ad groups after copying.
- Existing coverage: full (`Advertising Help After Login/articles/019-copy-a-campaign-GPFGH67KMNLQ5TKU.md`).
