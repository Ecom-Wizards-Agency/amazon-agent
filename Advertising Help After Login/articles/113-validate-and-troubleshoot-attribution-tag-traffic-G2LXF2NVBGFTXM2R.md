---
title: "Validate and troubleshoot attribution tag traffic"
source_url: "https://advertising.amazon.com/help/G2LXF2NVBGFTXM2R"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Validate and troubleshoot attribution tag traffic

Validate the reporting metrics by following our troubleshooting tips.

Updated on May 18, 2026

Once you apply attribution tags to your non-Amazon campaigns, clicks will be recorded. You may notice 10-20% discrepancy when comparing Amazon Attribution to the publisher or ad server traffic metrics. This could be due to a number of factors, including a difference in click-counting methodology.

If you see a click variance greater than 20%, follow our troubleshooting guidelines below.

Tips for troubleshooting click variance:

- If you’re seeing more clicks in Amazon Attribution than in your publisher or ad server reporting, ensure the date range you’re selecting matches up for Amazon Attribution and publisher reporting. Ensure that the attribution tag isn't being shared across other creatives, URLs, or event trackers.
- If you’re seeing fewer clicks in Amazon Attribution than in your publisher or ad server reporting, ensure the date range you’re selecting matches up for Amazon Attribution and publisher reporting. Ensure you're comparing publisher reporting only for ads that had Amazon Attribution tags appended.
- If you’re not seeing any clicks in Amazon Attribution, ensure you’ve properly implemented your attribution tags. Also, we recommend making sure that the landing page of the campaign is active on Amazon. Learn how to apply attribution tags
- If you’re not seeing conversions or sales in Amazon Attribution, ensure product ASINs have been assigned to your campaigns. Keep in mind that the default columns in our console show conversions attributed to the ASINs associated to your campaign. Sometimes when there are no detail page views for ASINs, ads can still contribute to overall brand conversions. These will be itemized under Total metrics, such as “Total sales” and “Total detail page views.” You can customize the columns in the UI to see Total metrics in addition to existing columns.
- Amazon Attribution reporting will mask (as zero) all clicks and conversions for data rows with fewer than 10 clicks. After the corresponding tags have been clicked 10 times, all metrics for those rows should appear within 48 hours. When data is masked, the console will display a notification near the top of the screen.
- If you’re seeing discrepancies between Amazon Attribution and Stores, note that Amazon Attribution and Stores use different attribution methodology which likely accounts for any discrepancies. Learn more about Stores attribution
