---
id: KC-0340
title: "Support requests acknowledgement before investigating missed delivery window defects"
kind: decision-aid
topic: logistics
status: draft
skills: [amazon-logistics, amazon-communications]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Shipment summary > Problems"
surface_verified: false
symptom_keywords: ["acknowledge before investigation", "missed delivery window dispute", "only Acknowledge available"]
error_text: ["Missed delivery window", "Acknowledge"]
asked_as: ["Is there an alternative to acknowledging missed delivery window defects before Support investigates?"]
synonyms: ["MDW", "inbound performance appeal", "delivery window acknowledgement"]
resolution_status: diagnosis-only
fix_source: agency
evidence_location: case
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-11
review_by: 2027-11
provenance: "ledger:KC-0340"
---

## Question

Seller Support asks the seller to acknowledge disputed missed delivery window defects before it investigates. Is acknowledgement required, and is there another review route?

## Answer

Treat the request as case-specific until Amazon identifies the governing requirement and the effect of acknowledgement. Published Amazon moderator guidance describes missed-window appeals and escalation through an existing case, but does not establish that these routes are available in every live account. A Problems page can show only Acknowledge controls; that alone does not establish that acknowledgement is mandatory before an investigation. Ask for manual review or escalation and clarification of acknowledgement's effect before deciding.

## Cause

The reason for the Support prerequisite is unconfirmed. Published appeal instructions and the controls visible on a particular shipment can differ; neither establishes whether acknowledgement changes the defect metric or later dispute eligibility.

## Fix

1. Capture the exact Support request, defect type, coaching level, status and controls. Inspect the selected account's Problems view without acknowledging the defect.
2. Compare the selected calendar delivery window at assessment with actual carrier arrival or delivery evidence, including time zones. Appointment compliance and later receiving or processing events do not by themselves establish calendar-window compliance.
3. If a dispute or appeal control is available, prepare the shipment-specific evidence for the operator's approval. Published missed-window guidance describes Shipping Queue > Shipment Summary > Inbound Performance > Appeal; confirm the live route before using it.
4. If only Acknowledge is visible, prepare a reply in the existing case requesting review by the inbound performance investigation team or escalation. Ask Amazon to cite the acknowledgement prerequisite and explain its effect on defect status, metrics and further disputes.
5. Apply prep, label, carton or tracking rules only to their stated defect type and marketplace. Do not infer a missed-window investigation deadline or acknowledgement requirement from those rules.

## Verify

After an approved submission, verify the sent text, case receipt and subsequent response. Confirm each disputed defect's status and metric separately. A case marked Resolved or an acknowledged row is insufficient evidence that the defect was removed or the underlying question investigated.

## Stop before

Stop before acknowledging a defect, submitting an appeal or sending a case reply unless the operator approved that exact action and wording. Do not describe acknowledgement as harmless or as preserving dispute rights without evidence.

## Sources

- First-party: none captured locally for the acknowledgement prerequisite or its effects.
- Published Amazon moderator guidance on a missed-window appeal: https://sellercentral.amazon.com/seller-forums/discussions/t/02214a14-30c3-45f0-a6aa-ce0598f83cc0 (FIST context; public guidance, live route unconfirmed).
- Published Amazon moderator guidance offering missed-window case escalation: https://sellercentral.amazon.com/seller-forums/discussions/t/4d7ef61c-636d-4cb3-b757-1fa04c720476 (FIST context; seller retains delivery-window responsibility).
- Published Amazon moderator guidance describes acknowledgement and dispute as alternatives for general inbound alerts: https://sellercentral.amazon.com/seller-forums/discussions/t/08c23964-8dc7-4c99-915b-b12f6f2642fc (older guidance; not a universal missed-window eligibility rule).
- Procedure: `skills/amazon-communications/references/appeal-writing-posture.md` (evidence-led wording and admission limits).
- Evidence: team vault ledger row for this id.

## Gaps

No verified universal rule establishes that acknowledgement is required before missed-window investigation, preserves or waives later disputes, removes a defect, or changes its metric. A Support request and a limited live UI observation do not settle those effects. Escalation success, live appeal availability, any applicable deadline and other marketplaces remain unverified. This unit stays draft and unverified pending human review and suitable verification.
