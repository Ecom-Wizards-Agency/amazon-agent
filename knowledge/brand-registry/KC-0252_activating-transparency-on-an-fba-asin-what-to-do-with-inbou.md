---
id: KC-0252
title: "Activating Transparency on an FBA ASIN: what to do with inbound stock and how to label units"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: false
surface: "Brand Registry > Transparency; Send to Amazon; AWD auto-replenishment settings"
surface_verified: false
symptom_keywords: ["Transparency activation inbound stock", "Transparency code per unit or box", "pause AWD auto replenishment Transparency", "send coded units before Transparency"]
error_text: []
asked_as: ["Before Transparency protection went live on a brand, the team needed to know whether any shipments without codes were still in transit and how to get coded stock into FBA before the listing locked."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0252"
---

## Question

Before Transparency protection went live on a brand, the team needed to know whether any shipments without codes were still in transit and how to get coded stock into FBA before the listing locked.

## Answer

Before Transparency protection goes live, check every inbound flow for uncoded units, including AWD stock and its auto-replenishment, and land a coded batch in FBA first. Every sellable unit needs its own code on the unit, not on the shipping box. Uncoded stock still in AWD or in transit at activation may be set aside, so move the activation date or plan relabelling for it.

## Cause

Once Transparency protection is active, units without a valid code are set aside (help page). Uncoded stock still in transit, and uncoded AWD units that replenish into FBA after activation, can therefore be blocked. The thread says protection takes about 30 days after the coded units arrive; no cited page confirms that timing.

## Fix

1. ["1. Confirm no FBA or AWD shipments without Transparency codes are still in transit.", "2. Pause AWD auto-replenishment while the coded batch is prepared; manual sends remain possible. Decide what happens to uncoded units stored in AWD, because after activation they may not be accepted into FBA.", "3. Have the 3PL apply a Transparency code to each sellable unit (not the outer box), together with the FNSKU or manufacturer barcode; a combined sticker is an option.", "4. Send a small coded batch per SKU so it arrives before activation.", "5. Resume auto-replenishment once the coded shipment is receiving, after confirming whether the AWD stock carries codes."]

## Verify

The coded shipment is receiving before activation and no uncoded inbound remains.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Sources cover enrolment and per-unit codes but not the activation-time logistics: clearing uncoded inbound, pausing AWD auto-replenishment and landing a coded batch first.
- Existing coverage: full (`MAG SOPs/README.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
