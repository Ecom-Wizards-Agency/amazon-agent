---
title: "Amazon Ads API v1 overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/reference/amazon-ads/overview"
library: "Amazon Ads Advanced Tools Center"
section: "reference"
downloaded_at: "2026-05-13"
status: "captured"
---

# Amazon Ads API v1 overview

Amazon Ads API v1 is Amazon's common model for advertising APIs. It is designed to provide consistent concepts, naming, and behavior across Sponsored Products, Sponsored Brands, Sponsored Display, Sponsored Television, and Amazon DSP.

Amazon recommends v1 for new Ads API users and says it will eventually replace ad product-specific APIs.

## Getting started

| Need | Page |
| --- | --- |
| v1 prerequisites, headers, and access | [Get started with Amazon Ads API v1](https://advertising.amazon.com/API/docs/en-us/reference/amazon-ads/getting-started) |
| Campaign management | [Campaign management overview](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/overview) |
| Entity model | [Campaign management entities overview](https://advertising.amazon.com/API/docs/en-us/guides/campaign-management/entities/overview) |
| API specification | [Amazon Ads API v1 specification](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis) |

## Key benefits

- Consistent field names, error handling, and resource patterns.
- Less duplicated implementation work across ad products.
- One integration pattern for multiple ad products.
- Future features and ad products are intended to use the common framework.
- Predictable versioning, support windows, and deprecation timelines.

## Developer experience

Amazon highlights:

- Consistent error codes and messaging.
- Simpler documentation and implementation guides.
- Reusable code patterns.
- Faster adoption of new features.
- Consistent OAS files and namespacing for client generation.

## General availability and beta releases

- Beta v1 APIs are listed under [Betas](https://advertising.amazon.com/API/docs/en-us/developer/betas).
- Released APIs are visible in the [v1 API spec](https://advertising.amazon.com/API/docs/en-us/amazon-ads/1-0/apis).
- Updates are tracked in [API v1 release notes](https://advertising.amazon.com/API/docs/en-us/release-notes/ads-api).

## Future expansion areas

Amazon says the long-term vision is to generate Ads API v1 APIs from a common domain model. Areas expected to expand include:

- Reporting
- Recommendations
- Rules
- Media planning

## Routing use

Use this page as the default route for new Amazon Ads API development or when a user asks whether to use legacy product-specific APIs versus the common model. For frontend console tasks, still route through Seller Central/Amazon Ads UI SOPs first; use this page when API automation is appropriate.
