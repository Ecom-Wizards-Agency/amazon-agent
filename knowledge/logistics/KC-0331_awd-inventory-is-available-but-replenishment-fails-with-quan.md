---
id: KC-0331
title: "AWD inventory is available but replenishment fails with Quantity per box over limit"
kind: diagnosis
topic: logistics
status: draft
skills: [amazon-logistics, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > AWD inventory and Shipments, orders and replenishments"
surface_verified: true
symptom_keywords: ["AWD stock already received", "AWD replenishment failed", "units per box limit changed", "carton splitting"]
error_text: ["Quantity per box over limit", "The quantity you entered is above the accepted limit for units per case."]
asked_as: ["Why can inventory already stored in AWD not move to FBA, and did the units per box rule change?"]
synonyms: ["case pack", "carton", "box configuration"]
resolution_status: diagnosis-only
fix_source: first-party-doc
evidence_location: run-note
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0331"
---

## Question

Inventory is already available in AWD, but replenishment reports Quantity per box over limit or an accepted-limit error for units per case. How can existing stock move to FBA, and has the box limit changed?

## Answer

Reconcile the recorded box configuration with the physical cartons and original receiving evidence. Current AWD guidance limits a single-SKU box to 150 units; older Amazon staff replies already describe this rule, so a new failure does not establish a recent policy change. Escalate accepted stock to the AWD team before ordering a costly return, because a supported correction or exception is not guaranteed. A request-confirmed banner does not prove that a replenishment shipment was created successfully.

## Cause

AWD moves inventory at the carton level as received. Inventory can show Available while downstream replenishment fails the recorded units-per-box validation. The observed failure identifies a box-configuration problem; it does not establish whether physical packing or Amazon's recorded configuration is wrong.

## Fix

1. Verify the seller and US marketplace. Open the exact order's Review details and capture the affected SKU, ordered cartons and units, status, and full error. Check outbound and reserved inventory before any further move.
2. Reconcile the original AWD inbound packing template, receiving records and physical packing evidence. If the stored configuration is inaccurate, ask AWD support for an evidence-based correction; do not enter a smaller quantity merely to bypass validation.
3. Prepare an AWD-team escalation with inbound and replenishment references, the accepted configuration and screenshots. Ask what supported correction or exception is available for stock already received. Obtain approval before sending. A historical support reply about clearing an error is not an exception entitlement or a turnaround guarantee.
4. If cartons physically exceed the limit and Amazon offers no supported correction, confirm whether MCD can return those specific cartons to an authorized commercial prep facility for external repacking. Amazon staff says AWD does not offer internal carton splitting or repacking. Obtain separate approval for the destination, fees, removal and repacking before proceeding.
5. After the underlying issue is corrected, verify the next replenishment attempt rather than repeatedly creating test orders or marking the error fixed prematurely.

## Verify

Read the exact order in Shipments, orders and replenishments. Verify the intended SKU and quantity, a progressing order status and any generated shipment identifiers; check carrier or receiving evidence before claiming dispatch or delivery. The automated error may remain until a successful replenishment attempt. A confirmed request followed by Failure is not a successful shipment.

## Stop before

Stop before a support send, new move request, packing-data change, removal, return destination, repacking charge or replenishment-setting change unless the operator approved that exact action. Do not mark the error fixed while the underlying issue remains unresolved.

## Sources

- First-party: [AWD Choose inventory to send](https://sellercentral.amazon.com/help/hub/reference/GZLL7RYU2FJRN9BU), current box rule read in attended US Seller Central; [older Amazon staff explanation](https://sellercentral.amazon.com/seller-forums/discussions/t/6ac573ad-3f26-44c8-a6fe-29ba851701c1) shows the rule predates the observed error. No local rule capture yet.
- First-party: [Amazon staff on existing inventory and external repacking](https://sellercentral.amazon.com/seller-forums/discussions/t/d226bc69-ab21-48c0-ae56-1cb3e94a3622); [support correction and escalation precedent](https://sellercentral.amazon.com/seller-forums/discussions/t/2afaf9f8-f3c1-4b96-b7d5-6deb317ce5cb), without a verified successful-transfer outcome.
- First-party: [AWD Service Terms, returns section](https://supplychain.amazon.com/legal/service-terms/warehouse-and-distribution); [MCD Help](https://sellercentral.amazon.com/help/hub/reference/GEPTXX9PMMXUKMK9), commercial return destinations and external unit-level services.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

The failure and current diagnosis were observed live, but the remedy has not been verified end to end. The exact rule introduction date, any change in enforcement, grandfathering, an approved exception, and MCD acceptance of particular over-limit cartons remain unverified. The 150-unit rule here is AWD-specific, not a universal claim about every FBA packing method. This unit remains draft and unverified pending human review and a completed remedy.
