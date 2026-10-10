---
id: KC-0097
title: "Which entity to name as the GPSR responsible person when the products are made outside the EU and imported by the seller"
kind: rule
topic: compliance
status: reviewed
skills: [amazon-account-health-check, amazon-catalog, amazon-regulated-product-appeals]
marketplaces: [DE]
marketplace_inferred: true
surface: "Seller Central > listing GPSR / product safety attributes (responsible person)"
surface_verified: false
symptom_keywords: ["GPSR responsible person producer or importer", "which company to enter as EU responsible person", "listings at risk of removal GPSR responsible person", "manufacturer outside EU GPSR contact"]
error_text: []
asked_as: ["Listings were flagged as at risk of removal for GPSR information."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md", "Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0097"
---

## Question

Listings were flagged as at risk of removal for GPSR information. The seller had first entered the non-EU producer as the responsible party and asked whether its own EU company, which imports the goods, should be selected instead.

## Answer

When products are made outside the EU, the foreign producer cannot serve as the EU responsible person. Name an EU-established party instead: the EU importer, an authorised representative appointed in writing, or an EU fulfilment service provider. A seller whose own EU company imports the goods can enter itself.

## Cause

The thread does not show the Amazon notice. Amazon's Sell Globally FAQ lists who can be the EU Responsible Person: the manufacturer or brand if established in the EU, an importer established in the EU, an authorised representative appointed in writing, or a fulfilment service provider established in the EU. A producer outside the EU is none of these, so naming it alone likely leaves the listing without a valid EU responsible person.

## Fix

1. Identify an EU-established party that qualifies: the manufacturer or brand if based in the EU, the EU importer, an authorised representative appointed in writing, or an EU fulfilment service provider.
2. When the producer is outside the EU and the seller's own EU company imports the goods, enter that EU company as the responsible person in the listing's product safety attributes (listing change: operator approval).
3. If the form has separate manufacturer fields, keep the producer there; the thread does not show the form layout.
4. Recheck the at-risk listings in Account Health once the attributes are saved.

## Verify

The at-risk-of-removal flag clears for the listings after the responsible-person attribute names the EU importer. Not confirmed in the thread.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`
- First-party: `Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No local unit or first-party capture says which entity to enter as the GPSR responsible person when the producer is outside the EU; the Compliance Services Store page only names the RsP service.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`, `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md`, `Amazon Seller Help/articles/199-sell-globally-experience-GDYZBUHVDD66VHVR.md`).
