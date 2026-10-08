---
title: "View audience details in Amazon Marketing Cloud"
source_url: "https://advertising.amazon.com/help/GD7CBPPLDA3PD9MK"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# View audience details in Amazon Marketing Cloud

To view the details of the audience creation in Amazon Marketing Cloud (AMC), select the name of the audience from the list of audiences.

Updated on Jan 29, 2026

On the audience detail page, you can view:

- **Query status**: The status of the audience query in AMC: Pending, Completed, or Failed.
- **ID**: The unique identifier of the audience execution in AMC.
- **Creation date**: The date when the audience was created.
- **Advertiser name**: The name of the advertiser.
- **Advertiser ID**: The identifier for the advertiser.
- **Canonical ID**: The canonical identifier of the audience created.
- **Audience ID**: The audience identifier.
- **Update audience**: How often AMC will re-run the SQL query to regenerate the audience in Amazon DSP. If the audience was created using the UI, this value will always be daily for rule-based audiences and weekly for lookalike audiences. If created using the API, this value may vary.
- **Last update**: The most recent date and time the audience was refreshed (that is, the SQL query was re-run) and pushed to Amazon DSP or sponsored ads. Each time the audience is refreshed and the new audience overwrites the existing audience in Amazon DSP, this attribute is updated. Initially, this value will be the same as the creation time.
- **Audience size**: The approximate size of the audience.
- **Date range**: The date range of the most recent update. If you’ve selected to automatically adjust the date range, this range will reflect the most recent date range used for the updated audience.
- **No 3P trackers:**True if this item not allowed to use 3P tracking, and false if the item is allowed to use 3P tracking.
- **Auto adjust date**: If you select: **Yes**, each time the query runs, the date range will be adjusted automatically. The start and end dates will be incremented by 1 day each time the query is run. **No**, each time the query is run, the date range won’t be adjusted; it will stay the same as what you originally selected.
- **Name**: The name of the audience.
- **Description**: The description of the audience.
- **Query**: The query used to create the audience.

## Managing audiences

From the **Action** button, you’ll have the **Create copy**option. You can use this as a starting point for a new audience.

If the audience has failed, you’ll have the added option to**Edit** or **Delete** the audience. Those with **Pending**, **Running**, and **Completed** status can’t be edited or deleted. To learn more about how to edit or delete audiences, visit Manage your Amazon Marketing Cloud audiences.
