---
id: KC-0068
title: "Seller identity document and utility bill rejected because they are not in an accepted language"
kind: rule
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central identity and address verification"
surface_verified: false
symptom_keywords: ["ID rejected twice no reason", "identity document rejected language", "non-Latin ID rejected Amazon", "phone bill rejected proof of address", "verification document not accepted language"]
error_text: []
asked_as: ["The national ID was rejected twice with no detailed reason even though every field matched."]
synonyms: []
resolution_status: partial
fix_source: amazon-support
evidence_location: screenshot
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md"]
related_sops: [sop-drafts/2026-08-08_amazon-client-onboarding.md]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0068"
---

## Question

The national ID was rejected twice with no detailed reason even though every field matched. A phone bill submitted as proof of address was also rejected. The ID was in a non-Latin script with only field labels translated.

## Answer

If identity or address documents are rejected while every detail matches, check the document language first. Amazon accepts verification documents only in its listed languages; the test is language, not script, so a document printed in Latin letters can still fail. Switch to a document in an accepted language, such as a passport whose data page includes English, or submit a notarized translation with the original, and enter its details exactly as printed.

## Cause

An automated email said the documents were rejected because they were not in an accepted language. Amazon accepts verification documents only in a listed set of languages; documents in any other language need a notarized translation submitted with the original.

## Fix

1. Read the automated verification email or the rejection notice for the stated reason.
2. Check the document language against the accepted language list on the verification help page. The rule is about language, not script: a document printed fully in Latin letters can still be rejected.
3. Replace the document with one in an accepted language (for example a passport whose data page includes English), or attach a notarized translation in an accepted language together with the original.
4. Make sure the name, date of birth, ID number and expiry entered match the replacement document exactly.
5. Resubmit only when Amazon asks for it, not while a review is pending; a resubmission request must be answered within 30 days. Wait for the verification result.

## Verify

Verification accepts the replacement document. The thread ended before the result was shown.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- Also in: `sop-drafts/2026-08-08_amazon-client-onboarding.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds the symptom view: repeated rejections with matching data trace back to the accepted-language rule, and a passport in an accepted language is the quickest replacement.
- Existing coverage: full (`Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/218-brand-registry-identity-verification-process-GYRZRWX6NG36F4GH.md`, `MAG SOPs/catalog/catalog-sop-providing-dmca-counter-notice-for-copyright-infringements.md`, `Amazon Seller Help/articles/219-brand-registry-identity-verification-faq-G3UY9ZFTXGRJUSQ2.md`, `Amazon Ads Help/articles/guides/011-sponsored-display-for-all-businesses.md`).
