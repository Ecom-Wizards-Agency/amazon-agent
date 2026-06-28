---
title: "Streamline Amazon Marketing Stream Data Integration with Snowflake"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/usage-examples/2025-01-ams-and-snowflake-integration"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
security_note: "Secret, private-key, and IAM policy implementation details summarized for safer local use."
---

# Amazon Marketing Stream to Snowflake

This article explains how to send Amazon Marketing Stream data directly to Snowflake through Amazon Data Firehose and Snowpipe Streaming.

## Purpose

Amazon Marketing Stream provides near real-time Amazon Ads reporting data. This integration makes AMS records available in Snowflake within minutes or seconds, reducing the need for older multi-step pipelines using SQS, Firehose, and S3 as intermediate storage.

## Architecture

![Amazon Marketing Stream to Snowflake architecture](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/stream-to-snowflake-real-time.png)

## Benefits

- Near real-time AMS data in Snowflake.
- Scales across multiple AMS datasets.
- Lower operational complexity than older multi-hop pipelines.
- Direct delivery from Amazon Data Firehose to Snowflake through Snowpipe Streaming.
- Infrastructure can be deployed consistently with CloudFormation.

## Requirements

| Area | Requirement |
| --- | --- |
| AWS | AWS account with IAM, Amazon Data Firehose, Amazon S3, and CloudFormation access. |
| AWS logging | S3 bucket for Firehose backup or error logging. |
| Snowflake | Snowflake account and user with sufficient admin privileges. |
| Snowflake auth | Key-pair authentication configured for the Snowflake user. |
| Optional networking | PrivateLink support if private connectivity is required. |
| Amazon Ads | Amazon Marketing Stream subscription ability and access to relevant datasets. |

## Setup workflow

1. Create a Snowflake database, schema, and destination table for AMS records.
2. Create an Amazon Data Firehose stream.
3. Set Firehose source to Direct PUT.
4. Set Firehose destination to Snowflake.
5. Configure Snowflake connection settings and database/table targets.
6. Configure S3 backup or error logging.
7. Create Firehose IAM roles and policies for AMS/SNS delivery.
8. Subscribe to Amazon Marketing Stream topics and direct records to the Firehose stream.
9. Verify delivery through CloudWatch logs and Snowflake queries.

## Console screenshots

![Create Firehose stream](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/create-firehose.png)

![Firehose destination settings 1](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/destination-settings.png)

![Firehose destination settings 2](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/destination-settings2.png)

![Firehose destination settings 3](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/destination-settings3.png)

## Deployment options

| Option | Best for | Notes |
| --- | --- | --- |
| Manual AWS Console setup | First-time review and learning | Good for seeing each Firehose and Snowflake field. |
| CloudFormation template | Repeatable deployments | Uses the Amazon Ads Advanced Tools GitHub template for AMS Firehose/Snowflake setup. |

## Related assets

- [Amazon Marketing Stream onboarding](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/onboarding)
- [Amazon Marketing Stream API reference](https://advertising.amazon.com/API/docs/en-us/amazon-marketing-stream/openapi)
- [CloudFormation template repository](https://github.com/amzn/ads-advanced-tools-docs/tree/main/amazon_marketing_stream)
- [Stream Firehose Snowflake template](https://github.com/amzn/ads-advanced-tools-docs/blob/main/amazon_marketing_stream/Stream_firehose_snowflake.yml)

## Checkpoints

- Confirm the AMS datasets needed before subscribing.
- Confirm the Snowflake account URL, role, database, schema, and table names.
- Store private keys and credentials only in approved secret storage.
- Confirm S3 backup/error logging is configured before starting the stream.
- Check CloudWatch logs if Snowflake records do not arrive.
- Stop before deploying IAM, CloudFormation, or AMS subscriptions in a real account unless the user approves the account, dataset, and destination.

## Routing use

Use this page when the user asks about Amazon Marketing Stream, near real-time Ads reporting, Snowflake integration, Firehose delivery streams, Snowpipe Streaming, or AMS data pipelines.
