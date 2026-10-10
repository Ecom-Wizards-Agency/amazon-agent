---
id: KC-0168
title: "Who pays Canadian taxes on sales fulfilled through Remote Fulfillment with FBA, and what is unconfirmed for Mexico"
kind: rule
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US, CA, MX]
marketplace_inferred: false
surface: "Remote Fulfillment with FBA (NARF)"
surface_verified: false
symptom_keywords: ["Remote Fulfillment taxes Canada", "NARF GST HST", "do I need to register for GST Remote Fulfillment", "Mexico taxes Remote Fulfillment", "cross-border FBA tax responsibility"]
error_text: []
asked_as: ["A client asked how to treat the tax situation for Canada and Mexico sales when US inventory serves those marketplaces."]
synonyms: []
resolution_status: resolved
fix_source: first-party-doc
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/202-expand-to-canada-with-panamericas-GL29MXM9KNN7WLJV.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-unenroll-from-the-remote-fulfillment-program-narf.md"]
supersedes: []
contradicts: []
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0168"
---

## Question

A client asked how to treat the tax situation for Canada and Mexico sales when US inventory serves those marketplaces.

## Answer

If US inventory serves Canada through Remote Fulfillment with FBA, Amazon's own comparison lists cross-border logistics as handled by Amazon, which collects and remits taxes on your behalf. That changes once inventory is stored in Canada, for example through PanAmericas or in-country FBA. For Mexico, and for any registration question, no local Amazon page settles it. Amazon's pages say they are not tax advice, so refer those questions to a tax advisor.

## Cause

Under Remote Fulfillment with FBA, Amazon ships from US fulfillment centers and handles the cross-border logistics. For Canada, Amazon's PanAmericas comparison table lists Remote Fulfillment cross-border logistics as 'Amazon (collects remits taxes on your behalf)'. The thread relayed an unattributed text saying customers act as importer of record, which the capture does not state. No local capture covers Mexico or says whether Remote Fulfillment sales alone avoid a local tax registration.

## Fix

1. Confirm the products are enrolled in Remote Fulfillment with FBA for the destination marketplace.
2. For Canada orders fulfilled through Remote Fulfillment, Amazon collects and remits the taxes; for Mexico, confirm the tax treatment with a tax advisor.
3. Revisit tax registration before moving inventory into the destination country (for example through PanAmericas or in-country FBA), and refer specific questions to a tax advisor.

## Verify

The Remote Fulfillment enrollment shows the products as active for the destination marketplace.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/202-expand-to-canada-with-panamericas-GL29MXM9KNN7WLJV.md`
- Also in: `MAG SOPs/catalog/catalog-sop-unenroll-from-the-remote-fulfillment-program-narf.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The PanAmericas page states Amazon collects and remits taxes for Remote Fulfillment; the card turns that into a direct answer to the seller tax-registration question for Canada and Mexico.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-unenroll-from-the-remote-fulfillment-program-narf.md`, `Amazon Seller Help/articles/202-expand-to-canada-with-panamericas-GL29MXM9KNN7WLJV.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`, `Amazon Seller Help/articles/184-registration-requirements-by-store-G201468460.md`).
