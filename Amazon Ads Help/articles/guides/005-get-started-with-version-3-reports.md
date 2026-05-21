---
title: "Get started with version 3 reports"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/get-started"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Get started with version 3 reports

Version 3 reports are asynchronous. The operational flow is:

1. Request a report.
2. Wait for Amazon to generate it.
3. Download the completed report from the generated URL.

## Headers

| Parameter | Description |
| --- | --- |
| `Amazon-Ads-ClientId` | Client ID associated with the Login with Amazon application. |
| `Authorization` | Access token. |
| `Amazon-Advertising-API-Scope` | Profile ID for the advertising account and marketplace. Use the correct regional base URL for that marketplace. |
| `Content-Type` | `application/vnd.createasyncreportrequest.v3+json` |

## Reporting account header

For reporting across ad products, Amazon documents `Amazon-Ads-AccountId` as required across ADSP, Sponsored Products, Sponsored Brands, and Sponsored Display.

For ADSP, get the value from either:

- DSP Advertisers API, using the desired `advertiserId`.
- Manager Accounts API, using the `dspAdvertiserId` of a linked account.

For Sponsored Products, Sponsored Brands, and Sponsored Display reporting, use the reporting onboarding docs for the correct account ID source.

## Requesting reports

Endpoint:

```text
POST /reporting/reports
```

Report requests support report types, time periods, metrics, filters, and groupings. Report support depends on the selected report type.

### `timeUnit`

| Value | Column guidance |
| --- | --- |
| `DAILY` | Include `date` in the column list. |
| `SUMMARY` | Can include `startDate` and `endDate` in the column list. |

Summary request body:

```json
{
  "name": "SP campaigns report 7/5-7/10",
  "startDate": "2022-07-05",
  "endDate": "2022-07-10",
  "configuration": {
    "adProduct": "SPONSORED_PRODUCTS",
    "groupBy": ["campaign"],
    "columns": ["impressions", "clicks", "cost", "campaignId", "startDate", "endDate"],
    "reportTypeId": "spCampaigns",
    "timeUnit": "SUMMARY",
    "format": "GZIP_JSON"
  }
}
```

Daily request body:

```json
{
  "name": "SP campaigns report 7/5-7/10",
  "startDate": "2022-07-05",
  "endDate": "2022-07-10",
  "configuration": {
    "adProduct": "SPONSORED_PRODUCTS",
    "groupBy": ["campaign"],
    "columns": ["impressions", "clicks", "cost", "campaignId", "date"],
    "reportTypeId": "spCampaigns",
    "timeUnit": "DAILY",
    "format": "GZIP_JSON"
  }
}
```

### `groupBy`

Every v3 report request requires `groupBy`. It controls the granularity of the report. Some report types support multiple `groupBy` values.

### Filters

Filters are determined at the `groupBy` level. Only use a filter that is supported by every `groupBy` value in the configuration.

```json
{
  "name": "SP campaigns report 7/5-7/10",
  "startDate": "2022-07-05",
  "endDate": "2022-07-10",
  "configuration": {
    "adProduct": "SPONSORED_PRODUCTS",
    "groupBy": ["campaign"],
    "columns": ["impressions", "clicks", "cost", "campaignId", "startDate", "endDate"],
    "reportTypeId": "spCampaigns",
    "timeUnit": "SUMMARY",
    "format": "GZIP_JSON",
    "filters": [
      {
        "field": "campaignStatus",
        "values": ["ENABLED", "PAUSED"]
      }
    ]
  }
}
```

## Sample request

Amazon's sample uses the North America endpoint `https://advertising-api.amazon.com`.

The official page includes a runnable cURL example with authorization headers. In this local library, keep the useful structure but avoid storing token-shaped examples. A report creation request needs:

- North America endpoint: `https://advertising-api.amazon.com/reporting/reports`
- Method: `POST`
- Content type for the reporting v3 create request.
- Amazon Ads client identifier.
- Amazon Ads profile scope.
- Current access token.
- JSON report body with name, date range, ad product, groupings, columns, report type, time unit, format, and optional filters.

## Response and status flow

A successful request returns a `reportId` and initial `status`, often `PENDING`.

```json
{
  "reportId": "xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx",
  "status": "PENDING",
  "url": null,
  "urlExpiresAt": null
}
```

Check status with:

```text
GET /reporting/reports/{reportId}
```

Statuses while generating include `PENDING` and `PROCESSING`. When ready, `status` becomes `COMPLETED` and the response includes `url`.

## Downloading and reading reports

The completed report URL points to an S3 object. Download it through a browser or GET request, then decompress the returned file. Amazon's sample output is raw JSON containing rows such as `campaignId`, `adGroupId`, `impressions`, `clicks`, `cost`, `startDate`, `endDate`, and purchase metrics.

## Operational notes

- Report generation can take up to three hours.
- Duplicate identical report requests may return status code `425`.
- Too many status checks may return `429`; use retry logic with exponential backoff.
- To combine performance data with campaign metadata, request an export and join datasets by `campaignId`.

## Related pages

- [Report types](https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/report-types)
- [Columns](https://advertising.amazon.com/API/docs/en-us/guides/reporting/v3/columns)
- [Exports overview](https://advertising.amazon.com/API/docs/en-us/guides/exports/overview)
- [Amazon Marketing Stream overview](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/overview)
- [API endpoints](https://advertising.amazon.com/API/docs/en-us/reference/api-overview#api-endpoints)
