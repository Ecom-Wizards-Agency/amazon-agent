---
id: KC-0078
title: "FBM late shipment risk: some SKUs fall back to a 1-day handling time instead of the set business-day handling time"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health (Late Shipment Rate); Manage All Inventory > Edit listing > Offer > Handling Time; flat file handling time column"
surface_verified: false
symptom_keywords: ["late shipment rate above 4%", "handling time showing 1 day", "handling time not syncing", "FBM late delivery benchmark", "what counts as late shipment"]
error_text: []
asked_as: ["A brand with FBM orders asks what Amazon's late-delivery benchmark is and what 'late' means, while late shipments put the account at risk."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md", "MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0078"
---

## Question

A brand with FBM orders asks what Amazon's late-delivery benchmark is and what 'late' means, while late shipments put the account at risk.

## Answer

An FBM order counts as late when it ships after the expected ship date, which comes from the offer's handling time in business days; the target is a late shipment rate of under 4%. If some SKUs show a 1-day handling time instead of the value you set, those orders can turn late even when the warehouse ships on its normal schedule. Audit handling time on every FBM SKU, fix it by flat file or in the listing editor, and keep rechecking.

## Cause

Amazon's target is a late shipment rate of under 4%. Most SKUs were set to a 4-business-day handling time, but some showed a 1-day handling time in the backend instead, so orders on those SKUs ran against a shorter ship-by promise. Why those SKUs showed 1 day was not established in the thread.

## Fix

1. Check the Late Shipment Rate in Account Health against the 4% target.
2. Review the handling time on every FBM SKU and find any that show 1 day instead of the intended business-day value.
3. Correct the handling time through a flat file (handling time column) and, where it does not take, directly in the listing editor.
4. Keep monitoring and recheck SKUs, because the agency saw the wrong value reappear and had to correct it more than once.
5. If FBA stock has arrived and the FBM fulfilment setup is the problem, consider pausing FBM until it is fixed (operator approval).

## Verify

Every FBM SKU shows the intended handling time in the listing, and the Late Shipment Rate trends under 4% in the following periods.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Also in: `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the failure mode where some FBM SKUs silently fall back to a 1-day handling time and become late, fixed by flat file plus listing edits.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/supplemental-article-understanding-order-handling-capacity-on-amazon-seller-central.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
