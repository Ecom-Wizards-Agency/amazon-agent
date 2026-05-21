---
title: "How to onboard first-party data to Amazon Ads using ADM"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
---

# How to onboard first-party data to Amazon Ads using ADM

This workshop explains how to onboard first-party data with the Ads Data Manager API and activate it across Amazon DSP and Amazon Marketing Cloud.

## What ADM enables

Amazon Ads Data Manager is a centralized platform for securely uploading first-party data and activating it across Amazon Ads products.

Key capabilities:

- Upload hashed customer lists such as emails, phones, and addresses for audience matching.
- Create DSP audiences from uploaded data.
- Share datasets with AMC for analytics and custom audience modeling.
- Track conversion events by connecting offline/online signals to campaigns.
- Manage retention controls and identity deletion for privacy compliance.

## Data flow

```text
CRM / CDP
  -> Hash PII with SHA-256
  -> Upload to ADM through API, UI, or S3
  -> Create sharing rule
  -> Activate in DSP Audiences, AMC, or Events Manager
```

## Prerequisites

Amazon Ads API credentials:

- Client ID
- Client Secret
- Refresh Token
- Manager Account ID or Advertiser ID

Python environment:

- `requests`
- `python-dotenv`

Authentication requires the client ID and bearer access token plus exactly one account identification header:

| Header | When to use |
| --- | --- |
| `Amazon-Ads-Manager-Account-ID` | Manager/agency accounts, recommended for agencies. |
| `Amazon-Ads-AccountId` | Individual advertiser accounts. |

ADM does not currently support Single Global Accounts in this workflow; use a Manager Account or individual Advertiser Account.

## Key concepts

| Concept | Description |
| --- | --- |
| Dataroom | Container for ADM data. One per account. Required before other operations. |
| Dataset | Named collection of audience records inside a dataroom. Has schema, country code, and retention settings. |
| Sharing Rule | Connects a dataset to a destination application. |
| Identity Resolution | Matching hashed PII to Amazon identities for targeting. |
| ID Retention | When enabled, hashed data is retained for 90 days and UID tokens are refreshed automatically. |

## Supported destination applications

| Application ID | Purpose |
| --- | --- |
| `DSP_AUDIENCES` | Create audiences for Amazon DSP campaigns. |
| `AMAZON_MARKETING_CLOUD` | Share data with AMC for analytics and custom queries. |
| `EVENTS_MANAGER` | Connect conversion events to campaigns. |

## Use cases

| Use case | Description |
| --- | --- |
| [Onboard First-Party Audience Data](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/01-onboard-audience-data) | Upload hashed customer lists to ADM for identity matching. |
| [Create a DSP Audience](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/02-create-dsp-audience) | Activate ADM data as targetable audiences in Amazon DSP. |
| [Share Data with AMC](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/03-share-with-amc) | Send ADM data to Amazon Marketing Cloud. |
| [Conversion Event Tracking](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/04-conversion-tracking) | Connect offline/online conversion events to campaigns. |
| [Manage Audience Lifecycle](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/05-manage-audience-lifecycle) | Update, remove members, and delete datasets. |
| [Identity Deletion for Privacy](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/06-identity-deletion) | Handle GDPR/CCPA deletion requests. |
| [Monitor Dataset Health](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/07-monitor-dataset-health) | Track match rates, record counts, and dataset metrics. |

## Reference pages

- [API Quick Reference](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/08-api-reference)
- [Troubleshooting & Best Practices](https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/09-troubleshooting)
- [Amazon Ads Data Manager Overview](https://advertising.amazon.com/API/docs/en-us/guides/ads-data-manager/get-started)
- [ADM Dataset Management Guide](https://advertising.amazon.com/API/docs/en-us/guides/ads-data-manager/dataset-management)

## Routing use

Use this page for first-party customer data onboarding, CRM/CDP audience activation, Amazon DSP audience creation, AMC data sharing, identity deletion, or dataset health monitoring.
