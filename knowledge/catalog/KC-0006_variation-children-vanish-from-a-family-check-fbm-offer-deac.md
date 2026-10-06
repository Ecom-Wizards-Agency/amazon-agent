---
id: KC-0006
title: "Variation children vanish from a family: check FBM offer deactivation for Valid Tracking Rate before fixing images or parentage"
kind: diagnosis
topic: catalog
status: draft
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Account Health > Shipping performance (Valid Tracking Rate); variation family on the detail page"
surface_verified: false
symptom_keywords: ["variation sizes missing", "children disappeared from variation family", "valid tracking rate deactivated FBM", "only some sizes show on listing", "VTR below 95% apparel"]
error_text: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md", "MAG SOPs/catalog/catalog-sop-parentage-check.md"]
supersedes: []
contradicts: []
observed: 2026-09
review_by: 2027-09
provenance: "ledger:KC-0006"
---

## Question

The client asked why a multipack listing showed only some sizes. The other size children had disappeared from the variation family.

## Answer

When some children drop out of a variation family, check first whether their offers are inactive and why, before editing parentage, images or the flat file. FBM offers in a category can be deactivated for a Valid Tracking Rate below 95%, and image fixes or handling-time changes do not reinstate them. Reinstatement needs a plan of action backed by order-level tracking evidence reconciled against the VTR defect report, after the carrier or 3PL process is fixed. Moving the SKUs to FBA removes the VTR dependency.

## Cause

Amazon deactivated the FBM offers for the missing sizes because the Apparel Valid Tracking Rate was below the 95% requirement. Image issues were present but were not the cause. A handling-time change made the week before does not reinstate offers that are already deactivated.

## Fix

1. Check whether the missing children's offers are inactive and read the deactivation reason in Account Health before touching images, parentage or the flat file.
2. If the reason is Valid Tracking Rate, ask the 3PL for the order report through the deactivation date with carrier and service, tracking IDs, pickup scans, and tracking upload timestamps or error logs.
3. Compare it with Amazon's VTR defect report to prepare a plan of action for reinstatement. The appeal needs operator approval.
4. Have the 3PL fix tracking upload before contacting Seller Support or Account Health.
5. Consider moving the affected SKUs to FBA (an interim labelled parcel while the main stock is in transit) to remove the VTR dependency, and reduce ad spend while the children cannot be bought.

## Verify

The diagnosis is confirmed by Amazon's recorded VTR figure in the thread. The reinstatement outcome is not visible; the thread ends on the decision to move to FBA.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md`
- Also in: `MAG SOPs/catalog/catalog-sop-parentage-check.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source links missing sizes in a variation family to an FBM Valid Tracking Rate deactivation or warns that image and handling-time fixes do not reinstate.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-seller-fulfilled-offers-mfn-suspension.md`, `MAG SOPs/catalog/catalog-sop-parentage-check.md`).
