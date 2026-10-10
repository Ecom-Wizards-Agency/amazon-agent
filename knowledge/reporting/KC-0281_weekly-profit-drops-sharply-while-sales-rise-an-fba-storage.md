---
id: KC-0281
title: "Weekly profit drops sharply while sales rise: an FBA storage and inbound fee charge landed in that week"
kind: diagnosis
topic: reporting
status: reviewed
skills: [amazon-reporting, amazon-ads-performance-briefs]
marketplaces: [US]
marketplace_inferred: true
surface: "Weekly performance snapshot (profit tool) / Seller Central Payments transaction view"
surface_verified: false
symptom_keywords: ["profit dropped this week", "margin down sales up", "storage fee profit dip", "inbound placement fee charge hits profit", "weekly profit swing"]
error_text: []
asked_as: ["A weekly performance snapshot showed sales up week over week while profit fell sharply; the client asked whether the storage fee caused it."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0281"
---

## Question

A weekly performance snapshot showed sales up week over week while profit fell sharply; the client asked whether the storage fee caused it.

## Answer

A one-week profit collapse with rising sales is often a monthly FBA storage or inbound fee charge posting in that week. Check the payments transaction view for the fee line before diagnosing ads or pricing. Flag the charge in the weekly report and judge the trend on profit excluding the lump fee.

## Cause

Monthly FBA storage fees are assessed per calendar month and post as one charge, so a profit tool that books fees on the charge date loads a month of cost into a single week. In the source case the weekly report noted a combined storage and inbound fee charge in that week, and the analyst confirmed it as the main reason; profit returned to normal the following week. How and when inbound placement fees post was not established in the thread.

## Fix

1. When weekly profit falls while sales rise, check the transaction view for fee charges posted in that week.
2. Look for FBA storage fee and inbound placement or inbound fee lines and their amount.
3. Note the charge in the weekly report so the reader does not read it as an operational problem.
4. Compare profit across weeks excluding the lump charge, or spread it over the month, to judge the underlying trend.

## Verify

Profit and margin return to their usual level the next week, and the fee line explains the gap.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Explains a one-week profit collapse with rising sales as a monthly FBA storage and inbound fee charge posting in that week, to rule out before diagnosing ads or pricing.
- Existing coverage: full (`Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `AdLabs Help/articles/003-rpc-bidding-formula-acos-goals.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
