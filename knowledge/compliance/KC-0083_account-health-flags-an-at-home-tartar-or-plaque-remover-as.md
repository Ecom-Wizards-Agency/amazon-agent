---
id: KC-0083
title: "Account Health flags an at-home tartar or plaque remover as a professional-use only medical device; listing cannot be sold to consumers"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-account-health-check, amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Account Health > product policy violation detail"
surface_verified: false
symptom_keywords: ["dental scaler professional use only", "tartar remover listing removed", "professional-use medical device account health", "professional health care program only", "plaque remover flagged fda"]
error_text: ["has been identified as a dental scaler, which is classified as a professional-use only medical device by the FDA", "Medical devices of this type that are designed for tartar and calculus removal are typically classified by the FDA as devices requiring professional supervision and are not cleared for over-the-counter retail sale to general consumers.", "Per Amazon policy, professional-use only medical devices may only be sold to appropriately licensed healthcare customers who have Amazon Business accounts through sellers participating in the Professional Health Care program.", "This product cannot be listed for sale to general consumers on Amazon."]
asked_as: ["While cleaning up Account Health, the account manager found an at-home dental tartar remover flagged as a dental scaler, a professional-use only medical device, and asked the client for technical deta"]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/116-amazon-business-professional-healthcare-program-GFFRHXRJSRGPZ9UL.md"]
related_sops: [knowledge/compliance/KC-0002_cosmetic-applicator-listing-removed-as-an-uncleared-medical.md]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0083"
---

## Question

While cleaning up Account Health, the account manager found an at-home dental tartar remover flagged as a dental scaler, a professional-use only medical device, and asked the client for technical details to contest it. The client said the listing had never gone live because the model lacked the required certifications.

## Answer

If Account Health calls a product a professional-use only medical device, Amazon will not let it be sold to general consumers; under the Professional Healthcare program it can only go to licensed healthcare buyers. Amazon bases the classification on what the listing describes, so check with the brand whether the product has the clearance its device class needs. With documentation, appeal; without it, delete an unused listing instead of appealing.

## Cause

Amazon classified the product, from its listing description (tartar and calculus removal by high-frequency vibration), as a dental scaler, which the FDA treats as a professional-use only device. Such devices may only be sold to licensed healthcare buyers through the Professional Health Care program, so a consumer listing is not allowed.

## Fix

1. Open the Account Health violation and read the full detail text with Review details.
2. Ask the brand whether the product holds the FDA clearance the device class needs (for example a 510(k)) and whether the listing is still wanted.
3. If the brand has clearance documentation or the classification is wrong, follow the medical-device MAG SOP and appeal with that evidence (operator approval required before submitting).
4. If the product cannot be sold to consumers and the listing is not wanted, delete it so the violation does not keep resurfacing. Deleting a listing needs operator approval.
5. Selling a professional-use only device at all requires the Amazon Business Professional Healthcare program and its compliance documentation.

## Verify

The listing was removed; the thread does not show the Account Health entry clearing afterwards.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/116-amazon-business-professional-healthcare-program-GFFRHXRJSRGPZ9UL.md`
- Also in: `knowledge/compliance/KC-0002_cosmetic-applicator-listing-removed-as-an-uncleared-medical.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Gives the verbatim professional-use only dental scaler notice and the practical decision to delete an unused listing instead of appealing; the PHC page covers only the program rule.
- Existing coverage: full (`Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`).
