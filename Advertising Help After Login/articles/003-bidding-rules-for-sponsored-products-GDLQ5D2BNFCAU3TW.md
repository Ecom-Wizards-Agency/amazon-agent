---
title: "Bidding rules for Sponsored Products"
source_url: "https://advertising.amazon.com/help/GDLQ5D2BNFCAU3TW"
downloaded_at: "2026-05-12"
source: "Amazon Ads Support Center"
updated_on: "2025-11-06"
---

# Bidding rules for Sponsored Products

Learn about how schedule bid rules and rule-based bidding works for Amazon Sponsored Products.

Updated on Nov 06, 2025.

## Rule-based bidding

Rule-based bidding takes the guesswork out of adjusting bids to align with your marketing strategy. With this bidding strategy, you set a rule with a performance goal, for example Return on Ad Spend or ROAS. Amazon then adjusts your base bids for each ad impression, increasing or decreasing them as needed to try to achieve your performance target.

Amazon does not guarantee that it will hit the performance target you set.

To help capture sales from high-value opportunities, rule-based bidding can increase bids by up to 5 times the adjusted bid amount, if any adjustments are applied to the original bid. Amazon automatically adjusts bids for each ad opportunity based on how likely that opportunity is to result in a sale, working to meet the ROAS goal set for the campaign.

ROAS measures the revenue generated for every dollar spent on advertising.

## Example: Placement adjustment bid

If your base bid is `$1`, and you have a placement adjustment for Top of Search by `10%`:

Placement adjusted bid = Base bid amount * (1 + Bid Adjustment Percentage)

`1 * 1.10 = $1.10`

The table below shows bid cap increase by placement.

| Base bid | Placement | Placement adjustment | Placement adjustment bid | Max bid calculated |
| --- | --- | --- | --- | --- |
| $1.00 | Top of search | 10% | $1.10 | $5.50 |
| $1.00 | Rest of search | 0% | $1.00 | $5.00 |
| $1.00 | Detail page | 0% | $1.00 | $5.00 |

## Campaign eligibility

**Note:** Rule-based bidding campaign eligibility criteria may change as Amazon continues to enhance the rule-based bidding system.

Rule-based bidding is available for Sponsored Products.

Campaigns must:

- Meet the minimum daily budget requirement.
- Allow a ROAS target in campaign settings.
- Use automatic, keyword, or product targeting.

Amazon recommends waiting at least two weeks for the campaign to get enough data before specifying a ROAS target. If no target is specified, Amazon Ads will automatically determine an appropriate ROAS target to maximize sales.

**Note:** Amazon Ads does not guarantee that it will hit the ROAS target you set.

## Schedule bid rules

**Note:** You cannot apply schedule bid rules to campaigns that have Rule-based bidding active. Schedule bid rules will be on hold if you change your bidding strategy to Rule-based bidding.

Schedule bid rules are available for Sponsored Products campaigns. They allow you to schedule bid increases for specific times of day, days of week, date ranges, or high-traffic events such as Black Friday. This helps take advantage of high-impact time windows to drive more sales.

Schedule bid rules can be applied to these bidding strategies:

- Dynamic bids - up and down
- Down only
- Fixed

You can create a new rule by:

1. Selecting a campaign.
2. Setting a schedule, for example Mondays between 11am-12pm or Black Friday.
3. Setting a percentage to increase bids, for example 10%.

Amazon will then increase bids on an automated basis for each ad opportunity to help drive more sales.

## Using reports for schedule bid rules

To understand campaign performance at an hourly level and adjust schedule bid rules effectively, access the Report Center and download the campaign report. This report provides visibility into monthly, weekly, quarterly, daily, and hourly performance metrics such as impressions, clicks, conversions, and ROAS for Sponsored Product campaigns.

Select:

1. Report category: **Sponsored products**
2. Report type: **Campaigns**
3. Time period: **Hourly**

You can then choose to see:

- A summarized report across your time period for hours of the day
- A daily and hourly grain for the selected time period

This report is available for the last 30 days of your campaign. You can download 14 days of reporting data with a look-back period of 30 days.

Schedule bid rules are additive.

Example:

On campaign A, you set Rule 1 for Mondays between 9am-11am with a bid increase of 20%. For the same campaign, you set a daily rule for Mondays called Rule 2 with a bid increase of 10%. On Mondays between 9am-11am, bids on campaign A will increase by 30%.

Schedule bid rules are applied on top of placement adjustment.

Example:

If a campaign uses down-only bidding, a top-of-search placement adjustment of 10%, a bid of $1.00, and a schedule bid rule that increases bid by 20% on Mondays, then on Monday top-of-search impressions the bid will be $1.30 and $1.20 for all other placements on Mondays. For the rest of the week, the bid will be $1.10 for top-of-search impressions and $1.00 for all other impressions.

**Tip:** Apply a schedule-based budget rule to ensure the campaign does not exceed budget because of bid increases.

## Related topics

- Understand bidding
- Understand bidding on Amazon DSP
- Understand frequency on Amazon DSP
- Understand Amazon DSP bidding features
- Understand Amazon Ads auctions
- Bidding strategies for Sponsored Products
