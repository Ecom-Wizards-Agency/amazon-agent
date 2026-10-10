---
id: KC-0109
title: "Agency user cannot open or edit Seller Support cases until granted the Manage Your Cases permission"
kind: procedure
topic: support-cases
status: reviewed
skills: [amazon-communications, amazon-client-onboarding]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Settings > User Permissions (Manage Your Cases)"
surface_verified: false
symptom_keywords: ["cannot see support cases", "no access to case log", "Manage Your Cases permission", "agency user case access", "need edit permission for cases"]
error_text: []
asked_as: ["The agency needed access to the client's Seller Support cases and asked the account owner for the Manage Your Cases permission; a sibling message specified that edit rights were needed."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md"]
related_sops: [docs/team-owned-cases.md, skills/amazon-communications/references/seller-assistant-route.md, docs/rights/README.md]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0109"
---

## Question

The agency needed access to the client's Seller Support cases and asked the account owner for the Manage Your Cases permission; a sibling message specified that edit rights were needed.

## Answer

Before an agency user works Seller Support cases, have the account owner grant that user Manage Your Cases at Edit under User Permissions for the right account and marketplace. View only lets the user read the case log; creating and replying need Edit. Confirm with a real reply or case creation, not by opening the case log.

## Cause

Seller Central grants permissions per user and per area. The Manage Your Cases row controls Seller Support case access. View lets the user read the case log; Edit is needed to create cases and reply to them. The agency user lacked the needed grant until the account owner added it, and only a user who can manage permissions can grant it.

## Fix

1. Ask the account's primary user, or a user who can manage permissions, to open User Permissions in Seller Central settings.
2. Grant the agency user Manage Your Cases at Edit, not View, for the seller account and marketplace the cases concern.
3. Save. Then have the agency user reply to an existing case or start a new one. A refusal means the grant for that exact user is still wrong or not yet active, so recheck it and retry.

## Verify

The agency user can reply to an existing case or create a new one, and Seller Assistant no longer answers that the login lacks permission to create support cases. Opening the case log alone does not prove Edit access, because View allows that.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- Also in: `docs/team-owned-cases.md`
- Also in: `skills/amazon-communications/references/seller-assistant-route.md`
- Also in: `docs/rights/README.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The live-verified case route and the rights matrix already state the Manage Your Cases View/Edit rule for the team's own logins. This unit makes it a reusable onboarding answer for any agency user who needs case access.
- Existing coverage: partial (`docs/team-owned-cases.md`, `skills/amazon-communications/references/seller-assistant-route.md`, `docs/rights/README.md`, `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`).
