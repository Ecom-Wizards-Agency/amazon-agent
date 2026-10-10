---
id: KC-0065
title: "Scaling a winning ad by adding more targets to the same campaign"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-audit, amazon-ppc-weekly-management]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["too many targets in one campaign", "how to scale winning campaign", "add targets or new campaign", "campaign level optimization"]
error_text: []
asked_as: ["A brand-side operator planned to expand cold targeting and branded search by adding targets to an existing winning campaign."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/007-understand-bid-adjustments-in-sponsored-ads-GQ4R4FR4H56JL6V8.md"]
related_sops: ["MAG SOPs/amazon-advertising/advertising-sop-naming-conventions-and-creation-guidelines.md"]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0065"
---

## Question

A brand-side operator planned to expand cold targeting and branded search by adding targets to an existing winning campaign.

## Answer

Scale a winning ad by copying it into new campaigns for new targeting rather than adding many targets to one campaign. Budget, bidding strategy and placement adjustments work at campaign level, so crowded campaigns lose control over individual targets.

## Cause

Budget, bidding strategy and placement adjustments are set at the campaign level, so the more targets a campaign holds, the less those levers can be tuned to any one of them.

## Fix

1. Keep the winning campaign's target set small.
2. Put new targeting (cold targets, branded search) into new campaigns that reuse the winning ad.
3. Scale budgets per campaign based on each campaign's results.

## Verify

Each new targeting group runs in its own campaign with its own budget, bidding strategy and placement settings.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/007-understand-bid-adjustments-in-sponsored-ads-GQ4R4FR4H56JL6V8.md`
- Also in: `MAG SOPs/amazon-advertising/advertising-sop-naming-conventions-and-creation-guidelines.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Scale a winning ad by copying it into new campaigns for new targeting, because budget, bidding strategy and placement levers are campaign-level.
- Existing coverage: full (`Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md`).
