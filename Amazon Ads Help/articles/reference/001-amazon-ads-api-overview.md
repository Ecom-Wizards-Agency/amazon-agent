---
title: "Amazon Ads API overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/reference/api-overview"
library: "Amazon Ads Advanced Tools Center"
section: "reference"
downloaded_at: "2026-05-13"
status: "captured"
---

# Amazon Ads API overview

The Amazon Ads API lets advertisers and partners programmatically manage advertising operations and retrieve performance data.

Use the API reference navigation for endpoint details. Use the Developer guides for workflows, recommendations, and tutorials.

## First steps

| Need | Page |
| --- | --- |
| Apply and gain access | [Onboarding](https://advertising.amazon.com/API/docs/en-us/guides/onboarding/overview) |
| Manage authorization and make first requests | [Getting started](https://advertising.amazon.com/API/docs/en-us/guides/get-started/overview) |
| New common API model | [Amazon Ads API v1](https://advertising.amazon.com/API/docs/en-us/reference/amazon-ads/overview) |

Amazon recommends Amazon Ads API v1 for new API users.

## Typical use cases

Amazon expects a typical client to regularly:

1. Make batch requests for campaigns, ad groups, ads, and keywords in paginated requests, then store/update a local data copy.
2. Request recent performance data through reports, then join report data to locally stored entity IDs.
3. Analyze performance and update bids and budgets through batch update APIs.

Single-entity operations are also supported.

## Regional endpoints

| URL | Region | Marketplaces |
| --- | --- | --- |
| `https://advertising-api.amazon.com` | North America (NA) | US, CA, MX, BR |
| `https://advertising-api-eu.amazon.com` | Europe (EU) | UK, FR, IT, ES, DE, NL, AE, PL, TR, EG, SA, SE, BE, IN, ZA |
| `https://advertising-api-fe.amazon.com` | Far East (FE) | JP, AU, SG |

## Routing use

Use this page when deciding which regional endpoint or high-level API reference section applies. For campaign build/update tasks, route onward to API v1 and Campaign Management unless an older product-specific API is required.
