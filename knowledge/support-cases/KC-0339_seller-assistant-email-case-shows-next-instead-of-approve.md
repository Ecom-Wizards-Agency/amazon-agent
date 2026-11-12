---
id: KC-0339
title: "Seller Assistant email case shows Next instead of Approve"
kind: procedure
topic: support-cases
status: draft
skills: [amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Seller Assistant > email case wizard"
surface_verified: true
symptom_keywords: ["Seller Assistant Next instead of Approve", "Step 1 of 2 Issue summary", "Step 2 Contact channel", "email case wizard", "final Submit versus chat Submit"]
error_text: []
asked_as: ["Seller Assistant shows Next instead of Approve on an email case."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: run-note
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [skills/amazon-communications/references/seller-assistant-route.md]
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0339"
---

## Question

Seller Assistant shows Next instead of Approve on an email case. Does Next create the case?

## Answer

Next advances from the issue summary to the contact channel. Continue through the case wizard, choose Email when offered, and verify the actual case record after its final Submit. The chat composer has a separate Submit control.

## Cause

This interface uses a two-step email-case form. A route or tool expecting a single Approve control will not recognise its Next button or distinguish the final case submission from the chat composer.

## Fix

1. Verify the selected seller and marketplace. Match the Step 1 of 2 Issue summary subject, signed details and attachment names to the approved request.
2. Advance with Next only inside that verified case card. Automation uses the guarded approve --label Next action with the summary hash and case_summary binding; generic Next navigation is not a substitute.
3. On Step 2 of 2 Contact channel, select Standard Support if needed to expose Email, then choose Email when offered. Review the final case-card Submit separately from the chat composer control.
4. Submit only the approved case content and files. If delivery is uncertain, read back the same conversation and case log before taking any further action.

## Verify

A new case ID and its stored seller contact must match the approved subject, signed message and every expected attachment. Check attachment counts and readback checksums when available. Advancing with Next proves only the step transition; case creation does not prove the underlying issue is resolved.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `skills/amazon-communications/references/seller-assistant-route.md`
- Implementation: `tools/amazon-operations/seller-assistant.mjs`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The two-step form separates summary review, support type, channel choice and final case submission. Broader marketplace availability remains unverified. A timed-out final Submit must be reconciled with the saved conversation and case record; never resend solely because the tool returned uncertain.
- Existing coverage: partial (`skills/amazon-communications/references/seller-assistant-route.md`, `tools/amazon-operations/seller-assistant.mjs`).
