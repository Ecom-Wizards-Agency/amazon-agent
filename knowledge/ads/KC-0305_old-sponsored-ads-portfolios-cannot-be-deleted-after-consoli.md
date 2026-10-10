---
id: KC-0305
title: "Old Sponsored Ads portfolios cannot be deleted after consolidation: rename them so they read as retired"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["delete portfolio Amazon Ads", "cannot delete portfolio", "old portfolios renamed XXX", "merge portfolios cleanup"]
error_text: []
asked_as: ["The client saw portfolios renamed to a placeholder name in Amazon Ads and asked who created them and why."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/127-edit-your-portfolios-G57LGLBC94DGWXEH.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0305"
---

## Question

The client saw portfolios renamed to a placeholder name in Amazon Ads and asked who created them and why.

## Answer

Plan for leftover portfolios when you consolidate a portfolio structure, because Amazon Ads has no delete option for portfolios. Empty them, rename them with a clear retired marker and tell the client first. Unexplained renamed portfolios look like unauthorized changes.

## Cause

The first-party Edit your portfolios page lists rename, budget, move and remove-from-portfolio actions and no delete action, and the agency lead stated that portfolios cannot be deleted. After the agency merged campaigns into new portfolios, the emptied old portfolios stayed in the list, so the agency renamed them to mark them as retired.

## Fix

1. Move the campaigns into the new portfolio structure: Campaign Manager > All Campaigns, tick the campaigns, Bulk actions > Move to portfolio, Save changes.
2. Open each emptied portfolio and click Modify portfolio.
3. Edit the Portfolio name with an agreed retired marker so nobody assigns campaigns to it, then click Save changes.
4. Tell the client about the renamed portfolios before they notice them.
5. Moving campaigns and renaming portfolios are account changes and need operator approval.

## Verify

The old portfolios hold no campaigns and carry the retired name; all active campaigns sit in the new portfolios.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/127-edit-your-portfolios-G57LGLBC94DGWXEH.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source states that portfolios cannot be deleted or describes renaming emptied portfolios after consolidation.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-unauthorized-merging-of-two-parent-asins.md`).
