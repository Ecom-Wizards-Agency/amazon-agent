---
id: KC-0288
title: "Amazon Ads charges the card many times in small amounts; how the billing threshold rises"
kind: rule
topic: ads
status: reviewed
skills: [amazon-ads-console]
marketplaces: [DE]
marketplace_inferred: true
surface: "Amazon Ads > Billing and payments"
surface_verified: false
symptom_keywords: ["amazon ads charges every day", "small ads invoices accounting", "ads billing threshold", "increase ads credit limit", "too many advertising receipts"]
error_text: []
asked_as: ["A client asked whether anything could be done about Amazon Ads billing so often, almost daily, in small amounts, because collecting each receipt for accounting was a burden."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/084-understand-amazon-ads-billing-cycles-GY3YNTWRZYVPLADL.md", "Advertising Help After Login/articles/101-view-and-download-an-advertising-invoice-GKEZS9J2K2FCPEAX.md", "Advertising Help After Login/articles/097-how-to-pay-by-invoice-GZ5GNKLJVZDFUU4L.md"]
related_sops: []
supersedes: []
contradicts: ["Advertising Help After Login/articles/084-understand-amazon-ads-billing-cycles-GY3YNTWRZYVPLADL.md"]
observed: 2024-10
review_by: 2027-10
provenance: "ledger:KC-0288"
---

## Question

A client asked whether anything could be done about Amazon Ads billing so often, almost daily, in small amounts, because collecting each receipt for accounting was a burden.

## Answer

Frequent small Amazon Ads charges come from a low starting credit limit that rises automatically after each successful payment. Wait for the limit to step up, download invoices in bulk for accounting, and look at monthly invoicing if the account qualifies. Do not change payment settings without the account owner's approval.

## Cause

Amazon Ads bills card-paying advertisers whenever they reach a credit limit (billing threshold). The limit starts low and rises step by step after each successful payment, so new or recently reset accounts see frequent small charges until the limit reaches its top step.

## Fix

1. Open Billing and payments in the Amazon Ads console and check the current credit limit (billing threshold).
2. Expect the limit to rise automatically after each charge is paid successfully; no action is needed.
3. For accounting, use Download summary on the Billing page (all invoices issued in the last 90 days), the CSV invoice export, or the monthly global statement under Documents, instead of collecting each receipt.
4. If charges stay frequent after the top step, consider paying by invoice (monthly, Net 30) where the account qualifies, or open an Ads support case (operator approval before changing payment settings or submitting).

## Verify

Billing history shows larger, less frequent charges as the threshold rises.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/084-understand-amazon-ads-billing-cycles-GY3YNTWRZYVPLADL.md`
- First-party: `Advertising Help After Login/articles/101-view-and-download-an-advertising-invoice-GKEZS9J2K2FCPEAX.md`
- First-party: `Advertising Help After Login/articles/097-how-to-pay-by-invoice-GZ5GNKLJVZDFUU4L.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The help page states the threshold steps; the card adds the symptom phrasing (frequent small charges burdening accounting) and the bulk-invoice workaround.
- Existing coverage: full (`Advertising Help After Login/articles/084-understand-amazon-ads-billing-cycles-GY3YNTWRZYVPLADL.md`, `Amazon Ads Help/articles/knowledge-hub/007-amazon-connect-tealium-ads-api.md`, `Advertising Help After Login/articles/049-understand-ads-agent-GKT6KLCX98F5LWKM.md`, `Amazon Ads Help/articles/knowledge-hub/003-first-party-data-adm-workshop.md`, `Advertising Help After Login/articles/027-create-and-manage-ads-in-creative-studio-G55KXDLSKCKVG3TJ.md`).
