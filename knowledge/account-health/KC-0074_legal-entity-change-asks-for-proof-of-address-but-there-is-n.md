---
id: KC-0074
title: "Legal entity change asks for proof of address but there is no utility bill for the business address"
kind: procedure
topic: account-health
status: reviewed
skills: [amazon-account-health-check]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central Account Health / legal entity change"
surface_verified: false
symptom_keywords: ["legal entity change proof of address", "no utility bill for business address", "country of legal entity still shows old country", "address verification bank statement", "registered address differs from physical address"]
error_text: []
asked_as: ["During a legal entity change to a new company in another country, Seller Central asked for address verification."]
synonyms: []
resolution_status: partial
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0074"
---

## Question

During a legal entity change to a new company in another country, Seller Central asked for address verification. The country field still showed the old country, and the client only had a utility bill for a different physical address, not for the registered and banking address.

## Answer

When a legal entity change asks for proof of address, you do not need a utility bill: a bank account statement for the entity is an accepted document. Make sure the address on the document matches the address you entered. The account's country updates only once the entity change is processed, and verification items can reappear meanwhile, so recheck Account Health after submitting.

## Cause

Amazon accepts several document types as proof of address, including a bank account statement, so a utility bill is not mandatory. The country shown on the account updates only once the legal entity change itself is processed.

## Fix

1. Start the legal entity change and enter the new entity, its tax ID and its registered address exactly as on company documents.
2. Confirm which address is the registered and banking address and which is the physical address before filling the form.
3. For proof of address, use a bank account statement for the entity when no utility bill exists for that address; it is on Amazon's accepted list.
4. In the source case the agency chose to wait until the entity country had switched before uploading; this is a judgment call, not a stated Amazon rule.
5. Recheck the Account Health dashboard afterwards; the verification item reappeared once the change had started.

## Verify

The legal entity shows the new country and the address verification request disappears from the Account Health dashboard.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Applies the accepted proof-of-address list to a legal entity change and adds the practice of waiting for the entity country switch before uploading.
- Existing coverage: full (`Amazon Seller Help/articles/026-global-seller-identity-address-and-business-verification-GQRP483PDN88Q3M9.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/218-brand-registry-identity-verification-process-GYRZRWX6NG36F4GH.md`).
