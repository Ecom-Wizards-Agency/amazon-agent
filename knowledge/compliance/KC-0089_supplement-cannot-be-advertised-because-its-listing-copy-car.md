---
id: KC-0089
title: "Supplement cannot be advertised because its listing copy carries weight-loss and fat-burning claims"
kind: diagnosis
topic: compliance
status: reviewed
skills: [amazon-seo, amazon-ads-console, amazon-troubleshooting]
marketplaces: [IT]
marketplace_inferred: true
surface: "Listing copy; Amazon Ads eligibility"
surface_verified: false
symptom_keywords: ["supplement cannot be advertised", "weight loss claims ads blocked", "fat burner listing ineligible for ads", "health claims block sponsored products", "product blocked after SEO update"]
error_text: []
asked_as: ["A weight-management supplement's listing copy ranked well but the product could not be advertised."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/048-ads-content-moderation-GXZXZ78UXL2AEBQ9.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-01
review_by: 2027-10
provenance: "ledger:KC-0089"
---

## Question

A weight-management supplement's listing copy ranked well but the product could not be advertised. The brand asked whether to keep the persuasive copy or rewrite it so ads could run.

## Answer

If a supplement cannot be advertised, check its listing copy for weight-loss, fat-burning or diet claims that exceed the authorized health claims for its ingredients. Rewrite to authorized claim wording only, accept that the copy becomes less persuasive, and expect that getting ads re-approved can take time and a support case. Confirm afterwards that the catalog actually shows the new copy.

## Cause

According to the brand, the copy's weight-loss and fat-burning language exceeded the health claims authorized for the ingredients in the EU, and that kept the product out of ads. The brand's reviewer also flagged 'body weight control' and 'diet' as likely triggers. After the compliant rewrite was uploaded the product was blocked again and needed a ticket. The thread does not establish which wording caused that block or quote any Amazon notice.

## Fix

1. Decide the trade-off explicitly with the brand: aggressive copy without ads, or compliant copy with ads.
2. Rewrite title, bullets, description and backend terms using only authorized EU health-claim wording for the listed ingredients; remove weight-loss, fat-burning, 'diet' and 'body weight control' phrasing.
3. Have the brand review the revised copy, then upload it (approval gate).
4. If the product is blocked for ads or the listing after the change, open a support case with the compliant copy as the reasoned answer (approval gate for the send).
5. Recheck that the copy change actually applied in the catalog; in the thread part of it did not reflect and needed support.

## Verify

The ads block notice clears, the product can be added to a campaign, and the live detail page shows the revised copy.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/048-ads-content-moderation-GXZXZ78UXL2AEBQ9.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Links over-claiming supplement copy to the product being blocked for ads and shows the copy-versus-ads trade-off and slow reinstatement in an EU store.
- Existing coverage: partial (`MAG SOPs/catalog/catalog-sop-mental-health-disorder-and-sleep-disorder-claims.md`, `MAG SOPs/README.md`, `MAG SOPs/catalog/catalog-sop-disease-medical-and-pathogens-claims-of-usa.md`).
