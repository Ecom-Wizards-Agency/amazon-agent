---
title: "Amazon Marketing Cloud sandbox"
source_url: "https://advertising.amazon.com/help/GRRNHKR8QV6DGS4T"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Marketing Cloud sandbox

The Amazon Marketing Cloud (AMC) sandbox offers an environment that allows you to explore, develop, test, and innovate on AMC using synthetic data.

Updated on Feb 25, 2025

The AMC sandbox provides functionalities identical to what’s available in AMC advertiser instances. It contains only synthetic signals generated to mimic AMC signals, which include Amazon Ads signals, and paid features signals from Amazon and third-parties. Additionally, the sandbox is also integrated with other AMC features, such as custom parameters, the Use case library, and advertiser data upload. You can now simulate using AMC for various activities using the AMC sandbox, without affecting your live advertiser instances.

Some common use cases that the AMC sandbox can help you with are:

- **Hands-on learning**: Use the AMC sandbox along with other AMC trainings to experiment features and use cases, without the risk of causing disruptions to live executions.
- **Signal investigation**: Query with aggregation controls turned off and inspect non-aggregated reporting in detail to inform query understanding and optimization.
- **Query iteration**: Test and optimize queries using sandbox synthetic records that are lesser in volume, and then validate queries developed in sandbox instance in advertiser instances.
- **Paid features exploration**: Explore the schema and potential use cases of AMC paid features outside of the 30-day trial period.
- **Software development**: Enable software and tool developers with or without existing access to advertiser instances to start building on AMC.

Review the Introduction to Sandbox instructional query to get started with some basic use cases.

## AMC sandbox signals

AMC sandbox signals are synthetic, programmatically generated to mimic AMC signals. Sandbox signals and results may look realistic since it’s generated based on the business logics of Amazon Ads data. For example, it has the same logical interfield and cross-table relationship. It also includes a variety of ad product types, supply sources, and devices.

However, AMC sandbox data isn’t tied to any advertiser campaign, customer id, or ASIN product. As such, you shouldn’t use the results of sandbox signals to inform media strategy or implementation. We recommend using it for testing, demonstration, or as an inspiration on the insights you could possibly get from your advertiser signals.

## Accessing the AMC Sandbox UI

If you already have access to AMC, the sandbox instance should already be included in your AMC account. Sign in using the credentials you use to access your AMC account and then navigate to the instances page.

The sandbox instance will be listed at the top of your instances list page with “sandbox” suffixed to the instance name. Click the name of your sandbox instance and the Instructional queries page will open. If you’re unable to locate your sandbox instance, contact your AMC account admin to be included to the sandbox instance.

**Note:**By default, only the admin users of the AMC UI account have access to the sandbox instance. Admins can add non-admin users to the account and to the sandbox instance.

The AMC sandbox instance displays a collapsible banner in the header to indicate that you’re working in a sandbox instance. In addition to notifying that your active instance is a sandbox instance, the banner also allows you to access a Getting started guide. Click **Collapse this banner** to retain it in the collapsed form, through which you’ll continue to be notified that you’re in a sandbox instance.
