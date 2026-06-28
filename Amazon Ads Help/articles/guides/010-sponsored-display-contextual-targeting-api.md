---
title: "Sponsored Display contextual targeting API"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/contextual-targeting"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Sponsored Display contextual targeting API

Contextual targeting promotes products to audiences browsing related products, similar products, and categories. Amazon notes that this can reach shoppers both on Amazon and outside Amazon when customers view content related to the targeting strategy.

Sponsored Display contextual targeting follows the standard Amazon Ads API campaign structure and uses grammar similar to Sponsored Products campaigns.

## Dynamic targeting

Amazon recommends `similarProduct` targeting for campaigns to reach products similar to the advertised product. The similar products are dynamically generated using machine learning models built on retail data.

## Campaign creation workflow

| Step | Action | Endpoint/resource |
| --- | --- | --- |
| 1 | Create campaign | `/sd/campaigns` |
| 2 | Create ad group | `/sd/adGroups` |
| 3 | Create product ads | `/sd/productAds` |
| 4 | Create target clauses | `/sd/targets` |
| Optional | Negative targeting | `/sd/negativeTargets` |

Advertisers can create targeting clauses for both Audience and Contextual campaigns with tactic `T00030`.

## Campaign fields

Contextual targeting campaigns can use tactic `T00020` or `T00030`.

Useful campaign fields:

- `name`
- `tactic`
- `budgetType`
- `costType`
- `portfolioId`
- `budget`
- `startDate`
- `endDate`
- `state`

Supported cost types discussed:

| Cost type | Meaning | Use case |
| --- | --- | --- |
| `cpc` | Cost per click | Click and conversion objectives. |
| `vcpm` | Cost per 1000 viewable impressions | Awareness/reach objectives. |

## Ad group bid optimization

Ad groups can use `bidOptimization` to align with campaign objectives.

| `bidOptimization` | Meaning |
| --- | --- |
| `clicks` | Serve to audiences more likely to click. |
| `conversions` | Optimize for higher conversion rate. |
| `reach` | Optimize for viewable impressions; required when campaign `costType` is `vcpm`. |

## Product ads

Product ads are created under the ad group and campaign. Fields shown by Amazon include:

- `adGroupId`
- `campaignId`
- `landingPageURL`
- `landingPageType`
- `state`
- `adName`

## Target clause examples

Common contextual targeting expression types:

| Clause | Description |
| --- | --- |
| `asinSameAs` | Target products with the same ASIN. |
| `asinCategorySameAs` | Target products in the same category. |
| `asinBrandSameAs` | Target products from the same brand. |
| `asinPriceBetween`, `asinPriceGreaterThan`, `asinPriceLessThan` | Target based on ASIN price criteria. |
| `asinReviewRatingLessThan`, `asinReviewRatingGreaterThan`, `asinReviewRatingBetween` | Target based on review rating criteria. |
| `asinIsPrimeShippingEligible` | Target Prime-shipping-eligible products. |
| `asinAgeRangeSameAs` | Target products in an age range, for supported categories such as toys and games. |
| `asinGenreSameAs` | Target products in a genre, for supported categories such as Books. |
| `similarProduct` | Target products similar to the advertised ASIN. |

Target objects include fields such as:

- `adGroupId`
- `state`
- `expressionType`
- `bid`
- `expression`

## Campaign management operations

| Operation | Method/resource | Notes |
| --- | --- | --- |
| Retrieve one campaign | `GET /sd/campaigns/{campaignId}` | No request body. |
| Retrieve all campaigns | `GET /sd/campaigns/` | No request body. |
| Update campaign | `PUT /sd/campaigns` | Uses create-like structure plus required `campaignId`. |
| Delete campaign | `DELETE /sd/campaigns/{campaignId}` | No request body. |

## Negative targeting

Negative targeting for contextual campaigns uses `/sd/negativeTargets`. It follows the same format as `/sd/targets`, but the expressions are negated within the ad group.

Example use: target a category, then exclude a brand from that category by creating a negative target with `asinBrandSameAs`.

## Routing use

Use this page when the work involves Sponsored Display contextual targeting, similar-product targeting, `vcpm` reach campaigns, or Sponsored Display negative target exclusions.

## Related pages

- [Sponsored Display overview](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/overview)
- [Dynamic segments](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/dynamic-segments)
- [Targetable entities](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/targetable-entities)
- [Sponsored Display OpenAPI](https://advertising.amazon.com/API/docs/en-us/sponsored-display/3-0/openapi)
- [Create Sponsored Display campaigns using Postman](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/tutorials/postman)
