---
title: "Amazon Marketing Stream onboarding guide"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/onboarding"
resolved_url: "https://advertising.amazon.com/API/docs/en-us/guides/amazon-marketing-stream/onboarding/sqs/get-started"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Marketing Stream onboarding guide

Important

Amazon Marketing Stream v1 is on a deprecation path. Existing subscriptions will keep delivering data during this period, and some v1 functionality may be limited before Stream v1 is shut off on June 30, 2027. Migrate to Stream v2 before then to keep your data flowing without interruption. See the Migrate from Version 1 guide for details.

Follow the steps in this tutorial to connect your AWS application to Amazon Marketing Stream datasets. At the end of the tutorial, you should start receiving performance and campaign data in your SQS queue.

## Before you begin

To complete this tutorial, you will need:

- Access to the Amazon Ads API
- A valid Ads API access token
- Your Ads API profile ID
- An AWS account
- The ability to make basic cURL requests using a tool like Terminal or Postman
- An understanding of the Amazon Marketing Stream datasets

Note

During the Amazon Ads API onboarding process, you will need to create an Amazon Login With Amazon account. If you are creating an application associated with a business, we recommend you use an email address that is managed by multiple individuals in your organization. This will ensure that you do not lose access to your account if an individual leaves your organization.

Tip

Onboarding to Stream using our reference application. Our python-based reference application used the AWS CDK to help you programmatically complete the steps listed in the document. Learn more.

## Step 1: Create an SQS queue

To receive data using Amazon Marketing Stream, you must first set up a queue using AWS Simple Queue Service (SQS). We recommend your AWS set up be completed by someone familiar with AWS.

You can create a queue by logging in to your AWS account and using the SQS console or by using an AWS CloudFormation template.

When using AWS (both SQS and CloudFormation), it is important to make sure that you are logged in to the correct region. Use this table to select the correct region based on the location of the advertiser you are creating a subscription for.

| Advertiser region | AWS region |
| --- | --- |
| NA | `us-east-1` |
| EU | `eu-west-1` |
| FE | `us-west-2` |

You can select a region using the dropdown in the top right corner of the AWS console.

For full details on what countries are supported, see the Geographic availability.

### CloudFormation

Tip

To avoid errors during onboarding, we recommend using the CloudFormation template instead of manually setting up the queue in the SQS Console.

To use a CloudFormation template, follow the instructions in Onboarding with CloudFormation.

Our CloudFormation template automatically adds a valid resource-based IAM policy, so if you are using CloudFormation, you can skip step 2 in this guide and move directly to step 3.

### SQS Console

You can also create SQS queues manually using the SQS console. Follow the instructions in the AWS documentation.

Note

You must create a **Standard** queue; FIFO queues are not currently supported.

## Step 2: Add a resource-based IAM policy

Important

You must add a valid IAM policy to your queue in order to receive Amazon Marketing Stream data.

Each combination of dataset and region has a distinct IAM policy. For example, the `sp-traffic` dataset has different IAM policies for NA, EU, and FE. Make sure you are applying the correct IAM policy based on the dataset and region that you want to subscribe to. To view resource-based IAM policies for all available datasets and regions, see the Amazon Marketing Stream data guide.

You can add an access policy during queue creation, or edit an existing queue.

Note

When inserting an IAM policy, make sure `Resource` points to the Amazon Resource Name (ARN) of your own queue.

## Step 3: Subscribe to Amazon Marketing Stream datasets

Important

Before sending a subscription request, make sure you have already applied the IAM policy associated with the dataset to your SQS queue.

After setting up a queue and adding an IAM policy, you can subscribe to advertiser data using the Amazon Marketing Stream subscription APIs. You need to make a separate request for each dataset you want to subscribe to.

Important

There are two sets of subscription APIs, one for sponsored ads datasets and one for Amazon DSP datasets. For the relevant subscription endpoint for each dataset, see Datasets overview.

Tip

Use our Postman collection to test the Amazon Marketing Stream APIs. Once you have set up the collection and environment, check out the **Amazon Marketing Stream** folder to call the API.

### Subscribing to sponsored ads datasets

To subscribe to sponsored ads datasets, use the POST /streams/subscriptions endpoint.

If you are subscribing to data for multiple profiles, you must make a separate call for each.

**Headers**

| Parameter | Description |
| --- | --- |
| `Amazon-Advertising-API-ClientId` | The client ID associated with your Login with Amazon application. |
| `Amazon-Advertising-API-Scope` | Your profile ID. |
| `Authorization` | Your access token. |
| `Content-Type` | `application/vnd.MarketingStreamSubscriptions.StreamSubscriptionResource.v1.0+json` |

**Parameters**

| Parameter | Required | Description |
| --- | --- | --- |
| `dataSetId` | Yes | To view available datasets, see the data guide. |
| `destinationArn` | Yes | The ARN of the SQS queue where you want to receive data. |
| `clientRequestToken` | Yes | Unique value supplied by the caller used to track identical API requests. Should the request be retried, the caller should supply the same value. We recommend using a GUID. |
| `notes` | No | Additional details which can be used to identify the destination. |

**Example**

Make sure to replace `Amazon-Advertising-API-ClientId`, `Amazon-Advertising-API-Scope`, `Authorization`, and `destinationArn` with the values specific to your account. The `clientRequestToken` can be any idempotency token that could be used to identify the request if needed.

```
    curl --location --request POST  'https://advertising-api.amazon.com/streams/subscriptions'  \
    --header  'Amazon-Advertising-API-ClientId: xxxxxx'  \
    --header  'Amazon-Advertising-API-Scope: xxxxxxx'  \
    --header  'Content-Type: application/vnd.MarketingStreamSubscriptions.StreamSubscriptionResource.v1.0+json'  \
    --header  'Authorization: Bearer xxxxxxxxx'  \
    --data-raw  '{
    "clientRequestToken": "123456789xyz1234567",
    "dataSetId": "sp-conversion",
    "notes": "Advertiser 1 sp-conversion subscription",
    "destinationArn": "QUEUE_ARN"
    }'
```

**Response**

A successful request results in a response that includes a `subscriptionId`.

```
{ 
     "subscriptionId" :   "xxxxxxxxxxxxxx" , 
     "clientRequestToken" :   "123456789xyz1234567" , 
 }
```

### Subscribing to Amazon DSP datasets

To subscribe to Amazon DSP datasets, use the POST /dsp/streams/subscriptions endpoint.

If you are subscribing to data for multiple Amazon DSP advertiser IDs, you must make a separate call for each.

**Headers**

| Parameter | Description |
| --- | --- |
| `Amazon-Advertising-API-ClientId` | The client ID associated with your Login with Amazon application. |
| `Amazon-Advertising-API-Account-ID` | The Amazon DSP advertiser ID that you want to receive data for via Stream. You can view the advertiser IDs associated with your profile using GET /dsp/advertisers. |
| `Authorization` | Your access token. |
| `Content-Type` | `application/vnd.MarketingStreamSubscriptions.DspStreamSubscriptionResource.v1.0+json` |

**Parameters**

| Parameter | Required | Description |
| --- | --- | --- |
| `dataSetId` | Yes | To view available datasets, see the data guide. |
| `destinationArn` | Yes | The ARN of the SQS queue where you want to receive data. |
| `clientRequestToken` | Yes | Unique value supplied by the caller used to track identical API requests. Should the request be retried, the caller should supply the same value. We recommend using a GUID. |
| `notes` | No | Additional details which can be used to identify the destination. |

**Example**

Make sure to replace `Amazon-Advertising-API-Account-ID`, `Amazon-Advertising-API-ClientId`, `Authorization`, and `destinationArn` with the values specific to your account. The `clientRequestToken` can be any idempotency token that could be used to identify the request if needed.

```
    curl --location --request POST  'https://advertising-api.amazon.com/dsp/streams/subscriptions'  \
    --header  'Amazon-Advertising-API-ClientId: xxxxxx'  \
    --header  'Amazon-Advertising-API-Account-ID: xxxxxxx'  \
    --header  'Content-Type: application/vnd.MarketingStreamSubscriptions.DspStreamSubscriptionResource.v1.0+json'  \
    --header  'Authorization: Bearer xxxxxxxxx'  \
    --data-raw  '{
    "clientRequestToken": "123456789xyz1234567",
    "dataSetId": "adsp-campaigns",
    "notes": "Advertiser 1 adsp-campaigns subscription",
    "destinationArn": "QUEUE_ARN"
    }'
```

**Response**

A successful request results in a response that includes a `subscriptionId`.

```
{ 
     "subscriptionId" :   "xxxxxxxxxxxxxx" , 
     "clientRequestToken" :   "123456789xyz1234567" , 
 }
```

## Step 4: Confirm your subscription in SQS

Once you have successfully subscribed to Amazon Marketing Stream using the API, you need to confirm the subscription in SQS to start receiving data.

You should see a message in your SQS queue resembling:

```
{ 
     "Type"   :   "SubscriptionConfirmation" , 
     "MessageId"   :   "165545c9-2a5c-472c-8df2-7ff2be2b3b1b" , 
     "Token"   :   "2336412f37..." , 
     "TopicArn"   :   "arn:aws:sns:us-west-2:123456789012:MyTopic" , 
     "Message"   :   "You have chosen to subscribe to the topic arn:aws:sns:us-west-2:123456789012:MyTopic.To confirm the subscription, visit the SubscribeURL included in this message." , 
     "SubscribeURL"   :   "https://sns.us-west-2.amazonaws.com/?Action=ConfirmSubscription&TopicArn=arn:aws:sns:us-west-2:123456789012:MyTopic&Token=2336412f37..." , 
     "Timestamp"   :   "2012-04-26T20:45:04.751Z" , 
     "SignatureVersion"   :   "1" , 
     "Signature"   :   "EXAMPLEpH+DcEwjAPg8O9mY8dReBSwksfg2S7WKQcikcNKWLQjwu6A4VbeS0QHVCkhRS7fUQvi2egU3N858fiTDN6bkkOxYDVrY0Ad8L10Hs3zH81mtnPk5uvvolIC1CXGu43obcgFxeL3khZl8IKvO61GWB6jI9b5+gLPoBc1Q=" , 
     "SigningCertURL"   :   "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-f3ecfb7224c7233fe7bb5f59f96de52f.pem" 
 }
```

To start receiving data in your queue, you must confirm the subscription in one of the following ways:

1. Make a `GET` request to the `SubscribeURL` value returned in the SQS queue confirmation message. This call should return a message saying that subscription has been confirmed and the queue should start receiving messages. **Example confirmation message** ``` < ConfirmSubscriptionResponse > < ConfirmSubscriptionResult > < SubscriptionArn > arn:aws:sns:us-east-2:123456789012:MyTopic:1234a567-bc89-012d-3e45-6fg7h890123i </ SubscriptionArn > </ ConfirmSubscriptionResult > < ResponseMetadata > < RequestId > abcd1efg-23hi-jkl4-m5no-p67q8rstuvw9 </ RequestId > </ ResponseMetadata > </ ConfirmSubscriptionResponse > ```
2. Use the AWS SDK to call `ConfirmSubscription` using the `Token` and `TopicArn` values returned in the SQS queue confirmation message. Note You must confirm the subscription for each advertiser and dataset you are subscribing to. If you are receiving data for multiple advertisers or datasets in the same queue, you should consider using option 2 above to create an application that programmatically confirms subscriptions. The application should listen to the queue and distinguish confirmation messages from data events.

You can identify subscription messages versus data events using logic similar to:

```
     if   "Type"   in  content  and  content[ 'Type' ] ==  'SubscriptionConfirmation' :

     def   confirm_subscription ( content ):
        token = content[ 'Token' ]
        topicArn = content[ 'TopicArn' ]
         print ( f"Confirming subscription for  {topicArn} " )
        sns.confirm_subscription(TopicArn=topicArn, Token=token)
```

## Subscription status flow

You can view the status flow for Stream subscriptions in the following diagram.

Learn more about the possible statuses for subscriptions in Managing subscriptions.

## Next steps

Once you have confirmed your subscriptions and started receiving data, you can move on to:

- Aggregating data
- Querying data
- Managing subscriptions
- AWS best practices
- AWS serverless application repository
- SQS poller

## AWS Workshop

This Workshop provides an example of a serverless data analytics and managed machine learning platform built using Amazon Marketing Stream and AWS technology. Developers, data analysts, and architects can use the Workshop to get a practical idea of how Stream might be implemented to help your business.

View the Workshop.

## Troubleshooting FAQ

### Why am I seeing negative values for the first couple of days of data?

The negatives are corrections that are happening retroactively based on the Amazon click and conversion validation process. You may have negative aggregated values for the first day or two that we enabled the connection as you did not receive original traffic on those days, just corrections. The recommendation is to ignore negative values in the first one to two days.

After the first two days, you should start receiving positive values; if you do not see aggregate positive values after two days, contact support.

You will continue to see negative deltas as corrections happen due to click invalidation, but they should always aggregate to positive values.

### Why am I receiving null records?

You can disregard these rows. This is expected and these rows are not an issue and will cause no issues with data as they aggregate to 0.

### I have created a queue and while I am trying to subscribe using POST /streams/subscriptions I am getting error code 400 that my region is not supported.

In the current state, Amazon Marketing Stream supports only three regions: `us-east-1` (NA), `eu-west-1` (EU), and `us-west-2` (FE). When creating your SQS queue, make sure you are only using a supported region. To avoid this error, we recommend using the provided CloudFormation template to create your queue.

### My subscription status is `PENDING_CONFIRMATION`, but I never received a confirmation message in SQS.

You may have applied the wrong IAM policy to your queue. Make sure that the IAM policy you are using in your queue matches the region of the advertiser profile and the dataset that you are trying to subscribe to.

If you applied the wrong IAM policy to your queue, you should create a new queue, apply the correct policy, and subscribe to the dataset again using the new queue ARN.

Tip

We suggest using the provided CloudFormation template to create your queues to reduce the risk of manual errors.

If you are sure that you applied the correct IAM policy, but have been stuck in `PENDING_CONFIRMATION`, submit a ticket and our support team can manually resend the confirmation message.

### My subscription is stuck in `PENDING_CONFIRMATION` and will not move to `FAILED_CONFIRMATION`.

If you do not confirm a subscription within three days, the status should automatically move to `FAILED_CONFIRMATION`. Once the status has moved to `FAILED_CONFIRMATION`, you can send another request to subscribe to the dataset. In rare cases, the status may not switch to `FAILED_CONFIRMATION` automatically, and you should submit a ticket to our support team.

Alternatively, you can create a new queue, apply the relevant IAM policy, and try to subscribe to the dataset again using the new queue ARN.

### I have successfully confirmed my subscription in SQS, but I am not receiving any messages in my SQS destination queue.

Since Amazon Marketing Stream delivers data in near real time, an event related to the advertiser and their campaign in the subscribed dataset and marketplace must occur for anything to be sent. In the absence of these events, there will be no data. In other words, data is only sent if there is performance for that campaign within the hour.

### It looks like I am receiving duplicate data.

If it looks like you are receiving duplicate records, be sure to inspect your data first. There are a couple of scenarios where the data you are receiving might resemble duplicates, but is actually valid.

First, it is possible that your data for two different hours could be very similar. For example, consider a keyword that receives ten impressions and three clicks on a given date in hour one. In hour two, they again receive ten impressions and three clicks. Stream would send similar records for that keyword in both hours, differentiated only by the hour the data is related to. For keywords without many impressions, it is likely you might see only one impression and no clicks for many hours throughout the day.

Second, Amazon Marketing Stream sends an hourly delta for your campaigns, so restatements can result in records that appear almost identical. This could lead to two records with the same click and impression data for the same keyword and same hour, however one is the original delta and the second is a restatement. This is not a duplicate and can be checked by examining the `idempotency_id` of the two records. If the idempotency IDs are different, then they are not duplicates and are two distinct records for that keyword and hour.

### How do I cancel a subscription?

There is not currently a way to delete or cancel a subscription. To stop receiving data for a subscription, you should set the `subscriptionStatus` to `ARCHIVED`. For more information, see Managing subscriptions.

### What is the time zone associated with Amazon Marketing Stream data?

For hourly data, datasets contain a `time_window_start` field that represents the start timestamp of the activity within the time zone of the advertiser. You can check the time zone associated with an advertiser profile by calling GET /v2/profiles.

### How do I ensure that I am receiving all Amazon Marketing Stream data?

AWS CloudWatch provides a variety of metrics for SQS queues including the number of messages received, the number of messages deleted, and the number of messages in the queue. Partners can monitor these metrics to identify any discrepancies. For example, if the number of messages received is greater than the number of messages deleted plus the number of messages in the queue, then some messages may be missing.
