---
title: "Manage your connected AWS account"
source_url: "https://advertising.amazon.com/help/GX5SZY5THV3UGV4N"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Manage your connected AWS account

You can access Amazon Marketing Cloud (AMC) programmatically through APIs. The AMC APIs have the ability to automate and complete tasks, such as saving and scheduling queries at scale, uploading first-party records to AMC, and creating audiences.

Updated on May 7, 2025

You can provide the AWS account ID to your Amazon representative to ensure that the association is made during instance creation, or you can manage the association post-creation. Once the instance request is provisioned, results are delivered to the S3 bucket that you create and associate with your instance. These results will be from both manual queries run in the UI and automated queries scheduled through the API.

If you’re setting up an S3 bucket for the first time, you can use the AWS CloudFormation URL listed on your instance info page to create the bucket via the AWS Management console, AWS CloudFormation API, or AWS CLI.

As an AMC administrator, you can add, change, and manage the AWS Account ID and S3 bucket name by performing the following steps:

1. Go to the **Instance** tab drop-down at the top-right corner of the page and click **Instance info** to access the Instance info page. Scroll to the **Additional info** section at the bottom of the page.
2. Click **Edit** to make the **Connected AWS account ID** field editable.
3. Enter the 12-digit AWS account ID.
4. If required, you can either manually update the S3 bucket name or **Generate S3 bucket name**. Follow the bucket naming rules when renaming your S3 bucket. If the instance is already associated with an AWS account, then it also has a S3 bucket. You have the option of retaining the existing bucket name or creating a new one. If you want to retain the existing bucket name, delete the S3 bucket in the existing AWS account and create a new S3 bucket in the new AWS account with the same S3 bucket name. S3 bucket names must be globally unique. If the bucket name is changed, any data pipelines, automation, or code that reference the previous bucket name must be updated.
5. Click **Save**. The **AWS CloudFormation URL – S3 bucket setup** will auto-populate with a new link. **Note:**Only the AWS account administrators will be able to access this link and set up the S3 bucket.
6. Enter the updated CloudFormation URL in your browser, sign in to the specified AWS account using the AWS credentials and create the S3 bucket. Refer to the **Create and link the Amazon S3 bucket** topic in the **AMC Getting Started API Guide** for more details. **Note:**For details on setting up the AMC APIs, refer to the advanced tools center.
