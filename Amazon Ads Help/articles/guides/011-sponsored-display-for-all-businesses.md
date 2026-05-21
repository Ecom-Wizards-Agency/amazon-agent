---
title: "Get started with Sponsored Display for all businesses"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/non-amazon-sellers/get-started"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Get started with Sponsored Display for all businesses

This guide covers Sponsored Display campaigns for advertisers who do not sell in the Amazon store and want to advertise products or services not sold on Amazon in categories not already available on Amazon.com.

Visual reference:

![Sponsored Display architecture for advertisers who do not sell on Amazon](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/sponsored-display/non-endemic-architecture.png)

## Onboarding flow

| Step | Action | Notes |
| --- | --- | --- |
| 1 | Join Amazon Ads Partner Network | Create an Amazon Business Account through the Partner Network registration flow. |
| 2 | Create Login with Amazon account | Required for Ads API access and app authorization. |
| 3 | Create Amazon Ads Partner Network account | Required for business registration. |
| 4 | Wait for approval | Amazon notes email notification can take 1-2 business days. |
| 5 | Create a manager account | Needed for account management and advertiser onboarding. |
| 6 | Complete API onboarding | Follow standard Ads API onboarding. |
| 7 | Authorize the LwA application | Connect app authorization to the relevant manager/advertiser flow. |
| 8 | Accept Ads Agreement | Required before campaign use. |
| 9 | Register account and billing | Billing must be configured before serving ads. |

## Campaign creation workflow

The page is long and code-heavy; this local capture preserves the operational map rather than executable credential examples.

| Step | Action | Notes |
| --- | --- | --- |
| 1 | Create campaign | Uses Sponsored Display campaign resource. |
| 2 | Create one or more ad groups | Configure `bidOptimization` and `creativeType`. |
| 3 | Add locations, optional | Location targeting is available for this advertiser type. |
| 4 | Add targeting | Targeting is required before serving. |
| 5 | Create one or more product ads | Ads point to the landing page/offer being advertised. |
| 6a | Add creative assets to an ad | Include creative asset IDs, versions, and crop coordinates. |
| 6b | Add multiple images to creatives | Carousel-style creatives can use multiple images. |
| 7 | Optional pre-moderation | Use pre-moderation for real-time policy guidance before final moderation. |
| 8 | Moderation check | Ads can remain pending review for up to 72 hours. |

## Creative image requirements

For multiple image creatives, Amazon requires crop coordinates for all three aspect ratios.

| Aspect ratio object | Minimum pixels |
| --- | --- |
| `horizontalImage` | 1200 x 628 px |
| `squareImage` | 628 x 628 px |
| `verticalImage` | 353 x 628 px |

Amazon recommends using one horizontal source image and applying crop coordinates for the other aspect ratios when possible.

## Creative fields to preserve

Creative objects can include:

- `headline`
- `brandLogo`
- `assetId`
- `assetVersion`
- `croppingCoordinates`
- `horizontalImages`
- `squareImages`
- `verticalImages`
- `backgrounds`
- `color`

## Pre-moderation

The unified pre-moderation API gives real-time guidance based on technical, creative, and policy components of an ad. Amazon positions it as a way to reduce rejections for punctuation, grammar, spelling, capitalization, and spacing issues.

## Moderation checks

Moderation is required before ads serve. While moderation is in progress, the ad can be in pending review for up to 72 hours.

Moderation checks covered:

| Check | API/source | Notes |
| --- | --- | --- |
| Ad landing page moderation | `POST /moderation/results` | Uses `adProgramType: SPONSORED_DISPLAY` and `idType: AD_ID`. |
| Creative moderation by creative ID | `GET /sd/creatives` with creative ID filter | Returns moderation status and policy violations. |
| Creative moderation by ad group ID | `GET /sd/creatives` with ad group filter | Returns creatives under the ad group and moderation status. |

Moderation statuses include `APPROVED` and `REJECTED`.

Rejected moderation responses can include:

- `policyDescription`
- `policyLinkUrl`
- `violatingTextContents`
- `violatingImageContents`
- `violatingVideoContents`
- `violatingAsinContents`
- Image crop evidence for violating creative areas

## Reporting note

Use the reporting API to view campaign performance. Amazon notes that small impression and click restatements may happen up to 3 days after the original click date because of traffic validation. Retrieve click and impression data again after three days for the latest data.

## Routing use

Use this page when the user asks about Sponsored Display campaigns for non-Amazon sellers, external landing pages, advertiser onboarding, location setup, creative crop requirements, or moderation diagnostics.

## Related pages

- [Sponsored Display overview](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/overview)
- [Locations](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/non-amazon-sellers/locations)
- [Creatives](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/creatives)
- [Brand safety](https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/brand-safety)
- [Pre-moderation guide](https://advertising.amazon.com/API/docs/en-us/guides/moderation/pre-moderation)
- [Get started with reporting](https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/get-started)
