---
id: KC-0177
title: "FBA capacity showing full for a future month: how to request more and what the reservation fee means"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > FBA Inventory > Capacity Manager"
surface_verified: false
symptom_keywords: ["capacity full can we still ship", "request capacity increase", "reservation fee bid", "performance credits capacity"]
error_text: []
asked_as: ["Capacity showed as full, and the client asked whether it could still create a sea-freight shipment arriving in a later month and how to get more storage capacity."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md", "Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md"]
related_sops: [knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0177"
---

## Question

Capacity showed as full, and the client asked whether it could still create a sea-freight shipment arriving in a later month and how to get more storage capacity.

## Answer

When capacity looks full, check the limit for the month the shipment will actually arrive as well as the current month before you bid. If that limit is still short, submit a Capacity Manager request for a future period with the extra volume and a maximum reservation fee. Performance credits from sales on the extra space can offset the fee, but it is owed even for unused space, and requests cannot cover the current period.

## Cause

Capacity limits are set per period. In the thread, the arrival month already had a higher limit, so the account manager judged that no extra capacity was needed. Whether Seller Central checks a new shipment against the arrival month's limit rather than the current one is not confirmed by a local capture. More capacity comes through a Capacity Manager request with a maximum reservation fee; no upfront payment is required, and the fee is owed even if the extra space goes unused.

## Fix

1. Open Capacity Manager and check the confirmed or estimated limit for the period when the shipment will arrive.
2. If that period's limit covers the shipment, plan to it and do not bid.
3. If more is needed, click Create new request for a future period; requests cannot be submitted for the current period.
4. Enter the extra volume and the maximum reservation fee per cubic foot (US) you will pay. Estimate it from the downloadable reservation fee history or Amazon's calculator.
5. Submit only with operator approval. Performance credits earned from sales using the extra capacity can offset the fee, and the fee is still owed for space you do not use.

## Verify

Capacity Manager shows the request and its outcome, and the target period's limit covers the planned inbound volume.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`
- First-party: `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`
- Also in: `knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the check of the arrival month's limit before bidding, otherwise largely covered by the capacity SOP and KC-0004.
- Existing coverage: full (`knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`).
