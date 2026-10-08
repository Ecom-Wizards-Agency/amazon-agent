---
title: "View and interpret study results"
source_url: "https://advertising.amazon.com/help/GHRTKMK4SL3F6FB6"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# View and interpret study results

Learn how to access, view, and interpret the key metrics and data visualizations within an Amazon Brand Lift study report to gauge the branding impact and effectiveness of your advertising campaigns.

Updated on Dec 11, 2025

## View study results

Your study results include an overall summary of your ads on your chosen study goal (Awareness or Consideration), historical trend in results over the study period, and question breakouts for Campaign, Age, Gender, Household Income, Campaign Type, Device, and Frequency.

To view study results:

1. In the Amazon Ads console, go to **Measurement & reporting** and select **Brand lift studies**.
2. Locate your study in the dashboard.
3. In the **Results** column, click **View results** to proceed to the Studies results page.

To download results, click **Download results** in the upper-right section of the Studies results page or in the drop-down of the Actions column of the Studies dashboard.

## Interpret study results

On the **Overall** tab of Amazon Brand Lift results, a single chart displays the absolute lift (called “Difference” in the chart and Data Table) in your chosen study goal between the qualifying response rate of 2 groups: an ad-exposed audience and a lookalike, unexposed control group. This lift is cumulative as of the most recent update period.

The absolute lift displayed is the midpoint in a range of possible results. You can construct the range by hovering on the results to view the margin of error (95%). For example, if your absolute lift was +5 percentage points, and margin of error (95%) was +/- 3%, then your range of possible results was between +2 and +8 percentage points. If 0 doesn’t fall within your range of results, it means that we detected a statistically significant lift at the 95% confidence level.

Advertisers should aim for a statistically significant lift, which indicates that your results are likely a direct result of your ad campaign and didn’t happen by chance. The statistical significance is displayed in the chart next to absolute lift, denoted by one or more asterisks that represent the confidence level (* for 80%, ** for 90%, and *** for 95%). For studies that show significance at the 80% level, we would expect the same results 80% of the time in an identical scenario.

Statistical significance depends on:

1. **The size of the absolute lift (Ad-Exposed response % - Control response %).**For example, it’s harder to detect a statistically significant absolute lift of +1 than +10.
2. **The data points of the brand lift study.**The lower the size of the absolute lift, the more responses you’ll need to be confident in the results. Data points include survey responses and predictions of a customer’s awareness of your brand based on machine learning.

Objectives with negative lift or lift that’s positive but not statistically significant will show “No lift detected” and have no asterisks next to absolute lift. If an objective showed lift that wasn’t statistically significant, it doesn’t mean that lift didn’t occur, but that Amazon Brand Lift couldn’t confidently detect it. In such cases, focus on how you might adjust your campaign targeting and creatives to optimize future campaigns.

| Scenario | Interpretation |
| --- | --- |
| Positive, statistically significant absolute lift | The campaigns were successful in generating a measurable lift. |
| Positive, but not statistically significant absolute lift | Brand lift can’t be confidently proven. Audit creatives, messaging, and campaign goals for potential areas of improvement. |

Click the **Show Historical Trend** toggle within the **Overall** tab (available if your report has updated at least twice) to view how the lift in desired responses has changed with each update period to date. The lift displayed in each period is cumulative as of the most recent update period. Hover over results in view **Statistical Significance** and **Margin of Error** at the 95% confidence level, or the absolute degree to which results might differ from the published lift value. For example, if lift is displayed as +5 percentage points with 95% statistical significance, and Margin of Error (95%) is +/- 3%, the true range of results is between 2 to 8 percentage points.

**Available report breakouts**

**Note:**The campaign breakout and campaign-level results will only appear if at least 200 survey responses are collected for one or more campaigns. Other reporting breakouts will only appear if there are at least 100 survey responses collected for that breakout.

| Name | Definition |
| --- | --- |
| Campaign | Results by campaign included in the study |
| Gender | Gender identity |
| Age | Age range |
| Household Income | Household income range |
| Campaign Type | Sponsored ads campaign type |
| Device | The device on which the ad was viewed. |
| Frequency | Number of times a person viewed the ad. |

## Interpret campaign level results

With the campaign breakout, you can view how each campaign in your study contributed to the total result. Campaign results are cumulative from the beginning of the study. The breakout will appear if at least 200 survey responses are collected for one or more campaigns.

Campaigns without enough data to appear in the breakout will still be included in total level results. The total result for the Difference column will match the Overall tab within your study. The following columns will be shown in the breakout:

| **Name** | **Definition** | **Calculation** | **Aggregation** |
| --- | --- | --- | --- |
| Control | The percentage of people who weren’t exposed to your ad and are aware of your brand. | % of unexposed people who are aware of a brand | Study level results are calculated by combining results across campaigns, including those without enough data to appear in the table. |
| Exposed | The percentage of people who were exposed to your ad and are aware of your brand. | % of exposed people who are aware of a brand |
| Difference | The percentage change in your brand awareness after people see your ad. This number reflects the increase in brand awareness after your ad was exposed to people compared with a control group that wasn't exposed to your ad. Lift rate = (% of ad-exposed people who are aware of a brand) - (% of unexposed people who are aware of a brand) | (% of ad-exposed people who are aware of a brand) - (% of unexposed people who are aware of a brand) |
| Spend | Ad spend for the campaign. |  | Sum. |
| Incremental reach | Total number of unique people exposed to a campaign during the measurement period who hadn’t been exposed to the same campaign for 180 days prior. |  | Sum. This includes duplicates if the same person was exposed to multiple campaigns in the table. |
| **Lifted users** | The number of people likely made aware of your brand because of your ad. | (Difference) (Incremental Reach) | Calculated at the total level using total-level inputs. |
| **Cost per lifted user** | The amount you paid, in the advertiser's currency, for each person who was likely made aware of your brand because of your ad. | (Ad Spend)/(Lifted users) | Calculated at the total level using total-level inputs. |
| Statistical significance | The likelihood that the change in brand awareness was because of your ad. If blank, the change wasn't specifically because of your ad. | Statistical significance can be 80%, 90%, or 95%. Otherwise we’ll display an empty column. | Not tested at the total level |
