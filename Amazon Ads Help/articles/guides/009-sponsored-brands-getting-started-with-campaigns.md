---
title: "Getting started with Sponsored Brands campaigns"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-brands/campaigns/get-started-with-campaigns"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-10-07"
status: "captured"
---

# Getting started with campaigns

Note

See the latest Campaign Management APIs here for the latest Campaigns, Ad Groups, Ads, and Targets objects. Use the Ad Product Pill selector to see Sponsored Brands.

New campaign management APIs

This document describes using Sponsored Brands-specific APIs for campaign management. However, you can now manage campaigns across different ad products using a common model and a single set of API endpoints. To get started using the common campaign model in the Amazon Ads API v1, see the campaign management overview.

## Before you begin

- Complete the Amazon Ads API Onboarding and Getting started processes to obtain your access token and profile ID. You will need these to make all the calls referenced in the tutorial.
- Understand the structure of Sponsored Brands campaigns.

Tip

If you want to test out the creation flow for Sponsored Brands campaigns without worrying about ad spend, you can create a Test account and use it to complete this tutorial.

### Step 1: Create a campaign

The first step is to create a campaign using the POST /sb/v4/campaigns endpoint.

Bidding strategies can be specified at the campaign level. Bidding can be done automatically by Amazon to optimize bids for placements other than top of search or by specifying a custom bidding adjustment.

Note

If you are a seller and your brand has been approved, you must provide a `brandEntityId`. You can get the `brandEntityId` by calling the GET /brands endpoint.

#### Goal-based campaigns

Goal-based campaigns offer a streamlined campaign creation and management workflow to enhance your campaign performance. Each goal comes with a unique set of target and bid recommendations, designed to maximize success metrics and expand opportunities to display ads and reach potential customers on Amazon.

**Parameters to create goal-based campaigns**

| Parameter | Optional | Description | Default |
| --- | --- | --- | --- |
| `goal` | Yes | The goal type of the campaign. `BRAND_IMPRESSION_SHARE` - This goal will show your ads to shoppers searching for your brand. `PAGE_VISIT` - This goal drives traffic to your landing and detail pages through all placements. | `PAGE_VISIT` |
| `costType` | Yes | The `costType` can be set to determine how the campaign will bid and charge. To view the bid maximums and minimums by geography and `costType`, see https://advertising.amazon.com/API/docs/en-us/concepts/limits#bid-constraints-by-marketplace `CPC` - Cost per click. The performance of this campaign is measured by the clicks triggered by the ad. `VCPM` - Cost per 1000 viewable impressions. The performance of this campaign is measured by the viewable impressions triggered by the ad. | `CPC` |
| `smartDefault` | Yes | The `smartDefault` parameter specifies a list of strategies for a campaign. Each element in `smartDefault` can be set to determine which default strategy to use. `MANUAL` - No default targeting is created. If `MANUAL` is added on the list, no other strategies are allowed on the list (the list must contain only one item). `TARGETING` - Theme targeting is automatically created when creating an ad group. | If no goal is present in request, `MANUAL` is set by default. If a goal is present, `TARGETING` is set by default. |

Note

Once a goal-based campaign is created, the `goal`, `costType`, and `smartDefault` values are not editable.

**Validation rules**

Both `goal` and `costType` parameters must be included in the request body in order to create a goal-based campaign. If the request body contains only one of these parameters, the response will return a validation error of `INVALID_ARGUMENT`. Depending on the goal, either a goal-based campaign focused on brand impression or driving traffic to your landing page and detail page is created along with a set of target and bid recommendations to improve campaign performance.

| Goal type | `costType` | Result |
| --- | --- | --- |
| Not included in request | Not included in request | Default goal type is `PAGE_VISIT` with a `costType` of `CPC` |
| Not included in request | Included in request | `INVALID_ARGUMENT` error |
| Included in request | Not included in request | `INVALID_ARGUMENT` error |
| Included in request | Included in request | Creates a goal-based campaign |

Note

Goal-based campaigns are not supported in the Ireland (IE) marketplace. For IE, both `goal` and `costType` must be omitted from the request body, which creates a standard (non-goal-based) campaign; the default `PAGE_VISIT` / `CPC` behavior described above does not apply. Supplying `goal` and `costType` in IE returns a `GOAL_BASED_CAMPAIGNS_DISABLED` error.

Tip

For optimized campaign performance, do **not** include any bidding optimizations (`bidOptimizationStrategy`, `bidAdjustmentsByShopperSegment`, `bidAdjustmentsByPlacement`, `bidOptimization`) when setting `smartDefault` to `TARGETING` or using a `costType` of `VCPM`.

**Sample request**

The `smartDefault` parameter with `["TARGETING"]` value automatically creates theme-based targeting based on the goal selected. In this example, the theme targeting is created with a focus on brand impression.

```
curl --location  'https://advertising-api.amazon.com/sb/v4/campaigns'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxx'  \
--header  'Accept: application/vnd.sbcampaignresource.v4+json'  \
--header  'Content-Type: application/json'  \
--data  '{
    "campaigns": [
        {
            "budgetType": "DAILY",
            "name": "Goal-based campaign",
            "state": "ENABLED",
            "startDate": "2023-08-21",
            "budget": 10,
            "goal": "BRAND_IMPRESSION_SHARE",
            "costType": "VCPM",
            "smartDefault": ["TARGETING"]
        }
    ]
}'
```

For `goal` type `BRAND_IMPRESSION_SHARE`, only `costType` `VCPM` is available. If you try to use `costType` `CPC` for goal type `BRAND_IMPRESSION_SHARE`, the following error will occur:

```
  "errors" :   [ 
                     { 
                         "errorType" :   "INVALID_ARGUMENT" , 
                         "errorValue" :   { 
                             "otherError" :   { 
                                 "cause" :   { 
                                     "location" :   "$.goal" 
                                 } , 
                                 "message" :   "Invalid goal type specified." , 
                                 "reason" :   "CAMPAIGN_GOAL_TYPE_INVALID" 
                             } 
                         } 
                     } 
                 ]
```

### Step 2: Create ad group

Create at least one ad group using the POST /sb/v4/adGroups endpoint. Use the `campaignId` returned in step 1 to create your ad group.

**Sample request**

This sample request creates an ad group associated to one campaign. A successful call returns a `207` response code and indicates the `adGroupId` of the ad group created.

```
curl --location --request POST  'https://advertising-api.amazon.com/sb/v4/adGroups'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxxxxxx'  \
--header  'Accept: application/vnd.sbadgroupresource.v4+json'  \
--data-raw  '{
"adGroups": [{
    "campaignId": "{{campaignId}}",
    "name": "My ad group name",
    "state": "ENABLED"
}]
}
'
```

### Step 3: Upload and register assets

You can upload and register a video or image asset prior to creating an ad by using the creative asset library API.

### Step 4: Create an ad

Once you have the `assetId` from the previous step, you can create an ad. The ad types are collections, video, brand video and store spotlight. There has to be at least one ad in an ad group and an ad group cannot have more than one ad type.

To learn more about the requirements for each ad type, see:

- Collections
- Video (including brand video)
- Store spotlight

**Ad restrictions when using a brand impression share goal**

If you create a campaign with a goal of `BRAND_IMPRESSION_SHARE`, you must use one of the following creative types:

- Manual collection directing to a Store landing page
- Store spotlight directing to a Store landing page
- Brand video ad pointing to a Store landing page

### Step 5: Add targeting to your ad group

Once you have created an ad in an ad group, you need to add targeting. An ad group can be associated to either product or keyword targeting expressions.

- For keyword targeting, use the POST /sb/keywords endpoint.
- For product targeting, use the POST /sb/targets endpoint.
- For theme targeting, use the POST /sb/themes endpoint.

### Step 6: Check the moderation status

You can check the moderation status of your ads by passing the `adId` as the `id` in the Moderation API.

### Step 7: Make any changes to your ads or creatives

Based on the moderation status, you may need to make changes to your ad or creative. See Managing assets and Managing campaigns for more details.
