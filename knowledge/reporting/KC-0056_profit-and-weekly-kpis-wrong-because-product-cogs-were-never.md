---
id: KC-0056
title: "Profit and weekly KPIs wrong because product COGS were never entered in the profit analytics tool"
kind: diagnosis
topic: reporting
status: reviewed
skills: [amazon-ads-performance-briefs, amazon-client-onboarding, amazon-reporting]
marketplaces: [all]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["COGS missing profit tool", "profit too high zero cost", "weekly KPIs wrong COGS", "cost of goods not showing", "margin wrong missing COGS"]
error_text: []
asked_as: ["A product showed no cost of goods in the profit analytics tool across several date ranges, so profit in the weekly update was overstated."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [sop-drafts/2026-08-08_amazon-client-onboarding.md]
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0056"
---

## Question

A product showed no cost of goods in the profit analytics tool across several date ranges, so profit in the weekly update was overstated.

## Answer

Before reporting profit or margin, confirm every SKU has COGS in the profit tool, because a missing cost silently shows as zero and inflates profit. Collect COGS for every SKU at onboarding and enter them with an effective date that covers the reporting history.

## Cause

COGS for the product had never been entered in the profit tool; it was missing from the onboarding form, so the tool calculated profit with zero cost.

## Fix

1. Check every SKU in the profit tool for zero or blank COGS before reporting profit.
2. Get the COGS from the client, or edit access to the tool so the agency can enter them.
3. Enter COGS with the correct effective date so past ranges recalculate.
4. Re-run the affected weekly KPIs and correct earlier reports.
5. Make COGS a required field in the onboarding form.

## Verify

Profit and margin in the tool change after COGS are applied and match a manual check.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `sop-drafts/2026-08-08_amazon-client-onboarding.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Missing COGS in the profit tool silently shows as zero cost and inflates reported profit; COGS must be collected at onboarding.
- Existing coverage: partial (`MAG SOPs/README.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`, `AdLabs Help/articles/003-rpc-bidding-formula-acos-goals.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
