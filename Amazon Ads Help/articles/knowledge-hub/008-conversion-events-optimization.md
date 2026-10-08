---
title: "How Advertisers Optimize Campaign using Conversion Events"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/conversion/conversion"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
---

# How Advertisers Optimize Campaign using Conversion Events

by Chintan Sanghavi Lead Solutions Architect @ Amazon Ads, Mansi Pedgaonkar Sr. Product Manager at Amazon Ads on December 15th 2025

Traditional tracking methods (like third-party cookies and pixels) are becoming unreliable due to evolving privacy regulations (such as iOS restrictions and ad blockers), leading to a significant "signal loss" that causes undercounting of conversions. This creates problems for advertisers such as:

- **Inaccurate Attribution**: Advertisers struggle to know which specific ad interactions (clicks or views) actually lead to sales or leads, making it difficult to assess the true effectiveness of their ad spend across different channels (on and off Amazon).
- **Inefficient Optimization**: Without a complete picture of conversions, algorithms receive poor training signals, which results in inefficient bidding, suboptimal ad targeting, and wasted ad budget on underperforming campaigns or audiences.
- **Fuzzy ROI:** You cannot confidently calculate your true Return on Ad Spend (ROAS), making budget justification nearly impossible.

## Solution Overview: Harnessing the power of First-Party Data

Conversion Events provide a robust, reliable solution by allowing you to send your own server-side, first-party data directly to Amazon Ads. This bypasses browser-based limitations and ensures a complete, accurate count of valuable shopper actions. These events are like a customer has visited a page, added a product in cart, purchased a product etc.

The primary purpose of conversion events is to measure the effectiveness of advertising efforts in achieving critical business objectives. They help bridge the gap between ad clicks and actual business outcomes, such as a purchase or a sign-up, allowing advertisers to see which marketing activities are driving real results. In the world of digital advertising, accurate conversion tracking is the cornerstone of effective campaign management and optimization.

Conversion events are important because they provide tangible metrics for evaluating success, which allows advertisers to make informed decisions about their marketing strategy and budget allocation. Advertisers can leverage conversion events in several ways:

- **Performance Measurement**: They help determine the success of specific campaigns, ad groups, or keywords in achieving business goals. For example, A retailer runs two Amazon Ads campaigns: one targeting mobile users and one targeting desktop users. By tracking the purchase conversion event for both, they discover the mobile campaign generates 3x the conversions, allowing them to shift more budget there.
- **Optimization and Bidding**: Conversion data is used by automated bidding strategies of ad platforms (e.g., maximize conversions, target return on ad spend) to dynamically target the most relevant audience and maximize performance. For example, An advertiser wants to maximize sign-ups for a webinar. They use an automated bidding strategy in their ad platform set to "maximize conversions," using the form submission as the key signal. The platform automatically bids higher for users most likely to fill out the form.
- **ROI and CPA Calculation**: By tracking conversions, advertisers can accurately calculate key performance indicators like Return on Investment (ROI) and Cost Per Acquisition (CPA), ensuring they spend their budget wisely. For example, An online learning platform spends $5,000 on ads in one month and generates 100 course enrollments (conversions). They calculate the Cost Per Acquisition (CPA) is $50 per student, a key metric for budgeting and demonstrating value to stakeholders.

### Amazon Ads Solutions

Amazon Ads offers comprehensive conversion tracking solutions for both on-Amazon and off-Amazon conversions.

Amazon Ads distinguishes between two types of conversions. First, there are **on-Amazon conversions**, which occur within Amazon platforms such as Amazon.com, Twitch. These conversions, such as product purchases or add-to-cart actions, are automatically tracked and readily available to advertisers through both the Amazon Ads Console user interface and APIs. For those seeking deeper insights, these conversion metrics are also accessible via Amazon Marketing Cloud (AMC), enabling advanced analysis and reporting.

The second category, **off-Amazon conversions**, addresses the need to track customer actions that take place outside of Amazon such as the digital properties of advertisers and social media. Amazon provides four distinct methods for tracking these off-platform conversions:

1. Amazon Advertising Tags (AAT)
2. Amazon Attribution Tags
3. Amazon Marketing Cloud (AMC)
4. Amazon Conversions API (CAPI).

Each of these solutions is tailored to specific scenarios and business needs, offering advertisers the flexibility to choose the most suitable approach for their unique requirements.

## Architecture Overview

### How to capture and send conversion events?

As shown in the diagram above,

1. Advertisers will create a campaign to display ads on Amazon platforms or on non-Amazon platforms. This campaign can be ads campaign or also email or social media campaigns. Now, the advertiser wants to measure the campaign’s performance and wants to optimize the current campaign or future campaigns.
2. Customers interact with campaigns, generating conversions on Amazon or off-Amazon platforms. Each platform will generate many events, conversion events, for example, customer (buyer) has viewed the page, or added product in the cart or has purchased the product. For privacy and security, any personally identifiable information (PII) like email addresses should be **hashed** (converted into a secure, scrambled code using an algorithm like SHA-256) before being sent to Amazon.
  - 2.1 on-Amazon Platforms: If the customer is purchasing product on Amazon.com then Amazon.com will generate conversion events and will automatically store in Amazon Marketing Cloud (AMC).
  - 2.2 Advertiser’s Website: The customer can visit advertiser’s website to purchase the product. The advertiser’s website can track these events via various methods such as advertising tags or by storing events in the local database.
  - 2.3 Third Party Website: Advertiser can also list the product third party websites. The advertiser can also download the events from the third party websites using APIs etc. These events can be stored in the local database of the advertiser.
  - 2.4 Social Media: The social media campaigns can be tracked using Amazon Attribution Tags. These tags will directly post all required events in the Amazon Attribution.
3. Once events are captured,
  - 3.1 These events will be stored automatically in Amazon Marketing Cloud (AMC) automatically for all on-amazon events. Besides this, the advertiser can also upload data including conversion data directly in AMC using data upload feature of AMC
  - 3.2 For all off-Amazon events, the advertiser can write a conversion event publisher. This conversion event publisher will read data from customer’s database and will post all events to Amazon Ads’ event manager. The advertiser can also use customer data platforms (CDP) to publish these events.
  - 3.3 Social media, email campaign related attribution will be made available to Amazon Attribution using attribution tags. The advertiser can use reporting APIs to get these attributions related data. The advertiser can use event publisher to push these events.
4. Once events are available in events manager then all conversion events are sent for attribution as well as to AMC. Amazon internally matches the provided hashed identifiers against its own large database of pseudonymized user identifiers. If a match is found, Amazon checks if that user was exposed to one of your Amazon ad campaigns (clicked or viewed an ad) within a specific timeframe. The conversion is then attributed to the most relevant ad interaction based on a specific hierarchy (e.g., clicks are prioritized over views).

### How to Use Conversion Events to Create Audiences

You can leverage your conversion event data to create highly targeted custom audiences for remarketing or prospecting in Amazon DSP.

**Via Amazon DSP (using the Events Manager)** You can create rule-based audiences directly within the Amazon DSP console using the off-Amazon conversion events you've already defined and tracked.

- **Segment by Behavior:** Create audiences based on specific actions (or lack thereof) on your properties. Examples include "users who added to cart but did not purchase" or "users who signed up for a newsletter".
- **Set Rules:** Define the criteria for audience inclusion, such as the specific conversion event name and the time frame (lookback window, up to 365 days).
- **Activate:** Once created, these audiences appear in your Amazon DSP advertiser account under "Advertiser Audiences" and can be applied to new ad groups just like other Amazon audiences.

**Via Amazon Marketing Cloud (AMC)** For more sophisticated audience creation, you can use the AMC clean room environment:

- **Custom SQL Queries:** Within AMC, you can write custom SQL queries to analyze your conversion data alongside Amazon data and build nuanced audience segments. This allows for complex filtering that goes beyond the basic rule builder in the DSP.
- **Audience Templates:** Amazon provides instructional query (IQ) templates to simplify common audience creation tasks, such as creating audiences of users who "clicked but not purchased".
- **Push to DSP:** After building your desired audience in AMC (which requires a minimum of 2,000 unique user IDs), you can push it directly to your linked Amazon DSP account for activation.

## Conclusion

As privacy regulations continue to reshape digital advertising and traditional tracking methods become less reliable, conversion events represent a critical solution for maintaining accurate measurement and optimization capabilities. By leveraging first-party data through the comprehensive Amazon conversion tracking ecosystem, advertisers can overcome signal loss challenges while building more effective, targeted campaigns.

The combination of the Amazon Conversions API (CAPI), Amazon Marketing Cloud (AMC), and Amazon DSP creates a powerful framework that enables advertisers to not only track conversions accurately but also transform that data into actionable audience insights. Whether you are looking to measure campaign performance, optimize bidding strategies, or create sophisticated remarketing audiences, conversion events provide the foundation for data-driven advertising success.

To get started with conversion events, begin by identifying your key business objectives and the customer actions that matter most to your success. Then, implement the appropriate Amazon Ads solution—whether through server-side API integration, attribution tags, or direct AMC uploads—to start capturing and leveraging your valuable first-party conversion data.

### About the authors

**Chintan Sanghavi**
Chintan is a lead solutions architect at Amazon Ads, driving innovation with Generative AI, AWS, and Amazon Ads solutions. He has extensive experience building complex multi-technology solutions.

**Mansi Pedgaonkar**
Mansi is Senior Product Manager at Amazon Ads with extensive experience building advertising solutions across multiple companies.
