---
id: KC-0087
title: "Personal-care listing flagged for pesticidal claims before an FBA inbound: remove the antimicrobial wording, then appeal to clear the notification"
kind: procedure
topic: compliance
status: reviewed
skills: [amazon-account-health-check, amazon-seo, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Restricted Product Policy Violations; listing edit"
surface_verified: false
symptom_keywords: ["pesticide flag on listing", "pesticidal claims removed", "antibacterial claim listing blocked", "restricted product pesticide appeal", "listing flagged as pesticide device"]
error_text: ["Examples of prohibited claims include references to eliminating, destroying, or mitigating bacteria, viruses, fungus, germs, or similar microorganisms. Once all pesticidal claims are removed, you may relist your product through Seller Central."]
asked_as: ["While a new personal-care product was being prepared for its first FBA shipment, Account Health raised a pesticide flag on the listing with an appeal deadline."]
synonyms: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md"]
supersedes: []
contradicts: []
observed: 2026-03
review_by: 2027-10
provenance: "ledger:KC-0087"
---

## Question

While a new personal-care product was being prepared for its first FBA shipment, Account Health raised a pesticide flag on the listing with an appeal deadline. The client asked whether to appeal.

## Answer

If a product that is not a pesticide is flagged as one, look for pesticidal wording in the listing: claims about eliminating, destroying or mitigating bacteria, viruses, fungus or germs, or about killing or repelling pests. Remove those claims from every listing field, then appeal from the Account Health row before the deadline. Do not send FBA inventory until the flag has cleared. The pesticide SOPs carry the full appeal route.

## Cause

The listing text contained claims that Amazon reads as pesticidal, such as eliminating or mitigating bacteria, germs or similar microorganisms. Those claims make Amazon treat the product as a pesticide or pesticide device, which needs EPA registration; the product itself was not a pesticide.

## Fix

1. Open the notification under Account Health > Restricted Product Policy Violations and copy the notice text and the deadline.
2. Search the title, bullets, description, backend terms and images for claims about killing, eliminating or reducing bacteria, viruses, fungus, germs or microorganisms, and remove them.
3. Once the listing is clean, submit the appeal from the same violation row (operator approval before submitting).
4. Wait for the flag to clear, then continue with the FBA shipment.

## Verify

The violation no longer appears in Account Health and the listing is active and selectable in Send to Amazon.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Mostly covered by the pesticide SOPs; the card adds one confirmed instance where wording removal plus appeal cleared the flag before a first FBA inbound.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `MAG SOPs/catalog/catalog-sop-how-to-fix-pesticide-yanks-and-gating.md`).
