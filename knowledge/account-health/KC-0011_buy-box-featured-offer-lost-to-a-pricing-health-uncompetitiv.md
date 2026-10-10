---
id: KC-0011
title: "Buy Box (Featured Offer) lost to a Pricing Health 'uncompetitive price' flag; restored by pricing at or below Amazon's competitive-price threshold"
kind: diagnosis
topic: account-health
status: draft
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > Pricing > Pricing Health (Featured Offer eligibility); detail page Buy Box"
surface_verified: true
symptom_keywords: ["lost buy box no other seller", "uncompetitive price flag", "featured offer ineligible", "pricing health competitive price threshold", "buy box gone after pricing email"]
error_text: ["uncompetitive price"]
asked_as: ["The listing had lost the Buy Box and the client had received Amazon's pricing email."]
synonyms: ["Buy Box verloren", "Featured Offer", "Pricing Health"]
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0011"
---

## Question

The listing had lost the Buy Box and the client had received Amazon's pricing email. After a price reduction the Buy Box came back, and the client asked to test and monitor sales at the new price.

## Answer

If a Buy Box disappears and no other seller holds it, check Pricing Health before suspecting hijackers or account health. An 'uncompetitive price' flag removes Featured Offer eligibility, and Amazon shows the threshold to beat. Price at or below it, and check external channels, because a cheaper price off Amazon can trigger the flag.

## Cause

Amazon withdrew the offer's Featured Offer eligibility under Pricing Health with an 'uncompetitive price' flag, because the price was above the competitive-price threshold Amazon displayed. The agency also noted that Amazon compares prices on other marketplaces, so a cheaper external price can cost the Buy Box.

## Fix

1. Open Pricing Health and confirm the offer is listed as ineligible for the Featured Offer with an uncompetitive-price reason.
2. Read the competitive-price threshold Amazon shows for that offer.
3. Lower the price to the threshold or below. Price changes need operator approval.
4. Check that the Buy Box (Featured Offer) is back on the detail page.
5. Monitor sales and margin at the new price, and check external channels (other marketplaces, the brand's own site) for a lower price that may set the reference.

## Verify

The Buy Box returned after the price change and the client confirmed. No later message confirms that it held.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: It adds a diagnostic order: the 'uncompetitive price' flag with its displayed threshold as the first check for a lost Buy Box, and pricing to that threshold.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-managing-your-buy-box-percentage.md`, a MAG SOP dropped on 08.10.2026, a MAG SOP dropped on 08.10.2026).
