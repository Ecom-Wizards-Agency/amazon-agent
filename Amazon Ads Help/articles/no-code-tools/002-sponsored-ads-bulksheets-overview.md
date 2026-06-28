---
title: "Bulksheets overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/overview-about-bulksheets"
library: "Amazon Ads Advanced Tools Center"
section: "no-code-tools"
downloaded_at: "2026-05-13"
status: "captured"
---

# Bulksheets overview

Bulksheets is a spreadsheet-based tool for sponsored ads advertisers to create and optimize multiple campaigns in batches, reducing time and manual effort. It is useful for advertisers already using the advertising console who want more robust functionality and scale without calling the API.

> Important: Legacy bulksheets was deprecated effective September 28, 2023. The legacy template no longer works.

## Key features

With bulksheets, advertisers can:

- Update campaign names and ad group names in large batches.
- Optimize campaigns by updating thousands of keywords, product targets, and bids.
- See performance metrics such as impressions, clicks, CTR, conversions, ACOS, CPC, and ROAS.
- Download and view search term reports for Sponsored Products.
- Add multiple ad groups to a single campaign from the same bulksheets file.

## Frequently asked questions

### Can I use a legacy template with the new version?

No. Legacy spreadsheet uploads return errors.

### Should I download a custom spreadsheet or use the blank template?

Either works. A downloaded custom spreadsheet includes past campaign data, read-only fields, and performance metrics. Those extra columns do not affect upload. A blank template has fewer columns and no pre-filled data.

### Formatting rules

| Field type | Rule |
| --- | --- |
| Dates | Use `YYYYMMDD`. Example: December 17, 2023 is `20231217`. |
| Percentages | Use whole numbers without symbols or decimals. A 25% bidding adjustment is `25`. |
| Sponsored Brands bid multipliers | Use `%` for Sponsored Brands bid multipliers. Examples: `40%`, `-60%`. |
| Commas | Do not use commas in numbers. Use `1500`, not `1,500`. |
| Bid | Do not use currency symbols or commas. `0.75` means 75 cents. `1` means one dollar. Bids are limited to 2 decimal places and are rounded if needed. |
| Portfolios | For new portfolios, `Product` must be `Portfolios` and `Entity` must be `Portfolio`. |

## Upload behavior tip

Rows where the **Operation** field is blank are ignored during bulk upload and remain unchanged. This allows unchanged data to stay in the sheet while making the upload more efficient.

## Example scenarios captured from Amazon

### Example 1. Update a campaign and ad group name using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | Campaign Name | Ad Group Name | Start Date | End Date | Targeting Type | State | Daily Budget | Ad Group Default Bid | Bidding Strategy | Product Targeting Expression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Update | 2270350216 |  | New Campaign Name 1 |  | 20220325 | 20221231 | AUTO | enabled | 15 |  | Dynamic bids - up and down |  |
| Sponsored Products | Ad Group | Update | 2270350216 | 1764163005 |  | New Ad Group Name 1 |  |  |  | enabled |  | 0.5 |  |  |
| Sponsored Products | Product Ad |  | 2270350216 | 1764163005 |  |  |  |  |  | enabled |  |  |  |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  |  |  | paused |  |  |  | close-match |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  |  |  | enabled |  |  |  | loose-match |

### Example 2. Create a new campaign and ad group using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | Campaign Name | Ad Group Name | Start Date | Targeting Type | State | Daily Budget | Ad Group Default Bid | Bidding Strategy | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Create | SP Campaign Name 2 |  | SP Campaign Name 2 |  | 20220411 | Auto | enabled | 10 |  | Fixed bid | Amazon Business |
| Sponsored Products | Ad Group | Create | SP Campaign Name 2 | Ad Group Name 2 |  | Ad Group Name 2 |  |  | enabled |  | 0.75 |  |  |

### Example 3. Create a new auto-targeting campaign with bidding adjustment and ad group using the blank template

| Product | Entity | Operation | Campaign ID | Campaign Name | Ad Group Name | Start Date | Targeting Type | State | Daily Budget | Ad Group Default Bid | Bidding Strategy | Placement | Percentage | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Create | Spring toys 2022 | Spring toys 2022 |  | 20220401 | Auto | Enabled | 100 |  | Fixed bid |  |  | Amazon Business |
| Sponsored Products | Bidding adjustment | Create | Spring toys 2022 |  |  |  |  |  |  |  | Fixed bid | placementTop | 35 |  |
| Sponsored Products | Ad group | Create | Spring toys 2022 |  | Outdoors |  |  | Enabled |  | 0.75 |  |  |  |  |

### Example 4. Archive a product ad and update product targeting using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | State | ASIN | Product Targeting Expression |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Product Ad | Archive | 2270350216 | 1764163005 | enabled | B01N05APQY |  |
| Sponsored Products | Product Targeting | Update | 2270350216 | 1764163005 | paused |  | close-match |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 | enabled |  | loose-match |

## Related docs

- [Getting started guide](https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/get-started-with-bulksheets-part1)
- [Overview for updating campaigns](https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/campaign-update-overview)
- [Creating Sponsored Brands campaigns in bulksheets](https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/create-sb-campaign)
