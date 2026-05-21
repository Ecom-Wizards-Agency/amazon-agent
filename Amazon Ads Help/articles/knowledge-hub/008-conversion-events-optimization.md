---
title: "How Advertisers Optimize Campaign using Conversion Events"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/conversion/conversion"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
---

# Optimize Campaigns With Conversion Events

This article explains how Amazon Ads conversion events help advertisers recover signal loss, measure campaign outcomes, optimize bidding, and create remarketing or prospecting audiences.

## Problem solved

- Browser-based tracking can miss conversions because of privacy rules, device restrictions, ad blockers, and cookie loss.
- Advertisers may not know which clicks or views created purchases, leads, or sign-ups.
- Automated bidding performs poorly when it is trained on incomplete conversion signals.
- ROAS, ROI, and CPA become harder to trust when off-Amazon actions are undercounted.

## Conversion event options

| Conversion area | Amazon Ads solution | Notes |
| --- | --- | --- |
| On-Amazon actions | Amazon Ads Console, Ads APIs, AMC | Purchases and other Amazon-owned events are automatically available. |
| Off-Amazon actions | Amazon Advertising Tags, Amazon Attribution Tags, AMC uploads, Conversions API | Used for advertiser websites, third-party sites, social campaigns, and owned databases. |
| Advanced analysis | Amazon Marketing Cloud | Combines advertiser data with Amazon signals in a clean room. |
| Audience activation | Amazon DSP and AMC audience pushes | Uses event behavior for remarketing and prospecting. |

## Architecture

![Conversion APIs architecture](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/knowledge_hub_images/blogs/Blog-ConversionApis-Overview.png)

## Workflow

1. Create campaigns on Amazon or external channels.
2. Capture customer actions such as product views, add-to-cart events, purchases, leads, sign-ups, or form submissions.
3. For privacy, hash personal identifiers before sending them to Amazon Ads.
4. Store on-Amazon events automatically in AMC; upload or publish off-Amazon events through tags, AMC uploads, a CDP, or Conversions API.
5. Amazon Ads matches hashed identifiers against pseudonymized user identifiers, checks ad exposure windows, and attributes conversions.
6. Use conversion events for performance reporting, automated bidding, budget allocation, and audience creation.

## Audience creation

| Path | Use it for | How it works |
| --- | --- | --- |
| Amazon DSP Events Manager | Direct rule-based audiences | Build audiences from event names and lookback windows, such as added-to-cart but not purchased. |
| Amazon Marketing Cloud | More advanced audience logic | Use SQL and instructional query templates, then push qualified audiences to linked DSP accounts. |

## Checkpoints before implementation

- Confirm the business objective and the exact customer actions that count as conversions.
- Decide whether the conversion source is on-Amazon, advertiser-owned, third-party, or social/email.
- Confirm which identifier fields are permitted and hashed correctly.
- Decide whether the output is reporting only, bidding optimization, DSP audience activation, or AMC analysis.
- Stop before sending real customer data or live conversion events unless the account owner has approved the mapping and privacy handling.

## Routing use

Use this page when the user asks about Amazon Ads conversion tracking, CAPI, server-side events, off-Amazon attribution, audience building from events, AMC uploads, or campaign optimization using first-party data.
