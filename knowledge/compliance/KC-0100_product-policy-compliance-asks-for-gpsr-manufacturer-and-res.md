---
id: KC-0100
title: "Product policy compliance asks for GPSR manufacturer and responsible person details on EU listings"
kind: rule
topic: compliance
status: reviewed
skills: [amazon-regulated-product-appeals, amazon-catalog]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central > Account Health > Product policy compliance > Regulatory compliance"
surface_verified: false
symptom_keywords: ["GPSR manufacturer contact details", "GPSR responsible person", "EU regulatory compliance missing info", "GPSR warning and safety information", "GPSR needed on US"]
error_text: ["GPSR: manufacturer contact details", "GPSR: Responsible Person contact details", "GPSR: warning and safety information"]
asked_as: ["The regulatory compliance tab on the EU account listed many SKUs needing GPSR manufacturer contact details, responsible person contact details, warning and safety information, and certificates; the su"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md", "Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-product-document-upload.md"]
supersedes: []
contradicts: []
observed: 2024-09
review_by: 2027-10
provenance: "ledger:KC-0100"
---

## Question

The regulatory compliance tab on the EU account listed many SKUs needing GPSR manufacturer contact details, responsible person contact details, warning and safety information, and certificates; the supplier asked whether the US listings needed the same.

## Answer

The EU regulatory compliance tab asks per SKU for manufacturer contact details, Responsible Person contact details, and warning and safety information. The Responsible Person must be established in the EU, so a contact at a non-EU factory does not qualify. Collect the details per SKU from the supplier, and do not copy GPSR fields to US listings, which the agency treated as not needed.

## Cause

EU product safety rules require manufacturer contact details, a Responsible Person established in the EU, and warning and safety information for products sold in the EU, so the EU regulatory compliance tab asks for them per SKU. Only the agency, not an Amazon source, said the US listings do not need them.

## Fix

1. Open Account Health > Product policy compliance > Regulatory compliance on the EU marketplace and list each SKU and missing attribute.
2. Collect from the supplier, per SKU, the manufacturer contact details, the Responsible Person contact details, the warning and safety information and the certificates.
3. Check that the Responsible Person is established in the EU (EU manufacturer or brand, EU importer, appointed EU authorised representative, or EU fulfilment service provider); a contact outside the EU cannot fill that role. Keep the producer in the manufacturer fields.
4. Enter the details per SKU on the EU marketplace; do not add GPSR fields to US listings.

## Verify

The regulatory compliance tab no longer lists the SKUs with missing GPSR attributes.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/200-sell-globally-experience-faq-GNFDSYQP7TR7SPUW.md`
- First-party: `Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md`
- Also in: `MAG SOPs/catalog/catalog-sop-product-document-upload.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Lists the three GPSR attributes the EU regulatory compliance tab asks for and that US listings do not need them.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/201-compliance-services-store-G5XSKWYY7BWDMS4V.md`, `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`, `sop-drafts/2026-06-07_daily-amazon-account-health-check.md`).
