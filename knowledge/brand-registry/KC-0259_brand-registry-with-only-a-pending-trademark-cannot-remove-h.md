---
id: KC-0259
title: "Brand Registry with only a pending trademark cannot remove hijackers from a listing"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["hijackers pending trademark", "brand registry useless against hijackers", "cannot remove resellers from listing", "need transparency to stop hijackers", "pending trademark brand registry enforcement"]
error_text: []
asked_as: ["The brand owner asked whether being in Brand Registry without a registered trademark is useless against hijackers on their listing."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md", "Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md"]
supersedes: []
contradicts: ["Amazon Seller Help/articles/225-report-alleged-trademark-infringements-via-common-law-GS45XXXQDNDP9MJU.md"]
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0259"
---

## Question

The brand owner asked whether being in Brand Registry without a registered trademark is useless against hijackers on their listing.

## Answer

Brand Registry on a pending trademark gives limited leverage against hijackers. Standard trademark reports need a registered mark, and only the US, Canada and South Africa allow a common-law report backed by a test buy. Even with a registered mark, a report only removes infringing or counterfeit offers, and a reseller of genuine units can stay or come back. The durable protection is Transparency, which needs a registered trademark and stops units without a valid code, so prioritise the registration and then enrol.

## Cause

Report a Violation trademark reports generally need a registered trademark; Amazon says you cannot submit them for pending trademarks. In the US, Canada and South Africa, Rights Owners and Registered Agents can instead file common-law trademark reports, which require a test buy and proof of first use. Even a successful report only removes an offer that infringes. A reseller of genuine units is not infringing, and a seller who answers a report with documents may return. Transparency, which the Transparency SOP says requires a government-registered trademark, blocks units without a valid code.

## Fix

1. Check whether the brand's trademark is registered or still pending at the trademark office the Brand Registry enrolment uses.
2. If it is only pending, do not count on standard Report a Violation trademark reports. In the US, CA and ZA stores, a common-law report is possible after a test buy that shows the trademark on the unit. Pursue the registration in parallel.
3. Once the trademark is registered, enrol the products in Transparency so units without a valid code cannot be sold on the ASIN.
4. Until then, report an offer only where a test buy shows it is counterfeit or infringing, never just because another seller is on the listing (operator approval needed before submitting).

## Verify

After Transparency activation, check the offer listing for the ASIN: other sellers' offers should disappear or stop being fulfilled because their units carry no valid code.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/229-protect-your-brand-with-transparency-GSB2AVC33KWCAYSA.md`
- First-party: `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`
- Also in: `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties hijacker removal limits to pending versus registered trademark status and names Transparency as the only durable block, which the SOPs cover separately but never connect.
- Existing coverage: full (`Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`).
