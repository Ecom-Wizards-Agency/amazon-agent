---
id: KC-0270
title: "Report a Violation will not submit for a seller using our brand name and keeps asking for an order ID"
kind: diagnosis
topic: brand-registry
status: reviewed
skills: [amazon-communications, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: false
surface: "Brand Registry > Report a Violation; Brand Registry > Get support (case)"
surface_verified: false
symptom_keywords: ["Report a Violation submit greyed out", "report a violation asks for order ID", "trademark infringement report blocked", "cannot submit brand registry infringement report", "seller using our brand name"]
error_text: []
asked_as: ["A third-party seller was listing products under the brand name."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/233-report-a-violation-error-messages-GMSR9C4BP3GYR673.md", "Amazon Seller Help/articles/224-report-intellectual-property-infringements-G202132860.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-how-to-fix-trademark-tm-infringement-yank.md"]
supersedes: []
contradicts: []
observed: 2024-08
review_by: 2027-10
provenance: "ledger:KC-0270"
---

## Question

A third-party seller was listing products under the brand name. The agency, with Brand Registry rights, tried Report a Violation with Trademark infringement; a warning about resellers appeared, the Submit button stayed greyed out, and every infringement type asked for an Order ID, even from the brand owner account.

## Answer

If Report a Violation keeps asking for an order ID and will not submit, Amazon wants a test purchase for reports against individual sellers' offers: buy from the seller, confirm the item infringes, and submit with that order ID. First confirm the seller is not a lawful reseller of genuine goods. When no form path works, open a case through Brand Registry support rather than Seller Support, follow up with Escalate previously submitted issue, and keep Abuse Escalations as the last step.

## Cause

First-party guidance: reports against individual third-party sellers require a test purchase and its order ID, and Amazon can temporarily require test purchases after recent reports were found invalid. Without an order ID the form would not submit. The thread did not confirm which of these applied.

## Fix

1. Before reporting, confirm the seller is not a lawful reseller of genuine goods; the Report a Violation reseller warning and the first-party note that legally purchased products may be resold apply. Here the seller was using the brand name as its own. 2. In Report a Violation, choose the infringement type that fits (here Trademark infringement). 3. If the form requires an Order ID, Amazon wants a test purchase for reports against individual sellers' offers: buy from the seller, confirm the item infringes, and submit with that order ID. 4. If no reporting path submits, open a case from Brand Registry support (not Seller Central Seller Support) describing the brand-name misuse (operator approval before submitting). 5. To follow up, use Brand Registry support > Escalate previously submitted issue > Escalate an infringement related issue. 6. Treat Abuse Escalations as a last resort; the thread reports it requires all other options to be exhausted first.

## Verify

The Brand Registry case or the violation report shows a submitted ID and a response, and the infringing offers or listings are removed.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/233-report-a-violation-error-messages-GMSR9C4BP3GYR673.md`
- First-party: `Amazon Seller Help/articles/224-report-intellectual-property-infringements-G202132860.md`
- Also in: `MAG SOPs/catalog/catalog-sop-how-to-fix-trademark-tm-infringement-yank.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Opening a Brand Registry support case when Report a Violation will not submit without an order ID, with Abuse Escalations as the last resort, goes beyond the error-message page.
- Existing coverage: full (`Amazon Seller Help/articles/224-report-intellectual-property-infringements-G202132860.md`, `Amazon Seller Help/articles/233-report-a-violation-error-messages-GMSR9C4BP3GYR673.md`, `Amazon Seller Help/articles/225-report-alleged-trademark-infringements-via-common-law-GS45XXXQDNDP9MJU.md`).
