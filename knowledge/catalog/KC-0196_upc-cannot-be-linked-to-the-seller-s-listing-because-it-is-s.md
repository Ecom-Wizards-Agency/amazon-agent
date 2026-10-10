---
id: KC-0196
title: "UPC cannot be linked to the seller's listing because it is still attached to an inactive ASIN: request barcode removal through Seller Support"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central catalog; Seller Support case; account manager escalation"
surface_verified: false
symptom_keywords: ["UPC attached to another ASIN", "cannot link UPC to listing", "barcode on tombstoned ASIN", "remove UPC from old ASIN", "GTIN conflict inactive ASIN"]
error_text: []
asked_as: ["The seller could not attach its own UPC to its live ASIN."]
synonyms: []
resolution_status: partial
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0196"
---

## Question

The seller could not attach its own UPC to its live ASIN. Research showed the UPC was linked to a different, inactive ASIN that the seller never listed, with a registered address in another country, although the seller's brand-protection code records linked the UPC to the right product.

## Answer

If your UPC is stuck on an inactive ASIN you never listed, ask Seller Support to remove the barcode from that ASIN instead of asking for a transfer. Back the request with your GS1 certificate, a screenshot of the conflict and real photos of the printed barcode on the package. Expect the first team to decline or misroute it; in the thread an Amazon account manager pushed back that the ASIN was tombstoned before the removal went through, so sellers without one may need repeated escalation.

## Cause

The UPC was still associated with another catalog ASIN that was inactive and later tombstoned, which prevented the GTIN from being attached to the seller's ASIN. The seller had not caused it. Amazon teams initially said a UPC cannot be transferred between ASINs.

## Fix

1. ["1. Confirm the conflict: find which ASIN holds the UPC, its status and the brand or address on it, and screenshot it.", "2. Gather proof of ownership: the GS1 certificate and high-resolution photos of the physical package showing the printed barcode, the brand name and key product details (no mockups).", "3. Open a Seller Support case asking to remove the UPC from the conflicting ASIN; explain briefly why that ASIN carries the UPC although it is not in your inventory and attach the screenshots. Operator approval is required before sending.", "4. If you have an Amazon account manager, give them the case ID so they can route it to the team handling GTIN corrections; the first team reached may say it is out of scope.", "5. If the reply says the UPC cannot be transferred, push back (in the thread the account manager did this) that the conflicting ASIN is inactive or tombstoned and ask only for removal.", "6. After removal, attach the UPC to your ASIN and report any error."]

## Verify

Amazon confirms the barcode was removed from the conflicting ASIN and the UPC attaches to the seller's ASIN without an error.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The UPC SOPs cover changing a UPC, not removing a seller-owned UPC from an inactive ASIN through a Seller Support removal request.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-how-to-merge-asins.md`, `MAG SOPs/README.md`).
