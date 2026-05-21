---
title: "Amazon Marketing Stream onboarding guide"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/onboarding"
resolved_url: "https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/onboarding/sqs/get-started"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Amazon Marketing Stream onboarding guide

This guide explains how to connect an AWS application to Amazon Marketing Stream using SQS. The target outcome is receiving near-real-time performance and campaign data in an SQS queue.

## Before you begin

Requirements:

- Access to the Amazon Ads API.
- A valid Ads API access token.
- Ads API profile ID.
- AWS account.
- Ability to make cURL or Postman requests.
- Understanding of Amazon Marketing Stream datasets.

Amazon recommends using a shared/business-managed email for the Login with Amazon account when the application belongs to a company, so access is not lost when an individual leaves.

## Step 1: Create an SQS queue

Amazon Marketing Stream requires an AWS SQS queue. Amazon recommends that AWS setup be completed by someone familiar with AWS.

Supported queue regions:

| Advertiser region | AWS region |
| --- | --- |
| NA | `us-east-1` |
| EU | `eu-west-1` |
| FE | `us-west-2` |

Visual reference:

![AWS console region selector](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/amazon-marketing-stream/aws-console-region.png)

Queue options:

- CloudFormation template, recommended by Amazon to reduce onboarding errors.
- Manual setup through the SQS console.

Important: create a **Standard** queue. FIFO queues are not currently supported.

## Step 2: Add a resource-based IAM policy

The SQS queue needs a valid IAM policy before it can receive Amazon Marketing Stream data.

Important details:

- Each dataset and region combination has a distinct IAM policy.
- Apply the policy for the exact dataset and region you want to subscribe to.
- In the IAM policy, `Resource` must point to your queue ARN.
- If using Amazon's CloudFormation template, the template adds the resource-based IAM policy and this manual step can be skipped.

## Step 3: Subscribe to datasets

After creating the queue and applying the IAM policy, subscribe to advertiser data through the Amazon Marketing Stream subscription APIs.

You need a separate request for each dataset.

### Sponsored ads subscription

Endpoint:

```text
POST /streams/subscriptions
```

Headers:

| Parameter | Description |
| --- | --- |
| `Amazon-Advertising-API-ClientId` | LwA application client ID. |
| `Amazon-Advertising-API-Scope` | Profile ID. |
| `Authorization` | Access token. |
| `Content-Type` | `application/vnd.MarketingStreamSubscriptions.StreamSubscriptionResource.v1.0+json` |

Parameters:

| Parameter | Required | Description |
| --- | --- | --- |
| `dataSetId` | Yes | Dataset ID from the Amazon Marketing Stream data guide. |
| `destinationArn` | Yes | ARN of the destination SQS queue. |
| `clientRequestToken` | Yes | Unique idempotency token. Amazon recommends a GUID. |
| `notes` | No | Optional destination details. |

Example:

```bash
curl --location --request POST 'https://advertising-api.amazon.com/streams/subscriptions' \
  --header 'Amazon-Advertising-API-ClientId: xxxxxx' \
  --header 'Amazon-Advertising-API-Scope: xxxxxxx' \
  --header 'Content-Type: application/vnd.MarketingStreamSubscriptions.StreamSubscriptionResource.v1.0+json' \
  --header 'Authorization: Bearer xxxxxxxxx' \
  --data-raw '{
    "clientRequestToken": "123456789xyz1234567",
    "dataSetId": "sp-conversion",
    "notes": "Advertiser 1 sp-conversion subscription",
    "destinationArn": "QUEUE_ARN"
  }'
```

Expected response includes:

```json
{
  "subscriptionId": "xxxxxxxxxxxxxx",
  "clientRequestToken": "123456789xyz1234567"
}
```

### Amazon DSP subscription

Endpoint:

```text
POST /dsp/streams/subscriptions
```

Headers:

| Parameter | Description |
| --- | --- |
| `Amazon-Advertising-API-ClientId` | LwA application client ID. |
| `Amazon-Advertising-API-Account-ID` | Amazon DSP advertiser ID. |
| `Authorization` | Access token. |
| `Content-Type` | `application/vnd.MarketingStreamSubscriptions.DspStreamSubscriptionResource.v1.0+json` |

Parameters match the sponsored ads subscription flow: `dataSetId`, `destinationArn`, `clientRequestToken`, and optional `notes`.

Example:

```bash
curl --location --request POST 'https://advertising-api.amazon.com/dsp/streams/subscriptions' \
  --header 'Amazon-Advertising-API-ClientId: xxxxxx' \
  --header 'Amazon-Advertising-API-Account-ID: xxxxxxx' \
  --header 'Content-Type: application/vnd.MarketingStreamSubscriptions.DspStreamSubscriptionResource.v1.0+json' \
  --header 'Authorization: Bearer xxxxxxxxx' \
  --data-raw '{
    "clientRequestToken": "123456789xyz1234567",
    "dataSetId": "adsp-campaigns",
    "notes": "Advertiser 1 adsp-campaigns subscription",
    "destinationArn": "QUEUE_ARN"
  }'
```

## Step 4: Confirm the subscription in SQS

After the subscription API call succeeds, confirm the subscription in SQS before data begins flowing.

The confirmation message contains fields such as:

```json
{
  "Type": "SubscriptionConfirmation",
  "MessageId": "165545c9-2a5c-472c-8df2-7ff2be2b3b1b",
  "Token": "2336412f37...",
  "TopicArn": "arn:aws:sns:us-west-2:123456789012:MyTopic",
  "SubscribeURL": "https://sns.us-west-2.amazonaws.com/?Action=ConfirmSubscription&TopicArn=..."
}
```

Confirmation options:

1. Make a GET request to the `SubscribeURL`.
2. Use the AWS SDK to call `ConfirmSubscription` with the `Token` and `TopicArn`.

You must confirm each advertiser and dataset subscription.

For multiple advertisers or datasets in one queue, Amazon suggests a programmatic listener that distinguishes confirmation messages from data events:

```python
if "Type" in content and content["Type"] == "SubscriptionConfirmation":
    def confirm_subscription(content):
        token = content["Token"]
        topicArn = content["TopicArn"]
        print(f"Confirming subscription for {topicArn}")
        sns.confirm_subscription(TopicArn=topicArn, Token=token)
```

## Subscription status flow

Visual reference:

![Stream status flow diagram](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/amazon-marketing-stream/state-diagram.png)

Use the Managing subscriptions docs for the full status definitions.

## Troubleshooting notes

| Issue | Likely cause or action |
| --- | --- |
| Negative values in first one to two days | Expected corrections from click and conversion validation. Ignore initial negative values, then contact support if positive aggregate data does not begin after two days. |
| Null records | Expected; disregard rows that aggregate to 0. |
| Region not supported error on `POST /streams/subscriptions` | Use only supported regions: `us-east-1`, `eu-west-1`, or `us-west-2`. |
| `PENDING_CONFIRMATION` but no SQS confirmation message | Often wrong IAM policy for dataset/region. Create a new queue with correct policy and retry, or submit a support ticket. |
| Stuck in `PENDING_CONFIRMATION` | Should move to `FAILED_CONFIRMATION` after three days; if not, submit support ticket or create a new queue and retry. |
| Confirmed subscription but no messages | Data only appears when subscribed advertiser/campaign events occur. No events means no messages. |
| Possible duplicate data | Similar hourly rows may be valid. Check `idempotency_id`; different IDs mean distinct records. |
| Cancel subscription | Set `subscriptionStatus` to `ARCHIVED`. |
| Time zone | Hourly data uses `time_window_start` in the advertiser's time zone. Check profile time zone with `GET /v2/profiles`. |
| Ensure all data is received | Monitor SQS CloudWatch metrics, especially messages received, deleted, and currently in queue. |

## Related pages

- [Amazon Marketing Stream overview](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/overview)
- [Data guide](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/data-guide)
- [Managing subscriptions](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/managing-subscriptions)
- [AWS best practices](https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/aws-best-practices)
- [Postman tutorial](https://advertising.amazon.com/API/docs/en-us/guides/postman)
