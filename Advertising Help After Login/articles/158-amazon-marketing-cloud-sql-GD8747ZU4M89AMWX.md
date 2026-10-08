---
title: "Amazon Marketing Cloud SQL"
source_url: "https://advertising.amazon.com/help/GD8747ZU4M89AMWX"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Marketing Cloud SQL

Amazon Marketing Cloud (AMC) SQL is a custom query language. It’s designed to help our advertisers interact with event-level records to generate aggregated outputs, which lead to insights for campaign measurement, audience analysis, media optimization, and more.

Updated on Feb 24, 2026

Advertisers can access only aggregated, pseudonymized outputs from AMC. All information in an advertiser’s AMC instance is handled in strict accordance with Amazon’s privacy policies, and your own signals can’t be exported or accessed by Amazon. Hence, extracting event-level records from AMC isn’t permitted. Event-level records refer to individual events like an impression or click from a single user.

Aggregated records refer to grouped insights. For example, count of all unique users that were served an impression by a campaign. Our advertisers can extract aggregated records, if it meets AMC's aggregation thresholds. The AMC query compiler checks if the thresholds are met and ensures that analysis is pulled in a privacy-safe way. For example, AMC doesn’t support SELECT * for any of the tables.

## Supported and unsupported functions

AMC supports many SQL functions, including but not limited to:

- SELECT <column> FROM <table> (although it doesn’t support SELECT * FROM <table>)
- WHERE
- GROUP BY
- SUM( )
- CASE ( )
- IF ( )

: **Note:**AMC doesn’t support all SQL functions. For example, it doesn’t support LIMIT, and RIGHT JOIN.

For a more complete list of supported and unsupported functions, refer to the AMC SQL reference or to the instructional query Introduction to AMC SQL.

## Example AMC SQL query and results

The following is an example of a basic query. This query creates a report of Amazon DSP campaign information (campaign ID, campaign name, start date, and end date), as well as the sum of impressions for each campaign.

```
SELECT
  campaign_id,
  campaign,
  campaign_start_date,
  campaign_end_date,
  SUM(impressions) AS impressions
FROM
  dsp_impressions
GROUP BY
  1,
  2,
  3,
  4
```

The results of this query will look similar to the following:

This is a basic example, but you can use AMC SQL to interact with AMC event-level records in much more complex and customizable ways. For more information about AMC SQL, refer to the AMC SQL reference or to the instructional query Introduction to AMC SQL.
