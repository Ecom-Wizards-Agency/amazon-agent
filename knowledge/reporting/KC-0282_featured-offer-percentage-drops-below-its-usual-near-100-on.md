---
id: KC-0282
title: "Featured Offer percentage drops below its usual near-100% on a brand's own catalog: one ASIN lost the Featured Offer"
kind: diagnosis
topic: reporting
status: reviewed
skills: [amazon-reporting, amazon-troubleshooting]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Featured Offer % metric (dashboard)"
surface_verified: false
symptom_keywords: ["Featured Offer percentage dropped", "buy box percentage low", "Featured Offer % never this low", "account buy box percentage down"]
error_text: ["Featured Offer %"]
asked_as: ["The brand owner noticed the account's Featured Offer % at its lowest ever and asked whether it would hurt performance and whether the price of two variants should be aligned with the main SKU."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/137-featured-offer-G37911.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md", knowledge/account-health/KC-0011_buy-box-featured-offer-lost-to-a-pricing-health-uncompetitiv.md]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0282"
---

## Question

The brand owner noticed the account's Featured Offer % at its lowest ever and asked whether it would hurt performance and whether the price of two variants should be aligned with the main SKU.

## Answer

On a catalog where you are the only seller, a drop in Featured Offer % usually means one or more ASINs lost the Featured Offer, not an account-wide problem. Find the ASINs with a low per-ASIN figure and fix their pricing or availability. Do not keep repricing to chase the account-level number after the cause is fixed, because the figure can trail the fix.

## Cause

Featured Offer percentage is page views on which the seller holds the Featured Offer divided by all page views of the products it lists. One ASIN had lost the Featured Offer for a while (a pricing issue that was already being handled), which pulled the account-level figure down; the agency judged the reported value to lag behind the fix.

## Fix

1. Find which ASINs are not winning the Featured Offer, for example via a Business Report by child ASIN with Featured Offer percentage.
2. Fix the cause on those ASINs (price, availability, eligibility).
3. Once that cause is fixed, do not make further price changes just to lift the account-level figure; the agency judged that the reported figure lags behind the fix.
4. Recheck the metric over the following days.

## Verify

The account-level Featured Offer % returns to its usual level once the affected ASIN wins the Featured Offer again.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/137-featured-offer-G37911.md`
- Also in: `MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`
- Also in: `knowledge/account-health/KC-0011_buy-box-featured-offer-lost-to-a-pricing-health-uncompetitiv.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: KC-0011 covers losing the Featured Offer to a pricing flag; this adds reading the account-level Featured Offer % as a page-view-weighted aggregate that one ASIN can pull down, and not repricing unaffected variants.
- Existing coverage: partial (`knowledge/account-health/KC-0011_buy-box-featured-offer-lost-to-a-pricing-health-uncompetitiv.md`, `MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`, `Amazon Seller Help/articles/137-featured-offer-G37911.md`, `MAG SOPs/catalog/catalog-sop-high-odr-account-suspension.md`).
