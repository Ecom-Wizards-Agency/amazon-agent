---
id: KC-0066
title: "Inherited campaigns with poor ROAS still live after account takeover: pause gradually, not all at once"
kind: decision-aid
topic: ads
status: reviewed
skills: [amazon-ads-console, amazon-ppc-weekly-management, amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: true
surface: "Amazon Ads Console > Campaign manager > Campaigns"
surface_verified: false
symptom_keywords: ["old campaigns still live with bad ROAS", "should we pause all inherited campaigns", "account takeover pause campaigns", "legacy campaigns wasting money after onboarding"]
error_text: []
asked_as: ["Shortly after the agency took over an existing ads account, the client pointed out that many inherited campaigns were still live with very poor ROAS and expected them to be stopped."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0066"
---

## Question

Shortly after the agency took over an existing ads account, the client pointed out that many inherited campaigns were still live with very poor ROAS and expected them to be stopped.

## Answer

When you take over an account with poorly performing legacy campaigns, pause only the ones that are irrelevant or bring no sales, and optimize the rest instead of switching everything off. New campaigns need time to replace the revenue that old ones still carry, so move spend over gradually. Explain this to the client up front so a few lingering weak campaigns are not read as neglect.

## Cause

Not a fault: inherited campaigns still carry part of the account's ad-driven revenue. Pausing them abruptly and relying on brand-new campaigns to replace that revenue risks a sharp sales drop while the new campaigns are still gathering data.

## Fix

1. Pause right away only the inherited campaigns that are irrelevant or bring no additional revenue.
2. Keep campaigns that still convert live and optimize them (bids, targets, budgets) instead of pausing them; changes need operator approval.
3. Launch the new campaign structure alongside and shift spend from old to new as the new campaigns prove themselves.
4. Tell the client the transition is deliberate and that results will improve gradually rather than overnight.

## Verify

The client accepted the gradual transition in the thread; track total ad sales and ROAS week over week during the takeover to confirm revenue holds while waste falls.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The MAG SOP already says to keep converting legacy campaigns and pause zero-order ones; the card adds only the framing of explaining a gradual transition to a client who wants everything paused.
- Existing coverage: full (`Advertising Help After Login/articles/211-understand-display-video-and-audio-campaigns-GTTX72LGYHYYDDJ9.md`).
