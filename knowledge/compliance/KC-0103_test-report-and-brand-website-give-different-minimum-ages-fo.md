---
id: KC-0103
title: "Test report and brand website give different minimum ages for a toy or puzzle: which age goes on the listing"
kind: rule
topic: compliance
status: reviewed
skills: [amazon-catalog, amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: true
surface: "Listing attributes (manufacturer minimum age) and compliance documents"
surface_verified: false
symptom_keywords: ["test report age differs from website", "minimum age listing toy test report", "age grading mismatch Amazon listing", "children's product certificate age mismatch", "which recommended age to use on listing"]
error_text: []
asked_as: ["While preparing new toy SKUs with their test reports and Children's Product Certificates, the agency found that the test report and the brand's website stated different minimum ages, and asked which o"]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-children-s-product-safety-request-or-children-s-product-certificate-cpc.md"]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0103"
---

## Question

While preparing new toy SKUs with their test reports and Children's Product Certificates, the agency found that the test report and the brand's website stated different minimum ages, and asked which one to use on the listing.

## Answer

When the test report and the brand's marketing give different minimum ages, take the listing's age attributes from the test report, which is the lab's age grading, and ask the brand to align its website and packaging. Per the MAG CPC SOP, a listing age of 12 or younger prompts Amazon to ask for a Children's Product Certificate and test reports. Never set the listing age above the age the product is designed for just to keep it out of children's product scope.

## Cause

The thread establishes only the client's answer: use the age from the test report. The reasoning comes from the MAG CPC SOP, not the thread. Amazon asks for a Children's Product Certificate and test reports when a listing identifies its age group as 12 years or younger, so a listing age that disagrees with the lab's age grading can trigger or contradict a compliance request.

## Fix

1. Compare the minimum age on the test report, the Children's Product Certificate, the packaging and the brand website before listing.
2. Use the age stated in the test report for the listing's minimum age attributes.
3. Ask the brand to align its website and packaging with the test report.
4. Keep the test report and certificate ready for the compliance request.

## Verify

The listing's age attributes match the test report, and the brand's website and packaging show the same age. The thread does not show the later compliance outcome.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-children-s-product-safety-request-or-children-s-product-certificate-cpc.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The CPC SOP defines children's product scope but does not say which source sets the listing age when the test report and brand marketing disagree.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-children-s-product-safety-request-or-children-s-product-certificate-cpc.md`, `Amazon Seller Help/articles/233-report-a-violation-error-messages-GMSR9C4BP3GYR673.md`, `MAG SOPs/catalog/catalog-sop-how-to-remove-a-listing-from-a-parentage.md`, `MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`).
