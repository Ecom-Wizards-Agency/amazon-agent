---
id: KC-0326
title: "Stranded inventory settings link redirects to AmazonSell business: inspect the classic settings and saved address"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics, amazon-client-onboarding]
marketplaces: [US, DE, UK, AU]
marketplace_inferred: false
surface: "Seller Central > Fix stranded inventory > Edit automatic action settings > automatic removal settings"
surface_verified: true
symptom_keywords: ["stranded inventory settings redirects", "AmazonSell business instead of settings", "classic stranded inventory return address", "automatic removal settings"]
error_text: []
asked_as: ["How do we check stranded inventory return settings when the AmazonSell settings link redirects to the business page?"]
synonyms: ["stranded inventory", "automatic action settings", "automatic removal settings"]
resolution_status: resolved
fix_source: agency
evidence_location: run-note
confidence: medium
verification: verified
verified_on: "2026-10-21"
verified_how: "live-ui"
amazon_sources: []
related_sops: [skills/amazon-client-onboarding/references/day-zero-assessment.md]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0326"
---

## Question

How do we check stranded inventory return settings when the AmazonSell settings link redirects to the business page?

## Answer

Use the classic stranded-inventory page when the new settings page redirects away. Inspect every saved removal action and the separate saved return address. An address alone does not establish that all stranded-inventory categories are configured for return.

## Cause

The new `/amazonsell/value-recovery-settings/afn-stranded-inventory` page worked in a US check but redirected to `/amazonsell/business` in a DE check. The DE `/amazonsell/value-recovery-settings` hub also redirected there. The reason for that difference was not established. The classic stranded settings remained accessible in the inspected DE, UK and AU accounts.

## Fix

1. Verify the selected seller account and marketplace, then open `/inventoryplanning/stranded-inventory` in that marketplace.
2. Select `Edit automatic action settings`, then `Click here to review or edit automatic removal settings`.
3. Read the saved radio selection and removal age or schedule for every group. The inspected DE and UK settings had two groups; the inspected AU settings had five. Count the groups shown rather than assuming the same categories everywhere.
4. Open the separate `Edit address` dialog and read the complete saved return destination. The stranded-inventory destination is separate from fulfillable and unfulfillable removal settings.
5. Close the inspection dialogs without saving. Report each removal action and whether the stranded-inventory address is complete.
6. For the other removal groups in the inspected DE account, `/fba/settings/index.html` linked to `/recoveryui/removal-setting/automated-lts` and `/recoveryui/removal-setting/automated-unfulfillable`. The first redirected to `/recoveryui/removal-setting/automated-fulfillable`. Follow the live FBA settings links and inspect each group's saved status, action, schedule and destination separately.

## Verify

The classic removal-settings dialog shows the saved selections, and its separate address dialog shows the saved destination for the same verified account and marketplace. Confirm every group before reporting that returns are activated throughout the stranded settings.

If the hub says `Not configured`, an editor with `Enable` and return preselected plus an empty address does not prove a saved return configuration. Record the saved hub status and identify the editor values as defaults.

## Stop before

Stop before saving any setting or address change unless the operator approved that exact action. This inspection requires no settings writes.

## Sources

- First-party: none captured yet.
- Procedure: `skills/amazon-logistics/SKILL.md`.
- Also in: `skills/amazon-client-onboarding/references/day-zero-assessment.md` requires both stranded-removal settings and the complete visible return destination; it does not document the route difference.
- Evidence: team vault ledger row for this id.

## Gaps

The redirect's cause and rollout scope are unknown. The observed routes and group counts do not establish availability or identical categories on every account or marketplace. Recheck the live page before relying on them.

When a mandatory-review banner appears, preselected recovery programs alone do not establish confirmed enrollment or consent. Record the banner and verify the saved program status separately.
