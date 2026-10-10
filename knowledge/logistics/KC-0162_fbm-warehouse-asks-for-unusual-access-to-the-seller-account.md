---
id: KC-0162
title: "FBM warehouse asks for unusual access to the seller account: connect it through an integration, the API or a limited secondary user"
kind: procedure
topic: logistics
status: reviewed
skills: [amazon-logistics]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["connect warehouse to Amazon for FBM", "give fulfilment warehouse access to Seller Central", "warehouse needs account login", "secondary user permissions for warehouse", "FBM warehouse integration"]
error_text: []
asked_as: ["A new fulfilment warehouse for merchant-fulfilled orders asked the client for a kind of access to the Amazon account that the thread does not quote, and the client asked the agency whether that was re"]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md"]
supersedes: []
contradicts: []
observed: 2025-06
review_by: 2027-10
provenance: "ledger:KC-0162"
---

## Question

A new fulfilment warehouse for merchant-fulfilled orders asked the client for a kind of access to the Amazon account that the thread does not quote, and the client asked the agency whether that was really needed.

## Answer

Connect an FBM warehouse through a pre-built integration, the Selling Partner API or a secondary Seller Central user with only the order rights it needs; never hand over the main account. The warehouse only has to confirm shipments and upload tracking. Share the SKU list and naming logic with it before go-live so it picks the right item for every order.

## Cause

Not a fault. The thread does not quote the warehouse's request; the agency judged it was not a standard way to connect a warehouse. A fulfilment warehouse only needs to read orders, confirm shipment and upload tracking numbers, which standard connection routes cover without handing over the main account.

## Fix

1. Ask the warehouse which of the standard routes it supports: a pre-built connector or integration platform, a Selling Partner API connection, or a secondary user in Seller Central.
2. If it uses a secondary user, invite it through Settings > User Permissions and grant only the order-management rights needed to confirm shipments and upload tracking (invitation needs operator approval).
3. Never share the primary account login with the warehouse.
4. Send the warehouse the SKU list with an explanation of the SKU naming system, so it can map each SKU to the right physical item.
5. Test with one order that the warehouse can confirm shipment and that the tracking number appears on the order.

## Verify

A test order shows Shipped with the warehouse's tracking number, and the warehouse user has no rights beyond order management.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- Also in: `MAG SOPs/catalog/catalog-sop-fbm-late-shipment.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the three safe ways to connect an FBM warehouse and the least-privilege rule for a warehouse user.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-amazon-damaged-and-lost-inventory-reimbursements.md`).
