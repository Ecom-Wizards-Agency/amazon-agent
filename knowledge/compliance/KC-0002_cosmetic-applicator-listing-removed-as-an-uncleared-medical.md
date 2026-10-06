---
id: KC-0002
title: "Cosmetic applicator listing removed as an uncleared medical device because of skin-infusion marketing language"
kind: diagnosis
topic: compliance
status: draft
skills: [amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Account Health > Restricted Product Policy Violations; listing content (title, bullets, backend search terms, images); appeal"
surface_verified: false
symptom_keywords: ["listing removed medical device", "can't find listing not even inactive", "510(k) required cosmetic tool", "restricted product policy violation applicator", "micro-infusion claim removed"]
error_text: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-fix-medical-devices-and-accessories-yanks.md", "MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md"]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0002"
---

## Question

The client could no longer find their listing anywhere in Seller Central, not even as inactive, and asked whether they were off Amazon. An FBM offer had been removed under the same policy as the FBA offer.

## Answer

A cosmetic tool can be reclassified as a medical device by its marketing language as much as by its mechanism. Wording about delivering ingredients into the skin (infusion, micro-infusion, needling-style or penetration claims) on a stamping or needle-like applicator triggers the FDA 510(k) requirement. Without a 510(k), remove every such term from all listing fields, including backend search terms, A+ and images, confirm each field changed, then appeal with packaging photos. Expect lower odds when the packaging itself carries the claims; the fix may then need repackaged inventory or a new ASIN.

## Cause

Amazon classified a cosmetic serum applicator (a stamp with ultra-thin applicators) as a medical device that needs FDA 510(k) clearance. The trigger was the delivery mechanism combined with listing claims: infusion-style wording, use on face, neck and lips, and active-ingredient language. The agency's reading was that the wording drove the classification; this was not confirmed by Amazon.

## Fix

1. Read the full violation reason in Account Health. It lists the technical-characteristics trigger and quotes the flagged marketing phrases from the listing.
2. If the product has a 510(k) clearance, take the cleared route (packaging photos, IFU photos, 510(k) number). If it has none, take the non-device route: remove the flagged terms from title, bullets, description, backend search terms, A+ and images, and name the tool neutrally ('applicator', not a term that overstates what it does). Listing changes need operator approval.
3. Push the content change and confirm every field actually changed (feed batch ID or a live re-read). In this case the backend search-terms update did not take at first.
4. Upload packaging images and consider removing any image that shows the mechanism or the claims.
5. Submit the appeal from the Restricted Product Policy Violations row once the content is clean. The appeal needs operator approval.

## Verify

Not verified. The appeal was still pending when the thread ended and the backend update had not taken. The only success evidence is an earlier DE case reinstated after rewording plus a packaging image.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-medical-devices-and-accessories-yanks.md`
- Also in: `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Infusion-style wording as a specific trigger term and the warning that claims printed on the packaging lower appeal odds are not in the existing SOP.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-how-to-fix-medical-devices-and-accessories-yanks.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`).
