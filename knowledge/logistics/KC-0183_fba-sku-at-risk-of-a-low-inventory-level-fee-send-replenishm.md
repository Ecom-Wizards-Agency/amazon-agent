---
id: KC-0183
title: "FBA SKU at risk of a low-inventory-level fee: send replenishment before supply drops"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-fba-inventory-planning, amazon-logistics]
marketplaces: [DE]
marketplace_inferred: false
surface: ""
surface_verified: false
symptom_keywords: ["low inventory level fee", "low storage fee risk", "send stock to avoid low inventory fee", "days of supply fee"]
error_text: []
asked_as: ["The agency flags that a SKU in one EU marketplace is at risk of incurring a low-inventory-level fee unless stock is raised, and asks the client to send replenishment."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0183"
---

## Question

The agency flags that a SKU in one EU marketplace is at risk of incurring a low-inventory-level fee unless stock is raised, and asks the client to send replenishment.

## Answer

Watch fast-selling FBA SKUs for low-inventory-level fee risk and replenish before available supply falls below about 28 days, the level Amazon's readiness playbooks name; before a deal event they advise 4 to 6 weeks. Size the shipment from days of supply, not from a fixed unit count, and ship early enough that receiving time does not leave the SKU short. Check the current fee rule in Seller Central before quoting how it is charged.

## Cause

The thread called it 'low storage fees'; it is read here as the FBA low-inventory-level fee. The local readiness playbooks tie avoiding that fee to keeping enough available inventory (4 to 6 weeks before a deal event, at least 28 days afterwards), so thin stock on a fast-selling SKU puts it at risk. The exact fee trigger and how it is charged are not established in the thread or in a local capture.

## Fix

1. Check the SKU's available units and days of supply in FBA Inventory or the Restock report, and check whether Seller Central shows a low-inventory-level fee notice for it (the thread does not show where it appears).
2. Calculate the units needed to keep at least 28 days of supply, more before a deal event.
3. Ask the client to create and ship the replenishment shipment (shipment creation needs operator approval).
4. Track the shipment until it is received and available.

## Verify

After the replenishment is received, the SKU's available supply covers at least 28 days and no low-inventory-level fee notice shows for it.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The peak and deal playbooks mention the low-inventory-level fee only around deal events; the card adds the routine replenishment trigger for a flagged SKU.
- Existing coverage: full (`Amazon Seller Help/articles/101-policies-for-amazon-handmade-returns-refunds-restocking-fees-and-cancellations-G201817830.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
