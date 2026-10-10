---
id: KC-0308
title: "Sponsored Brands video uses a sister brand's logo instead of the brand the advertised product is sold under"
kind: rule
topic: ads
status: reviewed
skills: [amazon-sponsored-brands-video-briefs, amazon-ads-console]
marketplaces: [DE]
marketplace_inferred: true
surface: "Amazon Ads Console > Sponsored Brands > video creative > brand logo"
surface_verified: false
symptom_keywords: ["wrong logo in sponsored brands video", "sister brand logo sponsored brands", "multi-brand owner sponsored brands logo", "brand logo mismatch ad creative"]
error_text: []
asked_as: ["The brand owner reviewed a live Sponsored Brands video and reported that it carried the logo of a sister brand from the same company."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md", "Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-08
review_by: 2027-10
provenance: "ledger:KC-0308"
---

## Question

The brand owner reviewed a live Sponsored Brands video and reported that it carried the logo of a sister brand from the same company. The advertised product is sold under a different brand with its own positioning. The brand owner asked for the video to be changed.

## Answer

When a company sells under several brands, confirm which brand each advertised product belongs to before choosing the logo for a Sponsored Brands ad. Amazon asks for your registered brand logo, so a sister brand's logo misrepresents the product even when both brands share an owner. Keep a logo file for every brand in the account and ask the brand owner for any missing one before production starts.

## Cause

The creative producer assumed that one of the company's brands was a parent brand whose logo covered every product. The company runs separate brands with different positioning, and the agency had no logo file for the brand the product is sold under, so the wrong logo went into the creative.

## Fix

1. Check the brand attribute on the advertised product's listing and confirm which registered brand it belongs to before building any Sponsored Brands creative.
2. Ask the brand owner for the correct brand's logo file (vector format, with a light-on-dark version if needed) and store it in the client's brand asset folder.
3. Rebuild the video or creative with the correct brand logo and brand name.
4. Submit the updated creative for moderation (operator approval required before replacing a live ad).

## Verify

The live ad shows the logo and brand name that match the brand attribute on every advertised product, and the brand owner signs off on the creative.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md`
- First-party: `Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: First-party pages ask for the registered brand logo but do not warn that a multi-brand owner must match the logo to the advertised product's own brand.
- Existing coverage: full (`Advertising Help After Login/articles/172-create-a-sponsored-brands-campaign-GF86HBCNDJUAC5WN.md`, `knowledge/ads/KC-0010_competitor-product-appears-in-own-sponsored-brands-product-c.md`, `Amazon Ads Help/articles/guides/009-sponsored-brands-getting-started-with-campaigns.md`, `Advertising Help After Login/articles/035-sponsored-brands-GGWFYHL27MFXLHS6.md`, `Advertising Help After Login/articles/062-reserve-keywords-in-a-sponsored-brands-campaign-G86SD7HK6NHHRB9B.md`).
