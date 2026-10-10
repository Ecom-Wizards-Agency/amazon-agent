---
id: KC-0126
title: "Unrequested AWD-to-FBA transfers and FBM offers switched back to FBA: AWD replenishes FBA automatically, and stranded FBA units on a shared SKU force it back to FBA, so keep FBM on its own SKU"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-catalog, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Inventory > AWD inventory dashboard; Manage FBA Inventory > Stranded inventory; Manage All Inventory"
surface_verified: false
symptom_keywords: ["AWD sent inventory to FBA without request", "FBM listing changed to FBA", "stranded units after switching to FBM", "separate SKU for FBM", "AWD units on wrong ASIN"]
error_text: []
asked_as: ["The client saw thousands of units appear in FBA from AWD without anyone requesting a transfer, and noticed that some of its FBM offers had been changed to FBA."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-12
review_by: 2027-10
provenance: "ledger:KC-0126"
---

## Question

The client saw thousands of units appear in FBA from AWD without anyone requesting a transfer, and noticed that some of its FBM offers had been changed to FBA. It asked who requested the transfer, whether the units really existed in AWD, and asked the agency to stop switching FBM offers to FBA.

## Answer

Expect AWD to move stock into FBA on its own unless the SKU is opted out of automatic replenishment; a large unrequested transfer is replenishment working, not an error, so watch stranded inventory instead. Do not flip one SKU between FBA and FBM: leftover FBA units become stranded and the SKU cannot take new FBA stock while it is FBM. Create a separate SKU for FBM and keep the FBA SKU on FBA.

## Cause

AWD replenishes FBA automatically for SKUs not opted out of automatic replenishment, so transfers arrive without a manual request. A SKU the client sold as FBM still had a few FBA units under it; while the SKU was FBM those units were stranded and no new FBA stock could be sent for it, so the agency converted it back to FBA. Using one SKU for both channels made each switch strand or block inventory. The thread also reported stock booked against the wrong ASIN; that is a separate problem the thread did not resolve and it is not part of this card.

## Fix

1. On the AWD inventory dashboard, confirm the outbound replenishment transfers to FBA, the remaining AWD quantity per SKU, and whether each SKU is on automatic or manual replenishment.
2. Check Stranded inventory for SKUs whose offer was switched to FBM while FBA units remained; resolve them by converting the SKU back to FBA or removing the units (operator approval).
3. Create a dedicated SKU for FBM selling and leave the original SKU on FBA, so changing channels never strands units or blocks FBA replenishment.
4. Tell the client that AWD-to-FBA transfers are automatic unless a SKU is opted out, and that stranded inventory is the thing to monitor.

## Verify

No stranded inventory remains on the FBA SKU, the FBM SKU is active on its own, and AWD plus FBA quantities reconcile to the shipped units by ASIN.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/066-amazon-warehousing-and-distribution-awd-GF6ZC8VEBM7HCEGV.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The switching SOP shows how to convert between FBA and FBM but not that flipping one SKU strands leftover FBA units and blocks inbound, or that unrequested AWD-to-FBA transfers are normal replenishment.
- Existing coverage: partial (`knowledge/logistics/KC-0004_fba-capacity-limit-used-up-for-the-month-submit-a-capacity-m.md`, `MAG SOPs/catalog/catalog-sop-creating-multiple-offers-mfn-fba-for-an-asin.md`).
