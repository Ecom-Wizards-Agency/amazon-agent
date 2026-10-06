---
title: "Bidding rules for Sponsored Products"
source_url: "https://advertising.amazon.com/help/GDLQ5D2BNFCAU3TW"
downloaded_at: "2026-10-07"
source: "Amazon Ads Support Center"
updated_on: "2025-11-06"
---

# Bidding rules for Sponsored Products

Learn about how schedule bid rules and rule-based bidding works for Amazon Sponsored Products.

Updated on Jul 14, 2026

## Rule-based bidding

Rule-based bidding takes the guesswork out of adjusting bids to align with your marketing strategy. With this bidding strategy, you set a rule with a performance goal (example: Return on Ad Spend or ROAS). Amazon then adjusts your base bids for each ad impression, increasing or decreasing them as needed to try to achieve your performance target. Amazon does not guarantee that we’ll hit the performance target that you set.

To help you capture sales from high-value opportunities, rule-based bidding can increase your bids by up to 5 times your adjusted bid amount (if any adjustments are applied to your original bid). Amazon automatically adjusts your bids for each ad opportunity based on how likely that opportunity is to result in a sale, working to meet the ROAS goal you've set for your campaign. ROAS measures the revenue generated for every dollar spent on advertising.

**Example: Placement adjustment bid**

If your base bid is $1, and you have placement adjustment for Top of Search by 10%: Placement adjusted bid = (Base bid amount) * (1 + Bid Adjustment Percentage) = 1(1.10) = $1.10.

The table below shows bid cap increase by placement.

| Base bid | **Placement** | Placement adjustment | Placement adjustment bid | Max bid caculated |
| --- | --- | --- | --- | --- |
| $1.00 | Top of search | 10% | $1.10 | $5.50 |
| $1.00 | Rest of search | 0% | $1.00 | $5.00 |
| $1.00 | Detail page | 0% | $1.00 | $5.00 |

**Campaign eligibility**

**Note:**Rule based bidding campaign eligibility criteria may change as we continue to enhance our rule-based bidding system.

- Rule-based bidding is available for Sponsored Products.
- Campaigns must: Meet the minimum daily budget requirement (see requirements per marketplace here). You can specify a ROAS target in campaign settings. We recommend you should wait at least two weeks for the campaign to get enough data before specifying a ROAS target. If not specified, Amazon Ads will automatically determine an appropriate ROAS target to maximize sales. Can use any type of targeting: Automatic. Keyword. Product.

**Note:** Amazon Ads does not guarantee that we’ll hit the ROAS target that you set.

## Schedule bid rules

**Note:**You can’t apply schedule bid rules to campaigns that have **Rule-based bidding** active. Schedule bid rules will be on hold if you change your bidding strategy to **Rule-based bidding**.

Schedule bid rules is a feature available for Sponsored Products campaigns that allows you to schedule bid increases for specific times of the day, days of the week, date ranges or high traffic events (example: Black Friday). This lets you take advantage of high-impact time windows to help you drive more sales.

This rule can be applied to the following bidding strategies:

- Dynamic bids - up and down.
- Down only.
- Fixed.

You can create a new rule by:

1. Selecting a campaign.
2. Setting a schedule (example: Mondays between 11am-12pm, or Black Friday).
3. Setting a percentage to increase bids (example: 10%).

Amazon will then increase your bids on an automated basis on each ad opportunity to help to drive more sales.

To understand campaign performance at an hourly level and adjust Schedule bid rules effectively, you can access the Report Center and download the campaign report. This report provides visibility into all monthly, weekly, quarterly, daily, and hourly performance metrics (example: impressions, clicks, conversions, and ROAS) for your Sponsored Product campaigns.

Select:

1. Report category: **Sponsored products**.
2. Report type: **Campaigns**.
3. Time period: **Hourly**.

You can then choose to see a summarized report across your time period for hours of the day or a daily and hourly grain for the time period you selected. This report is available for the last 30 days of your campaign. You can download 14 days of reporting data with a look-back period of 30 days.

Schedule bid rules are add-on.

**Example**: On campaign A you set Rule 1 for Mondays between 9am-11am with a bid increase of 20%. Then, for the same campaign, you set a daily rule for Mondays called Rule 2 with a bid increase of 10%. This means that on Mondays between 9am-11am your bids on campaign A will increase by 30%.

Schedule bid rules will be applied on top of your placement adjustment.

**Example**: If you have a campaign with a down only bidding strategy, top-of-search placement adjustment of 10%, bid of $1.00, and you apply a Schedule bid rule to increase your bid by 20% on Mondays. On Monday for top of search impressions, your bid will be $1.30 and $1.20 for all other placements on Mondays. However, the rest of the week, your bid will be $1.10 for top of search impressions and $1.00 for all other impressions.

**Tip:**Apply a schedule-based budget rule to ensure that your campaign doesn’t exceed your budget due to bid increases.

Learn how to apply schedule bid rules for Sponsored Products.
