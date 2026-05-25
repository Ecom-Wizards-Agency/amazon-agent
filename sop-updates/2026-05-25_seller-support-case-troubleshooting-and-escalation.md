# SOP Update: Seller Support Case Troubleshooting And Escalation

Date: 2026-05-25
Status: applied locally
Source SOP: New SOP draft and Amazon operator routing guidance
Source link: N/A

## Problem

Recent Seller Central support work showed that case handling is faster when operators have a reusable process for existing-case follow-ups, live chat cadence, shipment defect disputes, local evidence storage, and sender-name traceability. The reusable process did not yet exist in GitHub without client-specific details.

## Verification

Verified against the current project routing rules, communications skill, SOP maintenance storage rules, and recent observed Seller Central support and shipment defect UI behavior. The update intentionally excludes client-specific case IDs, shipment IDs, ASINs, screenshots, Notion task URLs, local evidence, and actual local operator identity.

## Change Made

- Added a reusable SOP draft for Seller Central support-case troubleshooting, escalation, live chat, and inbound defect disputes.
- Updated Amazon communications guidance to require existing-case follow-ups, local operator full-name lookup, one-message-at-a-time chat behavior, root-cause evidence requests, and shipment defect disputes when photos/examples are needed.
- Updated Amazon operator routing guidance and workflow-router support-case notes with the same durable rules.

## Files Changed

- `sop-drafts/2026-05-25_seller-support-case-troubleshooting-and-escalation.md`
- `sop-updates/2026-05-25_seller-support-case-troubleshooting-and-escalation.md`
- `skills/amazon-communications/SKILL.md`
- `skills/amazon-operator-routing/SKILL.md`
- `skills/amazon-operator-routing/references/workflow-router.md`

## Checks Run

- `git diff --check`
- Searched tracked skill and SOP-update paths for accidental client names, case IDs, shipment IDs, ASINs, FNSKUs, and support-associate names from the source workflow.
- `git status --short`

The identifier search found only a pre-existing inventory-planning reference outside this support-case update. No new or modified support-case files contain the recent case-specific identifiers.

## Evidence

Evidence and screenshots from the source case handling remain in ignored local folders and the live task tracker. GitHub contains only reusable process knowledge and sanitized lessons.

## Follow-Up

After review, promote the SOP draft into the durable SOP library or keep it as the canonical tracked draft for Seller Support case handling. Continue adding sanitized lessons from future cases to this workflow rather than committing client-specific evidence.
