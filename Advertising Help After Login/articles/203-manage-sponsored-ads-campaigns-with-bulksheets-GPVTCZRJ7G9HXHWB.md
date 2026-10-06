---
title: "Manage sponsored ads campaigns with bulksheets"
source_url: "https://advertising.amazon.com/help/GPVTCZRJ7G9HXHWB"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Manage sponsored ads campaigns with bulksheets

Manage sponsored ads campiagns using bulk spreadsheets.

Updated on Aug 12, 2026

Create, update, or archive Sponsored Products, Sponsored Brands, and Display campaigns using bulk spreadsheets. Learn more about bulksheets.

## Download your bulksheets file

To manage your sponsored ads campaigns in bulk, first download a bulksheet:

1. In the navigation side menu, click **Campaigns**.
2. In the **Campaigns** page menu, click ****Bulk operations****.
3. Download a spreadsheet: Existing campaigns: Click ****Download campaigns****. You can use this file as a starting template when updating existing campaigns. Bulk operations template: Click ****Download template and instructions**** to download a new, **blank** template.

## Manage your bulksheets file

Bulksheets organize your campaigns using a parent-child structure. A campaign is the top-level "parent," and the components within it (like ad groups, keywords, ads, and targeting) are "child" entities. Each entity gets its own row in the spreadsheet, with the parent campaign row at the top and child rows beneath it. This structure applies whether you're creating new campaigns, updating existing ones, or archiving campaigns you no longer need. All characters, capitalization, punctuation, and spacing matter. Enter values exactly as specified. After you download your bulksheets file using the steps above:

1. Make edits to the relevant fields in your bulksheet. The first 3 columns are: **Column A (Product):** Sponsored Products, Sponsored Brands, or Display **Column B (Entity):** Campaign component you want to make changes to (Campaign, Ad group, Keyword, etc.) **Column C (Operation):** Create, Update, or Archive
2. Use the rest of the columns in the sheet to make updates to your campaign components.

**Key guidelines**

- You will always need a new row for each entity, even if you are creating multiples of the same entity. For instance, to create 10 different keywords, you would need 10 different keyword rows.
- Include the Product (campaign type) in Column A for every row
- The Operation column must contain a value for updates to occur; blank rows are ignored
- When creating campaigns, enter **Create** in the Operation column for each entity row

## Upload your bulksheets file

Once you're done with making changes to your bulksheets file:

1. Save your file.
2. In the **Bulk operations** page, click ****Upload campaigns****.
3. Choose your file and click ****Upload****.

**Tip**: Delete rows that don't need updates before uploading your file to reduce processing time.

## Bulk manage campaigns by ad type

**Available entities**

Campaign, ad group, product ad, keyword, negative keyword, bidding adjustment, campaign negative keyword, product targeting, negative product targeting. Visit Sponsored Products entities to learn more about the entities hierarchy.

Create at least 1 ad group for automatic targeting campaigns.

**Example**

| Col A | Col B | Col C |
| --- | --- | --- |
| **Product** | **Entity** | **Operation** |
| Sponsored Products | Campaign | Create |
|  | Ad group | Update |
|  | Product ad | Archive |
|  | Keyword |  |
|  | Negative keyword |  |
|  | Bidding adjustment |  |
|  | Campaign negative keyword |  |
|  | Product targeting |  |
|  | Negative product targeting |  |

**Off-Amazon ad serving**

You can update the off-Amazon ad serving setting for your existing Sponsored Products campaigns using the **Off-Amazon ad serving** column in your bulksheet. This column accepts the following values:

- ****Increase reach off Amazon****: (default setting) Uses your campaign's targeting settings to deliver both on and off Amazon. This may increase impressions and sales opportunities off-Amazon.
- ****Limit reach to Amazon****: Your ads can only appear on Amazon owned-and-operated properties and won’t be shown off-Amazon. This may reduce impressions and sales opportunities.

**Note:** The Off-Amazon ad serving column is available for the Campaign entity only and applies to existing campaigns. This setting is not available during campaign creation via bulksheets. If your campaign is in a portfolio, include the Portfolio Id when uploading updates to avoid removing the campaign from the portfolio.

**Example**

| Col A | Col B | Col C | Column D | Col AG |
| --- | --- | --- | --- | --- |
| **Product** | **Entity** | **Operation** | **Campaign ID** | **Off-Amazon ad serving** |
| Sponsored Products | Campaign | Update | 10093874 | Increase reach |

## Add negative keywords

Stop keywords from showing your ads by adding negative keywords to campaigns or ad groups:

1. Download a bulksheets file from existing campaigns using the steps above.
2. Create a filter to locate the campaign you want to edit.
3. Enter 1 negative keyword per blank row with: **Campaign ID:** Must match the campaign name **Keyword**: Add the keywords **Match Type:** Enter "exact," "broad," or "phrase"
4. Save and upload your bulksheets file using the steps above.
