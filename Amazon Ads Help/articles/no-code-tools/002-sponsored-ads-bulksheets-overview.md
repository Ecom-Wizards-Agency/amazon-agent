---
title: "Bulksheets overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/no-code-tools/bulksheets/2-0/overview-about-bulksheets"
library: "Amazon Ads Advanced Tools Center"
section: "no-code-tools"
downloaded_at: "2026-10-07"
status: "captured"
---

# Bulksheets overview

This article provides a high-level overview of the new bulksheets, including key improvements, FAQs, and some examples of managing campaigns using the new template. When you are ready to learn more, check out the getting started guide.

Important

Legacy bulksheets has been deprecated effective September 28, 2023. Effective immediately, the legacy template will not work, and you must use the new version to continue managing sponsored ads campaigns using bulksheets.

## Overview

Bulksheets is a spreadsheet-based tool that allows sponsored ads advertisers to create and optimize multiple campaigns in batches, reducing time and manual effort. Bulksheets can be a good option if you have already been using the advertising console, but want more robust functionality and the ability to scale without calling the API.

## Key features

With bulksheets, you can

- Update campaign names and ad group names in large batches instead of one by one
- Optimize campaigns by updating thousands of keywords, product targeting, and bids at once
- See performance metrics such as impressions, clicks and click-through rates, conversions, ACOS, CPC, and ROAS
- Download and view search term reports for Sponsored Products
- Add multiple ad groups to a single campaign from the same bulksheets file

## Frequently asked questions

Can I use a legacy template with the new version?

No. If you upload a legacy spreadsheet, you will see errors. You can check out a side-by-side comparison of the two templates here for an idea of the differences between the previous template and the latest version.

Should I download a custom spreadsheet or use the blank template format?

Either option will work. If you create and download a custom spreadsheet the file will contain past campaign data and additional columns with read-only data and performance metrics. These additional columns will not affect the upload, so you can leave them intact if you use the downloaded custom spreadsheet. If you start with the blank template, you will see fewer columns and no pre-filled data. The examples below will give you an idea of what each scenario would look like, and you can see more details in the overview for updating campaigns.

Are there other formatting rules I should be aware of?

Yes, review these tips about formatting in bulksheet:
**Dates**: For campaign start and end dates, the format must be `YYYYMMDD`. December 17, 2023 would be entered as 20231217.
**Percentages**: Numbers intended to be percentages should be entered as whole numbers, with no symbols or decimals. A bidding adjustment of 25% would be entered as 25.
**Percentages exception for Sponsored Brands**: Due to the API structure of Sponsored Brands, you should use the percentage symbol to define a bid multiplier for Sponsored Brands campaigns, either a positive or negative value. For instance, a forty percent multiplier would be written as 40%. A negative sixty percent multiplier would be -60%. Learn more about creating Sponsored Brands campaigns in bulksheets.
**Commas**: Numbers should not include commas. For instance, when writing fifteen hundred, you would write 1500 (NOT 1,500).
**Bid**: For the CPC bid amount, do not use money symbols or commas. For example, to bid 75 cents, enter **0.75**. To bid one dollar, enter **1**. Also, there is a 2-place decimal limit. If you enter a number with more than 2 decimal places, we will automatically round to a 2-place decimal figure. For example, if you enter 0.756, we will round to 0.76. If you enter 0.754, we will round to 0.75
**Portfolios**: When you create a new portfolio, the first two fields (Product and Entity) require strict formatting. The “Product” field should include **Portfolios** (plural, with the “s”). The “Entity” field should include **Portfolio** (singular, without the “s”).

Where can I find more information about using bulksheets?

We recommend starting with the getting started guide.

## Example scenarios

Here are some examples of creating, updating, and archiving campaign entities using bulksheets. For more details on how to create and manage campaigns with bulksheets, refer to the getting started guide.

Tip

In the rows where the "Operation" field is blank, those entities will be ignored in the bulk upload and will remain unchanged. This lets you keep data in the sheet if you do not want to update it, and will make the upload more efficient because the rows will not be processed.

**Note:** In the examples below, blank values in the Sites column represent the default site setting.

#### Example 1. Update a campaign and ad group name using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | Portfolio ID | Ad ID (Read only) | Keyword ID (Read only) | Product Targeting ID (Read only) | Campaign Name | Ad Group Name | Start Date | End Date | Targeting Type | State | Daily Budget | SKU | ASIN | Ad Group Default Bid | Bid | Keyword Text | Match Type | Bidding Strategy | Placement | Percentage | Product Targeting Expression | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Update | 2270350216 |  |  |  |  |  | New Campaign Name 1 |  | 20220325 | 20221231 | AUTO | enabled | 15 |  |  |  |  |  |  | Dynamic bids - up and down |  |  |  |  |
| Sponsored Products | Ad Group | Update | 2270350216 | 1764163005 |  |  |  |  |  | New Ad Group Name 1 |  |  |  | enabled |  |  |  | 0.5 |  |  |  |  |  |  |  |  |
| Sponsored Products | Product Ad |  | 2270350216 | 1764163005 |  | 1626147106 |  |  |  |  |  |  |  | enabled |  |  | B01N05APQY |  |  |  |  |  |  |  |  |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  | 1475350320 |  |  |  |  |  | paused |  |  |  |  |  |  |  |  |  |  | close-match |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  | 15431673257 |  |  |  |  |  | enabled |  |  |  |  |  |  |  |  |  |  | loose-match |  |
| Sponsored Products | Ad Group |  | 2270350216 | 472947394 |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.25 |  |  |  |  |  |  |  |  |
| Sponsored Products | Campaign |  | 193847192 |  |  |  |  |  |  |  | 20220411 |  | Auto | enabled | 10 |  |  |  |  |  |  | Fixed bid |  |  |  |  |
| Sponsored Products | Ad Group |  | 193847192 | 2294632947 |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.75 |  |  |  |  |  |  |  |  |

#### Example 2. Create a new campaign and ad group using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | Portfolio ID | Ad ID (Read only) | Keyword ID (Read only) | Product Targeting ID (Read only) | Campaign Name | Ad Group Name | Start Date | End Date | Targeting Type | State | Daily Budget | SKU | ASIN | Ad Group Default Bid | Bid | Keyword Text | Match Type | Bidding Strategy | Placement | Percentage | Product Targeting Expression | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Create | SP Campaign Name 2 |  |  |  |  |  | SP Campaign Name 2 |  | 20220411 |  | Auto | enabled | 10 |  |  |  |  |  |  | Fixed bid |  |  |  | Amazon Business |
| Sponsored Products | Ad Group | Create | SP Campaign Name 2 | Ad Group Name 2 |  |  |  |  |  | Ad Group Name 2 |  |  |  | enabled |  |  |  | 0.75 |  |  |  |  |  |  |  |  |
| Sponsored Products | Campaign |  | 2270350216 |  |  |  |  |  |  |  | 20220325 | 20221231 | AUTO | enabled | 15 |  |  |  |  |  |  | Dynamic bids - up and down |  |  |  |  |
| Sponsored Products | Ad Group |  | 2270350216 | 1764163005 |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.5 |  |  |  |  |  |  |  |  |
| Sponsored Products | Product Ad |  | 2270350216 | 1764163005 |  | 1626147106 |  |  |  |  |  |  |  | enabled |  |  | B01N05APQY |  |  |  |  |  |  |  |  |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  | 1475350320 |  |  |  |  |  | paused |  |  |  |  |  |  |  |  |  |  | close-match |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  | 15431673257 |  |  |  |  |  | enabled |  |  |  |  |  |  |  |  |  |  | loose-match |  |
| Sponsored Products | Ad Group |  | 2270350216 | 472947394 |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.25 |  |  |  |  |  |  |  |  |

#### Example 3. Create a new auto-targeting campaign with bidding adjustment and ad group using the blank template

| Product | Entity | Operation | Campaign ID | Ad Group ID | Portfolio ID | Ad ID | Keyword ID | Product Targeting ID | Campaign Name | Ad Group Name | Start Date | End Date | Targeting Type | State | Daily Budget | SKU | ASIN | Ad Group Default Bid | Bid | Keyword Text | Match Type | Bidding Strategy | Placement | Percentage | Product Targeting Expression | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Campaign | Create | Spring toys 2022 |  |  |  |  |  | Spring toys 2022 |  | 20220401 |  | Auto | Enabled | 100 |  |  |  |  |  |  | Fixed bid |  |  |  | Amazon Business |
| Sponsored Products | Bidding adjustment | Create | Spring toys 2022 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | Fixed bid | placementTop | 35 |  |  |
| Sponsored Products | Ad group | Create | Spring toys 2022 | Outdoors |  |  |  |  |  | Outdoors |  |  |  | Enabled |  |  |  | 0.75 |  |  |  |  |  |  |  |  |

#### Example 4. Archive a product ad (`ASIN`) and update product targeting using a downloaded custom spreadsheet

| Product | Entity | Operation | Campaign ID | Ad Group ID | Portfolio ID | Ad ID (Read only) | Keyword ID (Read only) | Product Targeting ID (Read only) | Campaign Name | Ad Group Name | Start Date | End Date | Targeting Type | State | Daily Budget | SKU | ASIN | Ad Group Default Bid | Bid | Keyword Text | Match Type | Bidding Strategy | Placement | Percentage | Product Targeting Expression | Sites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sponsored Products | Product Ad | Archive | 2270350216 | 1764163005 |  | 1626147106 |  |  |  |  |  |  |  | enabled |  |  | B01N05APQY |  |  |  |  |  |  |  |  |  |
| Sponsored Products | Product Targeting | Update | 2270350216 | 1764163005 |  |  |  | 1475350320 |  |  |  |  |  | paused |  |  |  |  |  |  |  |  |  |  | close-match |  |
| Sponsored Products | Product Targeting |  | 2270350216 | 1764163005 |  |  |  | 15431673257 |  |  |  |  |  | enabled |  |  |  |  |  |  |  |  |  |  | loose-match |  |
| Sponsored Products | Ad Group |  | 2270350216 | Add New Ad Group |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.25 |  |  |  |  |  |  |  |  |
| Sponsored Products | Campaign |  | 193847192 |  |  |  |  |  |  |  | 20220411 |  | Auto | enabled | 10 |  |  |  |  |  |  | Fixed bid |  |  |  |  |
| Sponsored Products | Ad Group |  | 193847192 | 2294632947 |  |  |  |  |  |  |  |  |  | enabled |  |  |  | 0.75 |  |  |  |  |  |  |  |  |
