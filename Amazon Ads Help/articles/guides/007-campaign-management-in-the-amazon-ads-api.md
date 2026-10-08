---
title: "Campaign management in the Amazon Ads API"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/overview"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-10-07"
status: "captured"
---

# Campaign management in the Amazon Ads API

The Campaign Management APIs represent functionality needed to create, read, update, and delete campaign management objects for Campaigns, Ad Groups, Ads, Targets, and Ad Associations. These Campaign Management APIs are ad product-agnostic and use the same set versioning across the board, and one set of feature naming to represent similar ideas.

The Amazon Ads API currently supports campaign management operations for:

- Amazon DSP
- Sponsored Brands
- Sponsored Products
- Sponsored Display
- Sponsored Television

## Campaign management entities

The API currently covers five entities: campaigns, ad groups, targets, ads, and ad associations.

See the entity guides overview or these individual guides for information about each entity:

| Entity | API Specification |
| --- | --- |
| Campaign | Campaign API Specification |
| Ad Group | Ad Group API Specification |
| Ad | Ad API Specification |
| Target | Target API Specification |
| Ad Association | Ad Association API Specification |

## Current limitations

### Campaign management scale

The goal is to allow multiple-ad product support within payload for writes and reads without scale differences across ad products.

- At launch, calls will be bound to one ad product at a time.
- At launch, API rate limits (TPS) will be per each ad product.

Following launch, we will:

- Enable support for multi-ad product operations in the same payload and move rate limiting to payload level, allowing mixing of ad products. This helps use cases such as bulk updates across ad products without orchestration of multiple write calls.
- Continue to increase the scaling across ad products to create a consistent TPS experience.

Please report any issues with the campaign management APIs through our contact support page.
