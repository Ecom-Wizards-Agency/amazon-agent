---
title: "Get started with manual Sponsored Products campaigns"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/get-started/manual-campaigns"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Get started with manual Sponsored Products campaigns

Manual campaigns give advertisers direct control over targeting. Targeting can include manually created product targeting expressions and keywords.

Amazon recommends starting with an auto campaign if the advertiser is new to Sponsored Products campaign creation.

## Before you begin

- Complete Amazon Ads API onboarding and getting started.
- Have an access token and profile ID.
- Understand the Sponsored Products campaign structure.
- Optional: create or review an auto campaign to identify keywords and targeting expressions for the manual campaign.
- Optional: use a test account to practice without ad spend risk.

## Workflow

| Step | Action | Endpoint or object |
| --- | --- | --- |
| 1 | Create campaign | `POST /adsApi/v1/create/campaigns` |
| 2 | Create at least one ad group | `POST /adsApi/v1/create/adGroups` |
| 3 | Create at least one product ad per ad group | `POST /adsApi/v1/create/ads` |
| 4 | Add targeting | Product/category target or keyword |
| 5 | Optional: add negative targeting | `POST /adsApi/v1/create/targets` with `negative: true` |

To create a manual campaign, set `autoCreateTargets` to `false` in `autoCreationSettings`.

## Targeting choices

### Product targeting

1. Get recommended ASINs to target.
2. Get bid recommendations for the targeting expression.
3. Create a product targeting expression.

Key endpoints:

- `POST /sp/targets/products/recommendations`
- `POST /sp/targets/bid/recommendations`
- `POST /adsApi/v1/create/targets`

### Category targeting

1. Explore targetable categories or get suggested categories.
2. Explore refinements for the category, such as brands, age ranges, or genres.
3. Check targetable ASIN count for category/refinement combinations.
4. Get bid recommendations.
5. Create category targeting expressions.

Key endpoints:

- `GET /sp/targets/categories`
- `POST /sp/targets/categories/recommendations`
- `GET /sp/targets/category/{categoryId}/refinements`
- `POST /sp/targets/products/count`
- `POST /sp/targets/bid/recommendations`
- `POST /adsApi/v1/create/targets`

### Keyword targeting

1. Get recommended keywords and bids.
2. Create one or more keywords.

Key endpoints:

- `POST /sp/targets/keywords/recommendations`
- `POST /adsApi/v1/create/targets`

## Negative targeting

Negative keyword targeting and negative product targeting can stop ads from showing on certain search results, brands, or product detail pages.

Negative targets can be applied at campaign or ad group level. Create them through the targets API by setting `negative` to `true`.

## Completion checkpoint

A Sponsored Products manual campaign is complete and ready to run when it has:

- At least one active campaign.
- At least one active ad group.
- At least one active product ad.
- At least one targeting expression or keyword.

If the start date is today and all entities are `ACTIVE`, the campaign can start serving immediately.

## Related pages

- [Sponsored Products campaign structure](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/get-started/campaign-structure)
- [Auto campaigns](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/get-started/auto-campaigns)
- [Campaigns](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/campaigns)
- [Ad groups](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/ad-groups)
- [Product ads](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/product-ads)
- [Keyword targeting](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/keywords/overview)
- [Product targeting](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/product-targeting/overview)
