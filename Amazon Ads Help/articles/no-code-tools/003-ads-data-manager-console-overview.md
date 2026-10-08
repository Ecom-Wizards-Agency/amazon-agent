---
title: "Ads data manager console overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/1_ads-data-manager-console-overview"
library: "Amazon Ads Advanced Tools Center"
section: "no-code-tools"
downloaded_at: "2026-10-07"
status: "captured"
---

# Overview

Ads data manager is an Amazon Ads offering with options that enable advertisers to securely upload their first-party (1P) data to Amazon Ads using either an intuitive user interface (Ads data manager console) or Ads data manager APIs. The uploaded data can be mapped to the required inputs needed to activate their data across Amazon Ads products and then shared for planning and measurement use cases to gain insights and help you optimize campaigns and create audiences.

Designed for data stewards, data owners, marketers, or programmatic teams that have access to use their 1P data; Ads data manager facilitates use of advertiser first-party data within Amazon Ads, and enables the hand-off of data brought to Amazon between multiple accounts. For example, data can be shared from a manager account to campaign managers who do not handle 1P party data directly but are required to include this data in campaign setup for attribution or targeting purposes.

## Manager accounts and advertiser account hierarchy

Ads data manager operates at the manager account and advertiser account for advertisers with Display, Video, and Audio campaign access, allowing for centralized data management. When you link advertiser accounts to your manager account you can manage your uploaded data in a centralized location without exposing direct record-level access to your data across advertiser accounts.

Know more about manager accounts using the Ads console.

The image below illustrates how manager accounts function within the Amazon Ads account hierarchy using Kitchen Smart, a kitchen appliances company. In our example, Kitchen Smart operates from US and Europe .

- Datasets can be uploaded to a parent manager account like “**Kitchen Smart Global**", under which child manager accounts for “**Kitchen Smart US**” and “**Kitchen Smart EU**” are created.
- These manager accounts then serve as a central repository for data upload and management.
- The uploaded data can be shared on-demand with the linked advertiser accounts connected with the manager account.

This setup enables efficient first-party data management, where data uploaded once at the manager account level can be utilized across multiple linked advertiser accounts. And, the structure allows for streamlined data operations, ensuring that advertisers can use their uploaded data across accounts while maintaining control over data access and usage within the Amazon Ads.

Note

While data uploaded to Ads data manager is managed centrally at the manager account level, a destination is used to determine which datasets are available across linked advertiser accounts.

**Data sharing links do not cascade and are not inherited**. For example, if Kitchen Smart EU has an active data sharing link, the parent Kitchen Smart Global and its directly linked Advertiser Accounts do not have any data access, nor will any new advertiser accounts added directly to Kitchen Smart Global have access to the data Kitchen Smart EU has access to. Additionally if Kitchen Smart Global has data uploaded, and its children manager accounts like Kitchen Smart US have data sharing links, data will not be shared since the data lives at the parent level while sharing rules are at the child manager account level. Data sharing links will only provide data access when a manager account is directly linked to an advertiser account with the `data sharing` permission through **Account access and settings** > **Manager accounts** > **Account permission**.
