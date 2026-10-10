---
id: KC-0086
title: "New EU store listings held until an EPR number, EU responsible person, manufacturer details and SDS are supplied; another product type needs its own EPR number"
kind: procedure
topic: compliance
status: reviewed
skills: [amazon-regulated-product-appeals, amazon-catalog, amazon-client-onboarding]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central (EU) > listing compliance information; Settings > User Permissions"
surface_verified: false
symptom_keywords: ["[\"EPR number amazon germany\", \"EU responsible person listing\", \"compliance release before shipment\", \"different EPR number per product\"]"]
error_text: []
asked_as: ["A brand expanding from the US store to the German store needed its listings created and shipping labels issued."]
synonyms: []
resolution_status: partial
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md", "Amazon Seller Help/articles/199-sell-globally-experience-GDYZBUHVDD66VHVR.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0086"
---

## Question

A brand expanding from the US store to the German store needed its listings created and shipping labels issued. First the listing-service provider's user could not create listings in the new marketplace; once access worked, the listings could not be activated until Amazon received EU compliance information, and Amazon then asked for a separate EPR number for a second product type.

## Answer

Before opening an EU store, collect the EPR registration number for every product category, the EU Responsible Person, the manufacturer details and the SDS, because the listings stayed unreleased and unshippable until these were on file. Amazon can ask for a separate EPR number for a different product type, so check categories early or launch that type later.

## Cause

EU listings were held until product compliance information was on file: an EPR registration number, an EU Responsible Person, manufacturer details and safety documentation. Amazon would not reuse the EPR number given for one product type on another type; the thread does not say which EPR category applied. Amazon's Sell Globally pages say EPR is implemented per country and that electrical products also need a WEEE registration, which fits but does not establish a per-type rule.

## Fix

1. ["1. Before launch, collect the EPR registration number for each applicable category, the EU Responsible Person name and address, the manufacturer name and address, the SDS and the user manual.", "2. Upload them to each listing's compliance information and wait for the compliance release; listings can be released one at a time.", "3. Ship the released listings first if the launch cannot wait for all of them.", "4. When Amazon asks for a different EPR number for another product type, obtain that registration or keep the listing deactivated."]

## Verify

Each listing shows as released for sale and shipment creation is possible for it.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`
- First-party: `Amazon Seller Help/articles/199-sell-globally-experience-GDYZBUHVDD66VHVR.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: EU listing release needs EPR, Responsible Person, manufacturer and SDS on file, and Amazon may demand a separate EPR number for another product type; secondary-user verification can block listing permissions in a new marketplace.
- Existing coverage: partial (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/199-sell-globally-experience-GDYZBUHVDD66VHVR.md`, `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`).
