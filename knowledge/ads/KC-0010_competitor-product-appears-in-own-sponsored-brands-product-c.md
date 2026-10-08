---
id: KC-0010
title: "Competitor product appears in own Sponsored Brands Product Collection ad"
kind: diagnosis
topic: ads
status: draft
skills: [amazon-ads-console]
marketplaces: [DE]
marketplace_inferred: true
surface: "Amazon Ads Console > Sponsored Brands > product collection creative"
surface_verified: false
symptom_keywords: ["competitor product in my sponsored brands ad", "wrong ASIN in product collection", "other brand shown in SB ad", "sponsored brands creative shows competitor"]
error_text: []
resolution_status: resolved
fix_source: agency
evidence_location: slack
confidence: low
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md", "Advertising Help After Login/articles/048-ads-content-moderation-GXZXZ78UXL2AEBQ9.md", "Advertising Help After Login/articles/020-edit-a-campaign-GW73Q54RZZCMPYYV.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0010"
---

## Question

The client saw another brand's product shown next to their own products in their Sponsored Brands Product Collection ad on the first results page, and asked whether a competitor ASIN had been added to the campaign by mistake.

## Answer

If another brand's product shows up inside your own Sponsored Brands Product Collection ad, check the creative's product selection and any Store page it links to. Replace the product with Edit creative and confirm moderation approved the new version. Review usually takes under 24 hours and can take up to 3 business days.

## Cause

Not established in the thread. The fix was a new creative version without the other product, which suggests the creative's product selection contained it. Whether a wrong ASIN was picked, Amazon filled the products automatically, or a linked Store asset pulled it in is unknown.

## Fix

1. Open the SB campaign, go to the Creative tab and check the ASINs in the product collection creative and in any linked Store page.
2. Click Edit creative, remove any ASIN that is not the brand's own and submit the new creative version. Submission needs operator approval.
3. Wait for moderation to approve the new version (read the status in the console; Amazon no longer emails approvals), then confirm the live ad no longer shows the other product.

## Verify

The team reported the new creative version without the other product was approved. The live ad was not re-checked with a screenshot.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md`
- First-party: `Advertising Help After Login/articles/048-ads-content-moderation-GXZXZ78UXL2AEBQ9.md`
- First-party: `Advertising Help After Login/articles/020-edit-a-campaign-GW73Q54RZZCMPYYV.md` (Edit creative in the Creative tab)
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No source covers a foreign product appearing in a product collection ad or how a new creative version replaces the live ad after moderation.
- Existing coverage: partial (`Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md`, `Advertising Help After Login/articles/020-edit-a-campaign-GW73Q54RZZCMPYYV.md`).
- Thread observations no captured page supports: the ad keeps serving the old version until the new one is approved, so the change should be made the same day. No Sponsored Brands creative page under `Advertising Help After Login/articles/` covers serving during moderation.
- Confidence stays low: one thread, and the cited pages back the edit-and-moderation steps, not the mechanism that put the other product in the creative.
