---
id: KC-0085
title: "Pesticide device listing needs an EPA number and a long regulatory disclaimer: which pesticide attribute to choose and where the disclaimer fits"
kind: procedure
topic: compliance
status: reviewed
skills: [amazon-regulated-product-appeals, amazon-seo]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Edit listing > compliance attributes (Pesticide Marking, Pesticide Registration Status); A+ Content; Product Description"
surface_verified: false
symptom_keywords: ["pesticide device EPA establishment number", "pesticide marking attribute", "UV sanitizer listing EPA disclaimer", "EPA registration vs establishment number amazon", "where to put a long disclaimer on a listing"]
error_text: []
asked_as: ["The client had to add a long regulatory disclaimer (pesticidal device under EPA rules, not an FDA-cleared medical device) to a UV sanitizing device listing before it could go back live, and asked for "]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0085"
---

## Question

The client had to add a long regulatory disclaimer (pesticidal device under EPA rules, not an FDA-cleared medical device) to a UV sanitizing device listing before it could go back live, and asked for a discreet place for it. While editing, the listing would not save until the type of EPA number was chosen, and the number on the client's certificate differed from the one Amazon showed.

## Answer

For a pesticide device such as a UV sanitizer that is not itself a registered pesticide, choose EPA Establishment Number as the Pesticide Marking type and the FIFRA pesticide-or-device option as the registration status. Confirm the exact number against the product label before saving, since an older number may be on file. Put a long regulatory disclaimer in A+ Content, an image or the description, because it does not fit title or bullets.

## Cause

The product is a pesticidal device, so Amazon requires the Pesticide Marking attribute and a Pesticide Registration Status. A device that is not itself a registered pesticide is identified by the EPA Establishment number of the producing facility, not an EPA Registration number. The disclaimer was too long for title or bullet fields.

## Fix

1. Place the long regulatory disclaimer in A+ Content, a listing image or the Product Description; it does not fit title or bullet limits.
2. In the listing's compliance attributes set Pesticide Registration Status to "This product is a pesticide or pesticide device, as defined under the U.S. Federal Insecticide, Fungicide, and Rodenticide Act".
3. Set the Pesticide Marking type to EPA Establishment Number when the client holds an establishment number rather than a registration number.
4. Confirm the exact number with the client against the label or certificate, because the number already on file may be out of date, and enter it.
5. Save; the attribute block cannot be saved until a marking type is chosen.

## Verify

The listing edit saves without attribute errors and the listing shows the establishment number in its compliance attributes.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Choosing EPA Establishment Number (not Registration Number) for an unregistered pesticide device, and placing a long regulatory disclaimer in A+, images or description.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
