---
title: "Campaign management in the Amazon Ads API"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/overview"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Campaign management in the Amazon Ads API

Campaign Management APIs cover creation, reading, updating, and deletion for campaign objects across Campaigns, Ad Groups, Ads, Targets, and Ad Associations.

Amazon describes the current campaign management model as ad product-agnostic, with common versioning and feature naming across supported ad products.

## Supported ad products

- Amazon DSP
- Sponsored Brands
- Sponsored Products
- Sponsored Display
- Sponsored Television

## Entities

| Entity | Guide | API specification |
| --- | --- | --- |
| Campaign | [Campaign entity guide](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/campaign) | [Campaign API specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis#tag/Campaigns) |
| Ad Group | [Ad Group entity guide](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/ad-group) | [Ad Group API specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis#tag/AdGroups) |
| Ad | [Ad entity guide](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/ad) | [Ad API specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis#tag/Ads) |
| Target | [Target entity guide](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/target) | [Target API specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis#tag/Targets) |
| Ad Association | [Ad Association entity guide](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/ad-association) | [Ad Association API specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis#tag/AdAssociations) |

## Current limitations

- At launch, calls are bound to one ad product at a time.
- At launch, API rate limits are per ad product.
- Amazon's stated direction is multi-ad-product operations in the same payload, with rate limiting moving to the payload level.

## Routing use

Use this page when the task is about cross-product campaign entity operations, especially when choosing whether to use the newer common campaign management model instead of older Sponsored Brands, Sponsored Products, Sponsored Display, or DSP-specific endpoints.

## Related pages

- [Entity guides overview](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/overview)
- [Example request payloads](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/example-payloads)
- [Amazon Ads API reference overview](https://advertising.amazon.com/API/docs/en-us/reference/amazon-ads/overview)
- [Support](https://advertising.amazon.com/API/docs/en-us/support/overview)
