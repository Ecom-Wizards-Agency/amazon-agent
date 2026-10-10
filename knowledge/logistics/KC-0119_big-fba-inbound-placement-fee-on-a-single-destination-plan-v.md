---
id: KC-0119
title: "Big FBA inbound placement fee on a single-destination plan versus repacking for the Amazon-optimized split"
kind: decision-aid
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Send to Amazon > Step 2 placement options; AWD/GWD inbound"
surface_verified: false
symptom_keywords: ["avoid inbound placement fee", "placement fee single destination", "Amazon optimized split repack", "GWD single SKU cartons"]
error_text: []
asked_as: ["A seller moving stock from a 3PL to FBA saw a large inbound placement fee for one destination and asked how to avoid it, and what to do with upcoming overseas containers."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: []
observed: 2026-08
review_by: 2027-10
provenance: "ledger:KC-0119"
---

## Question

A seller moving stock from a 3PL to FBA saw a large inbound placement fee for one destination and asked how to avoid it, and what to do with upcoming overseas containers.

## Answer

Before accepting a single-destination plan, compare its placement fee with the repacking work the Amazon-optimized split needs. Create the shipment first, because the split quantities and the repack list only appear then. Stock that will sit in GWD should go in as clean single-SKU cartons, since it cannot be repacked there.

## Cause

Choosing a single destination incurs the inbound placement service fee; the Amazon-optimized multi-destination split has no placement fee but assigns its own quantities per destination, which may require opening or repacking cartons. The repack need is only known once the shipment is created.

## Fix

1. ["1. Create the shipment and compare placement options in Step 2, including the fee and the per-destination quantities.", "2. Count how many cartons the optimized split would require to be opened, rebuilt or verified; the final count can be far lower than a first SKU-level estimate.", "3. Estimate warehouse labour for that work and compare it with the placement fee.", "4. For stock bound for GWD, send clean single-SKU cartons only; the agency notes they cannot be repacked once inside. The thread did not establish whether the same holds for AWD.", "5. For overseas stock, repack at origin to the optimized quantities before the container leaves."]

## Verify

The chosen option shows the expected placement fee and the warehouse packing list matches the per-destination quantities.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Gives the trade-off between the single-destination placement fee and the repack work of the Amazon-optimized split, plus the clean single-SKU carton rule for AWD or GWD.
- Existing coverage: full (`Amazon Seller Help/articles/063-fba-features-services-and-fees-G201074400.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `MAG SOPs/README.md`).
