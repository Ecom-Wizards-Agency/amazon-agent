---
title: "Manage your Amazon Marketing Cloud audiences"
source_url: "https://advertising.amazon.com/help/GD9DJBUXY5QEX272"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Manage your Amazon Marketing Cloud audiences

After you’ve created your audiences, you can view, edit, and delete them by going to the **Projects** page and selecting the **Audience** tab.

Updated on Dec 22, 2025

## View audiences

**Note:**After the audience is created, the system automatically prepends “AMC” to the audience name. This allows you to easily identify and filter all AMC-created audiences in Amazon DSP.

The **Audience** tab displays all audiences created using the UI, as well as the API.

On the **Audience** tab, you can view:

- **Status**: Status of the audience query execution in AMC. This status isn’t the audience status in Amazon DSP or your sponsored ads account. Audience status can be: **Pending**: The query is still running. **Completed**: The query was successfully completed and the system automatically pushed the audience to Amazon DSP or sponsored ads. Although the status is listed as **Completed** in AMC, it may not yet be available for use in Amazon DSP or sponsored ads. It may take up to 48 hours for the audience to be available for use. **Failed**: The query failed to complete. Hover your cursor over **Details** to view additional information about why the query failed. For example, the audience creation may have failed in Amazon DSP because it didn’t reach the minimum size requirement of 2,000. If your audience is in **Failed** status, you can delete or edit the audience. Review the following section for detailed instructions on how to delete and edit your AMC audiences.
- **Name**: The name and canonical ID of the audience. These fields are displayed in Amazon DSP, Sponsored Products, Sponsored Brands, or Display and can’t be modified. The name given to the audience when it was created. This field is displayed in Amazon DSP and can’t be modified.
- **Description**: The description given to the audience when it was created.
- **Advertiser:**The advertiser name and type of advertiser.
- **Size**: If the query was successfully completed, this field indicates the estimated size of the audience.
- **Created on**: The date and time the audience was created.
- **Action:** Allows you to delete failed audiences, open in query editor, or copy the share link or execution ID.

## Edit failed audiences

**Note:** Only audiences with **Failed** status can be edited. Those with **Pending**, **Running**, and **Completed** status can’t be edited.

If an audience has failed, in most cases there’s an issue with the SQL query, or the audience didn’t reach the minimum size requirements. If the audience fails, you can edit and re-submit it.

The following table provides a summary of the components that are editable versus those that aren’t.

| Editable | Non-editable |
| --- | --- |
| SQL code | Audience name |
| Date range | Audience ID |
| Auto adjust date | Audience description |
| Time zone | Audience type |
|  | Lookalike expected reach (applicable to lookalike audiences only) |

To edit a failed audience, access the audience detail page, click the **Actions** button on the right-side of the page, and then click **Open in query editor**.

When you edit and save an audience, AMC will re-run the query. If it succeeds, the audience is pushed to Amazon DSP or your sponsored ads account. If it fails, you can choose to update it again. It may take up to may take up to 48 hours for edited audience to become **Active**.

## Delete failed audiences

**Note:**Only audiences with **Failed** status can be deleted. Those with **Pending**, **Running**, and **Completed** status can’t be deleted.

If an audience has failed and you no longer need it, you can delete it to remove unnecessary audiences from AMC.

To delete failed audiences from the **Audience**tab, click the **Actions** button on the right-side of the page next to the audience you want to remove, and then click **Delete**. The delete process is immediate after you select **Delete**.

Note that the delete process is immediate after you select **Delete**.
