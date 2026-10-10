---
id: KC-0188
title: "Do FBA shipping cartons need their own case-level GTIN barcode?"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: "Send to Amazon (box labels step)"
surface_verified: false
symptom_keywords: ["carton GTIN for FBA", "case barcode on outer box", "what to print on cartons to Amazon", "FBA box requirements", "case level GTIN inbound"]
error_text: []
asked_as: ["A client contact asked which information must be printed on the outer cartons sent to Amazon, assuming each carton needs a case-level GTIN that reflects the units inside so the fulfillment center can "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md"]
related_sops: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
supersedes: []
contradicts: ["MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md"]
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0188"
---

## Question

A client contact asked which information must be printed on the outer cartons sent to Amazon, assuming each carton needs a case-level GTIN that reflects the units inside so the fulfillment center can scan the case in.

## Answer

Cartons going to FBA do not need a case-level GTIN. Each unit needs its own barcode, and each carton needs the box label printed from Send to Amazon. The Send to Amazon SOP gives 50 lb as the standard box weight limit, with Team Lift or Mech Lift labels only for a single oversize unit above that. The thread quoted 60 lb, so take the current limit from Amazon's shipping requirements, not from memory.

## Cause

FBA receives cartons by the box label printed in the Send to Amazon workflow and identifies units by their own unit-level barcode, so a case-level GTIN on the carton is not part of the inbound requirement. The agency stated the box weight limit as 60 lb; the Send to Amazon SOP states 50 lb standard.

## Fix

1. Make sure every sellable unit carries its unit-level barcode (manufacturer barcode or FNSKU label, as the listing requires).
2. Pack the cartons within Amazon's box size and weight limits; check the current limit in the Send to Amazon SOP and the FBA shipping requirements, not from memory.
3. Print the box labels in Send to Amazon after accepting the shipment and attach one to each carton.
4. Do not add a separate case-level GTIN to the carton for FBA intake; it is not required.

## Verify

The Send to Amazon workflow accepts the box contents and prints a label for every box; cartons check in at the fulfillment center without a case-level barcode.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/062-fba-policies-and-requirements-G201030350.md`
- Also in: `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: States plainly that FBA cartons need only the Send to Amazon box label and unit barcodes, never a case-level GTIN, and flags a weight-limit figure that conflicts with the SOP.
- Existing coverage: partial (`knowledge/support-cases/KC-0008_dispute-invalid-fba-inbound-labeling-required-defects-one-ca.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `MAG SOPs/catalog/catalog-sop-how-to-request-gtin-exemption.md`, `MAG SOPs/catalog/catalog-sop-update-fba-weight-and-dimension-cubiscan.md`, `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`).
