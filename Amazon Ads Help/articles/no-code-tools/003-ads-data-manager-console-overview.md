---
title: "Ads data manager console overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/1_ads-data-manager-console-overview"
library: "Amazon Ads Advanced Tools Center"
section: "no-code-tools"
downloaded_at: "2026-05-13"
status: "captured"
---

# Ads data manager console overview

Ads data manager is an Amazon Ads offering for securely uploading first-party data to Amazon Ads through either:

- [Ads data manager console](https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/2_ads-data-manager-console)
- [Ads data manager APIs](https://advertising.amazon.com/API/docs/en-us/guides/ads-data-manager/get-started)

Uploaded data can be mapped to required inputs for activation across Amazon Ads products and shared for planning and measurement use cases.

![Ads data manager overview](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/ads-data-manager/adm_overview.png)

Ads data manager is designed for data stewards, data owners, marketers, and programmatic teams that can use first-party data. It supports handoff of data brought to Amazon between multiple accounts.

Example: data can be shared from a manager account to campaign managers who do not directly handle first-party data but need it for attribution or targeting.

## Manager accounts and advertiser account hierarchy

Ads data manager operates at the [manager account](https://advertising.amazon.com/help/GU3YDB26FR7XT3C8) level for centralized data management.

When advertiser accounts are linked to a manager account, uploaded data can be managed centrally without exposing record-level data access across advertiser accounts.

![Ads data manager sharing example](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/ads-data-manager/adm_sharing.png)

Amazon's example:

- Datasets can be uploaded to a parent manager account such as **Kitchen Smart Global**.
- Child manager accounts such as **Kitchen Smart US** and **Kitchen Smart EU** can exist under the parent.
- Manager accounts serve as a central repository for data upload and management.
- Uploaded data can be shared on demand with advertiser accounts linked to the manager account.

## Important data-sharing behavior

While data uploaded to Ads data manager is managed centrally at the manager account level, a destination determines which datasets are available across linked advertiser accounts.

Data sharing links do not cascade and are not inherited.

Example:

- If **Kitchen Smart EU** has an active data sharing link, the parent **Kitchen Smart Global** and directly linked advertiser accounts do not automatically have access.
- New advertiser accounts added directly to **Kitchen Smart Global** do not automatically access data that **Kitchen Smart EU** has access to.
- If data lives at **Kitchen Smart Global** but sharing rules are configured at a child manager account, data is not shared from parent to child by inheritance.

Data sharing links provide data access only when a manager account is directly linked to an advertiser account with the `data sharing` permission through:

**Account access and settings > Manager accounts > Account permission**

## Related docs

- [Ads data manager console](https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/2_ads-data-manager-console)
- [Manage Ads data manager account](https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/2a_ads-data-manager_account_setup)
- [Activate data in destination platforms](https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/6_adm-manage-data)
- [Destinations](https://advertising.amazon.com/API/docs/en-us/no-code-tools/adm/7_adm-destinations)
