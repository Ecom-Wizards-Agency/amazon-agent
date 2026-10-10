---
id: KC-0203
title: "Manage Your Experiments A/B test cannot start the same day it is created"
kind: rule
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-seo]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Brands > Manage Experiments > Create a new experiment"
surface_verified: false
symptom_keywords: ["A/B test start today", "Manage Experiments start date", "cannot start experiment same day", "schedule MYE test", "experiment start date greyed out"]
error_text: []
asked_as: ["After the client approved a new content version, the agency wanted to start the A/B test the same day."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md"]
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0203"
---

## Question

After the client approved a new content version, the agency wanted to start the A/B test the same day. The experiment could only be scheduled, because Manage Your Experiments did not allow a same-day start.

## Answer

Plan Manage Your Experiments tests at least a day ahead, because the tool does not let a test start on the day it is created. Get content approved early, create the experiment, pick the earliest start date offered and report it to the stakeholder as scheduled. The tool may propose a later default start date, so check the field before saving.

## Cause

Manage Your Experiments takes a start date at creation and does not allow the current day; the form proposes a later default start date. The thread does not establish the exact minimum lead time.

## Fix

1. Finish and approve both content versions before creating the experiment.
2. Create the experiment in Manage Your Experiments and set the earliest start date the form accepts (not today).
3. Tell the stakeholder the test is scheduled, not running, and when it starts.

## Verify

The experiment shows as scheduled with the chosen start date, then switches to running on that date.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local source states that a Manage Your Experiments test cannot start on its creation day; the SOP only mentions a one-week default start date.
- Existing coverage: full (`Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/074-amazon-outlet-GHLYT4TPVCY2MJE3.md`).
