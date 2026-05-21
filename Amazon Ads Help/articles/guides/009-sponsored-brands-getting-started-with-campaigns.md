---
title: "Getting started with Sponsored Brands campaigns"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-brands/campaigns/get-started-with-campaigns"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Getting started with Sponsored Brands campaigns

Amazon notes that this page describes Sponsored Brands-specific APIs, while newer campaign management APIs can manage multiple ad products through a common model.

Use the newer campaign management overview when the task can be handled through the common campaign model. Use this page when Sponsored Brands-specific v4 behavior, creative constraints, or goal-based campaign details matter.

## Before you begin

- Complete Amazon Ads API onboarding and getting started.
- Have an access token and profile ID.
- Understand Sponsored Brands campaign structure.
- Optional: use a test account to practice the flow without ad spend.

## Workflow

| Step | Action | Endpoint or object |
| --- | --- | --- |
| 1 | Create a campaign | `POST /sb/v4/campaigns` |
| 2 | Create ad group | `POST /sb/v4/adGroups` |
| 3 | Upload and register assets | Creative asset library API |
| 4 | Create an ad | Sponsored Brands ad type endpoint |
| 5 | Add targeting to the ad group | Keywords, product targets, or themes |
| 6 | Check moderation status | Moderation API using `adId` |
| 7 | Update ad or creative if needed | Asset management and campaign management APIs |

## Step 1: Create campaign

The first step is creating the campaign with `POST /sb/v4/campaigns`.

For sellers with an approved brand, Amazon says `brandEntityId` is required. Retrieve it through the `GET /brands` endpoint.

Campaign-level bidding can be automatic for placements outside top of search, or can use custom bidding adjustments.

## Goal-based campaigns

Goal-based campaigns provide a streamlined setup with recommendations aligned to the campaign goal.

| Parameter | Optional | Description | Default |
| --- | --- | --- | --- |
| `goal` | No | Goal type. `BRAND_IMPRESSION_SHARE` shows ads to shoppers searching for the brand. `PAGE_VISIT` drives traffic to landing and detail pages. | `PAGE_VISIT` |
| `costType` | No | Bid/charge model. `CPC` is cost per click. `VCPM` is cost per 1000 viewable impressions. | `CPC` |
| `smartDefault` | Yes | Default strategy list. `MANUAL` creates no default targeting. `TARGETING` creates theme targeting automatically when creating an ad group. | `MANUAL` without a goal; `TARGETING` when a goal is present. |

Once a goal-based campaign is created, `goal`, `costType`, and `smartDefault` are not editable.

Validation rules:

| Goal included? | Cost type included? | Result |
| --- | --- | --- |
| No | No | Defaults to `PAGE_VISIT` with `CPC`. |
| No | Yes | Validation error. |
| Yes | No | Validation error. |
| Yes | Yes | Creates a goal-based campaign. |

Operational note: for optimized performance, Amazon advises not to include bidding optimizations when `smartDefault` is `TARGETING` or `costType` is `VCPM`.

## Step 2: Create ad group

Create at least one ad group with `POST /sb/v4/adGroups`, using the `campaignId` from campaign creation. A successful create call can return a multi-status response and the created `adGroupId`.

## Step 3: Upload and register assets

Use the creative asset library API for images or videos before creating the ad.

## Step 4: Create ad

Supported ad types mentioned by Amazon:

- Collections
- Product collection
- Video
- Brand video
- Store spotlight

An ad group must have at least one ad and cannot contain more than one ad type.

When using `BRAND_IMPRESSION_SHARE`, use one of:

- Product collection with custom image and Store landing page.
- Store spotlight with Store landing page.
- Brand video with Store landing page.

## Step 5: Add targeting

An ad group can use product or keyword targeting expressions.

| Targeting type | Endpoint |
| --- | --- |
| Keyword targeting | `POST /sb/keywords` |
| Product targeting | `POST /sb/targets` |
| Theme targeting | `POST /sb/themes` |

## Step 6: Check moderation

Use the Moderation API and pass the `adId` as the moderation `id`.

## Step 7: Make changes

If moderation requires changes, use asset management and campaign management docs to update the ad or creative.

## Related pages

- [Campaign management overview](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/overview)
- [Sponsored Brands campaign structure](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-brands/campaigns/structure)
- [Creative asset library](https://advertising.amazon.com/API/docs/en-us/guides/creative-asset/asset-library-overview)
- [Moderation API](https://advertising.amazon.com/API/docs/en-us/moderation)
- [Managing Sponsored Brands campaigns](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-brands/campaigns/managing-multi-ad-group-campaigns)
