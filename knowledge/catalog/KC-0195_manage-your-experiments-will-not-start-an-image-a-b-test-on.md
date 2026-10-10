---
id: KC-0195
title: "Manage Your Experiments will not start an image A/B test on a new main image: the ASIN lacks enough traffic"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-listing-images, amazon-catalog]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central Brands > Manage Your Experiments"
surface_verified: false
symptom_keywords: ["cannot start A/B test low traffic", "Manage Your Experiments not eligible", "split test main image not available", "MYE traffic requirement", "ASIN not eligible for experiment"]
error_text: []
asked_as: ["After a new main image was accepted on a multipack listing, the brand owner wanted to split-test it against the old one but could not, because the ASIN did not have enough traffic."]
synonyms: []
resolution_status: diagnosis-only
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md"]
supersedes: []
contradicts: []
observed: 2025-07
review_by: 2027-10
provenance: "ledger:KC-0195"
---

## Question

After a new main image was accepted on a multipack listing, the brand owner wanted to split-test it against the old one but could not, because the ASIN did not have enough traffic.

## Answer

Manage Your Experiments only runs on brand ASINs that have had enough traffic in recent weeks, so a low-traffic listing cannot be A/B tested there. Drive traffic with ads before testing, and treat any exact view threshold as unverified, since Amazon states none.

## Cause

Manage Your Experiments only allows experiments on brand ASINs with enough recent traffic; low-traffic ASINs show as ineligible or do not appear at all. Amazon's page gives no fixed view threshold, only that high-traffic ASINs may get several dozen orders per week depending on the category; any specific threshold quoted elsewhere is unverified.

## Fix

1. Open Brands > Manage Your Experiments and check the ASIN's eligibility status.
2. If it is ineligible, build traffic first, for example with advertising, then check again.
3. Meanwhile, consider publishing the stronger image directly and comparing performance before and after (agency suggestion, not from the thread or Amazon's page).
4. Re-check eligibility after traffic grows and start the experiment then.

## Verify

The ASIN shows as eligible in Manage Your Experiments and the experiment can be created.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`
- Also in: `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links a blocked main-image A/B test to MYE traffic eligibility and flags the commonly quoted view threshold as unverified against Amazon's page.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `Amazon Seller Help/articles/075-manage-your-experiments-GVP453K5XRBJS7Y9.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-a-content.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`).
