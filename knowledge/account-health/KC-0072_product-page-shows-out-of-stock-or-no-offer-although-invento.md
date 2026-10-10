---
id: KC-0072
title: "Product page shows out of stock or no offer although inventory exists: check the marketplace listing status for vacation mode, even if it was switched back to active before"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health; Performance Notifications; Settings > Account Info > Listing status"
surface_verified: false
symptom_keywords: ["shows out of stock but we have stock", "offer not live front end", "listing not buyable with inventory", "account re-verification listings inactive", "vacation mode turned on again"]
error_text: []
asked_as: ["A brand saw its product page showing out of stock on Amazon while Seller Central showed sellable inventory, and asked why the offer was not live."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/028-manage-account-settings-G69035.md", "Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md", "Amazon Seller Help/articles/167-micro-deposit-verification-faq-G3VMLXD2ZL3V47JC.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0072"
---

## Question

A brand saw its product page showing out of stock on Amazon while Seller Central showed sellable inventory, and asked why the offer was not live.

## Answer

When an offer shows out of stock despite sellable inventory, check the marketplace listing status for vacation mode first, and check it again even if someone already switched it off, because it can be found in vacation mode again. Also clear any open verification requests and policy items in Account Health, but do not assume they caused the missing offer: in this case the offer returned only when the listing status was set back to active.

## Cause

The marketplace listing status was set to vacation mode, which sets listings to Inactive; the offer returned minutes after it was switched back to active. Why vacation mode was on again, after being turned off earlier, is not established. A seller re-verification request, a bank deposit method verification and a pending product policy item were open at the same time, but the thread does not show that any of them suppressed the offer, and the cited captures do not say that verification requests deactivate offers.

## Fix

1. Open Settings > Account Info > Listing status and check every marketplace; set the affected marketplace back to active if it shows vacation mode (operator approval required).
2. Open Performance Notifications and Account Health, including the product policies view, and list every open verification or policy item.
3. Complete any seller verification or bank deposit method verification the account owner is asked for; if the verification page shows everything verified, ask support which item is open.
4. Respond to any pending product policy item with the requested documents and wait for evaluation.
5. Recheck the product page and the offer status after each fix, and check the listing status again if the offer is still missing.

## Verify

The product page shows a buyable offer for the marketplace and Seller Central no longer lists open verification items; in the thread the offer returned right after the listing status was set back to active.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/028-manage-account-settings-G69035.md`
- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- First-party: `Amazon Seller Help/articles/167-micro-deposit-verification-faq-G3VMLXD2ZL3V47JC.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a combined checklist for an out-of-stock offer with sellable inventory: seller re-verification, bank deposit verification, pending policy items and a listing status that can flip back to vacation mode.
- Existing coverage: full (`knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
