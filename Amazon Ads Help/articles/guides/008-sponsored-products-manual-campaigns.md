---
title: "Get started with manual Sponsored Products campaigns"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-products/get-started/manual-campaigns"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-10-07"
status: "captured"
---

# Get started with manual campaigns

Manual campaigns give advertisers full control over targeting, including manually creating product targeting expressions and adding keywords. If you are new to creating Sponsored Products campaigns, we recommend starting with an auto campaign.

Tip

If you want to test out the creation flow for Sponsored Products campaigns without worrying about ad spend, you can create a Test account and use it to complete this tutorial.

## Before you begin

- Complete the Amazon Ads API Onboarding and Getting started processes to obtain your access token and profile ID. You will need these to make all the calls referenced in the tutorial.
- Understand the general structure for Sponsored Products campaigns.
- (Optional) Create an auto campaign so you can identify keywords or targeting expressions to use in your manual campaign.

## Steps

1. Create a campaign using the POST /adsApi/v1/create/campaigns endpoint. To create a manual campaign, make sure `autoCreateTargets` is set to `false` in the `autoCreationSettings`.
  - More information on creating campaigns.
2. Create at least one ad group using the POST /adsApi/v1/create/adGroups endpoint. Each ad group should contain one or more products that share similar characteristics (for example, price, category, genre).
  - More information on creating ad groups.
3. Create at least one product ad per ad group using the POST /adsApi/v1/create/ads endpoint.
  - More information on creating product ads.
4. Add targeting to the ad group. Ad groups for manual campaigns must have at least one associated targeting expression (product or category) or keyword.
  - **Product targeting**
    1. Get recommended `ASIN`s to target using the POST /sp/targets/products/recommendations endpoint. Learn more.
    2. Get bid recommendations for the targeting expression using the POST /sp/targets/bid/recommendations endpoint.
    3. Create a product targeting expression using the POST /adsApi/v1/create/targets endpoint. Learn more.
  - **Category targeting**
    1. Explore available categories using the GET /sp/targets/categories endpoint, or get suggested categories to target using the POST /sp/targets/categories/recommendations endpoint.
    2. Explore what refinements are available for your desired categories (brands, age ranges, genres) using the GET sp/targets/category/{categoryId}/refinements endpoint.
    3. Check the size of category with refinements using the POST /sp/targets/products/count.
    4. Get bid recommendations for the targeting expression using the POST /sp/targets/bid/recommendations endpoint.
    5. Create one or more category targeting expressions using the POST /adsApi/v1/create/targets endpoint. Learn more.
  - **Keyword targeting**
    1. Get recommended keywords and bids using the POST /sp/targets/keywords/recommendations endpoint.
    2. Create one or more keywords using the POST /adsApi/v1/create/targets endpoint. Learn more.
5. (Optional) Set up negative targeting. You can use negative keyword targeting or negative product targeting to stop ads from showing on certain search results, brands, or product detail pages. Negative targets can be applied at the campaign and ad group level. All negative targets are also created through the targets API POST /adsApi/v1/create/targets by setting the `negative` field to `true`.
  - More information on negative keywords.
  - More information on negative product targeting.

Once you have created at least one active campaign, ad group, product ad, and targeting expression or keyword, your campaign is considered complete and ready to run. If the campaign start date is set to today and all entities have an `ACTIVE` status, your campaign starts serving immediately.
