---
id: KC-0261
title: "Transparency went live before coded stock arrived: units in AWD cannot be sent on to FBA"
kind: diagnosis
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["Transparency activated before inventory arrived", "units without Transparency codes in AWD", "change Transparency start date", "cannot book in uncoded inventory", "Transparency protection timing"]
error_text: []
asked_as: ["Transparency protection was activated for one variation before its units, which carried no Transparency codes, reached Amazon storage; the team asked whether that inventory can still be booked into FB"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0261"
---

## Question

Transparency protection was activated for one variation before its units, which carried no Transparency codes, reached Amazon storage; the team asked whether that inventory can still be booked into FBA.

## Answer

Time Transparency activation per variation against the stock pipeline: once protection is live, units without valid codes are set aside instead of sold. Before activating, confirm no uncoded stock is still in transit, in AWD or at a 3PL; ship any uncoded batch while protection is off and require codes on every batch after it. If uncoded stock is still on its way, ask Transparency support to move the start date. If activation happens first, plan a removal back to your warehouse to label the units before sending them again.

## Cause

Once an ASIN is enrolled and Transparency is active, every unit must carry a valid Transparency code; units without one are set aside. Inventory that was produced before activation and has no codes cannot be booked in, so it has to come back to the warehouse for labelling.

## Fix

1. Before activating Transparency, check which variations still have uncoded units in transit, in AWD or in a 3PL.
2. Where uncoded stock is still on its way, ask Brand Registry / Transparency support to set a later protection start date for those variations so it can be received first.
3. If activation already happened, remove the uncoded units from AWD back to the 3PL, apply Transparency codes, and send them in again.
4. Variations whose stock already carries codes can be booked in normally.

## Verify

The Transparency status for each variation shows the intended start date, and new shipments for protected ASINs only contain coded units.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- Also in: `MAG SOPs/catalog/logistics-sop-how-to-send-inventory-to-amazon-warehousing-and-distribution-awd.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the timing risk that Transparency activation before uncoded stock arrives strands units in AWD, and that support can move the start date.
- Existing coverage: full (`Advertising Help After Login/articles/219-amazon-dsp-inventory-policies-GUYW2GE498ANTH8Y.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
