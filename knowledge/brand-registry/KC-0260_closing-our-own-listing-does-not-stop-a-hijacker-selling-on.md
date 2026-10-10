---
id: KC-0260
title: "Closing our own listing does not stop a hijacker selling on the same ASIN"
kind: rule
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["close listing to stop hijacker", "shut down listing hijacker", "hijacker keeps selling after closing listing", "pause listing while waiting for trademark", "trademark pending hijacker losing money"]
error_text: []
asked_as: ["With a hijacker on the listing, sales falling and a high refund rate, the brand owner asked whether temporarily shutting down the listing was the best option while waiting months for a trademark."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md"]
supersedes: []
contradicts: []
observed: 2026-06
review_by: 2027-10
provenance: "ledger:KC-0260"
---

## Question

With a hijacker on the listing, sales falling and a high refund rate, the brand owner asked whether temporarily shutting down the listing was the best option while waiting months for a trademark.

## Answer

Closing your listing only removes your own offer; the ASIN and any hijacker on it stay live, and the hijacker keeps selling. Keep your offer up and work on the actual loss driver, such as a refund problem. Check whether Brand Registry accepts any trademark the brand already holds, including one registered in another country, for that marketplace before waiting out a pending application.

## Cause

Closing or deleting a listing removes only the seller's own offer; the ASIN's detail page stays live and other sellers' offers on it keep selling (MAG delete-listing SOP). Removing a reseller then depends on Brand Registry enforcement. The agency lead held that this needs a registered trademark, and against hijackers Transparency as well; that is the lead's view, not a first-party rule.

## Fix

1. Do not close your own offer to stop a hijacker; it removes only your offer and leaves the reseller as the remaining seller.
2. Diagnose what is actually costing money, such as a refund rate that stays high while sales fall, before deciding to pause.
3. Collect every trademark the brand holds, including registrations in other countries, and check with Brand Registry which one it accepts for the marketplace you sell in. The thread did not establish whether a foreign registration enables enforcement there.
4. Use the accepted trademark for Brand Registry enforcement and, once possible, Transparency.

## Verify

After closing an offer, the detail page still shows remaining sellers' offers; only Brand Registry action or Transparency removes them.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Applies the close-does-not-remove-detail-page rule to the hijacker case and redirects the seller to fixing the refund driver and finding any registered trademark abroad, which the hijacker SOP does not cover.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-download-category-listings-report.md`, `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md`).
